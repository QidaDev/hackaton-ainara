"""
Cliente de resumen de caso vía Claude + MCP.
Clase autocontenida: no importa ni carga otros archivos de cliente.
Usado desde el endpoint POST /api/summary y desde la CLI (client-claude.py).
"""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from anthropic import AsyncAnthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

logger = logging.getLogger("summary_client")
logger.setLevel(logging.INFO)
logging.getLogger("anthropic").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)

MODEL_ID = "claude-3-haiku-20240307"


class SummaryClient:
    """
    Cliente para generar el resumen de un caso (modo a petición).
    Conecta a MCP, llama a Claude con herramientas y devuelve el texto del resumen.
    """

    def __init__(
        self,
        api_key: str | None = None,
        path_python: str | None = None,
        path_server: str | None = None,
    ):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self._api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        base_dir = Path(__file__).resolve().parent
        self._path_python = path_python or os.environ.get("MCP_PYTHON", "python")
        self._path_server = path_server or str(base_dir / "server.py")

    def _convert_tools_mcp(self, mcp_list_tools_result):
        anthropic_tools = []
        for tool in mcp_list_tools_result.tools:
            anthropic_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            })
        anthropic_tools.append({
            "name": "get_mcp_resource",
            "description": "Reads the content of a specific MCP resource given its URI.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "uri": {"type": "string", "description": "The exact URI of the resource"}
                },
                "required": ["uri"],
            },
        })
        return anthropic_tools

    def _get_system_instruction(self, mcp_resources):
        text = (
            "Eres un asistente de IA que genera un resumen de un caso de la familia a través de consultas a un servidor MCP.\n"
            "Tienes acceso a las siguientes herramientas y recursos.\n\n"
            "No añadas ningun tipo de tag html ni xml en el resumen."
        )
        for res in mcp_resources.resources:
            text += f"- {res.name}: {res.uri}\n"
        return text

    def _get_case_summary_prompt(self, case_id: str) -> str:
        return (
            f"""
                    Instrucciones:
                    Genera un resumen integral del caso con case_id = {case_id}, siguiendo estrictamente los pasos y reglas indicadas. No añadas explicaciones, introducciones ni comentarios finales.     Devuelve únicamente el resumen solicitado, en español.

                    Pasos a seguir:

                    1. Recuperación de datos desde MongoDB:
                       - Descarga todas las notas asociadas al case_id y utiliza únicamente su campo text.
                       - Descarga todas las conversaciones de WhatsApp asociadas al case_id y utiliza únicamente su campo   text.
                       - Descarga todas las transcripciones de llamadas asociadas al case_id y utiliza únicamente su campo  text.

                    2. Comprobación de existencia del caso:
                       - Si no se recupera ningún dato (ni notas, ni conversaciones, ni transcripciones), devuelve  únicamente:
                         "El caso no existe."
                         y no añadas nada más.

                    3. Proceso de resumen:
                       - Resume por separado:
                         a) El contenido completo de las notas.
                         b) El contenido completo de las conversaciones de WhatsApp.
                         c) El contenido completo de las transcripciones de llamadas.
                       - Unifica los tres resúmenes eliminando información redundante.
                       - Mantén coherencia temporal, ordenando la narración desde lo más antiguo a lo más reciente.
                       - Descarta lo obvio y prioriza siempre la información significativa.

                    4. Timeline:
                       - Dentro del resumen final, incluye una timeline breve que recoja únicamente:
                         - Las fechas de notas con contenido relevante.
                         - Las fechas de llamadas telefónicas y una breve descripcion de la llamada. Si la llamada tiene una fecha que hace que se intercale con otros eventos de la timeline, incluye la llamada y su descripcion antes de ese evento.
                       - Mantén el orden cronológico estrictamente.

                    5. Extensión y formato:
                       - El resumen completo no debe superar 1000 palabras.
                       - Mantén estructura clara y consistente en cada ejecución.
                       - Texto final únicamente en español.

                    Salida esperada:
                    Un único bloque de texto que contenga:
                    - El resumen combinado.
                    - La timeline integrada.

                    No añadas nada más fuera de este contenido.
                    Si no encuentras datos en alguna de las colecciones, como notas o conversaciones chat, no lo incluyas en el resumen. No incluyas nunca tags HTML ni XML
                    """
        )

    async def _run_single_turn(
        self,
        anthropic_client: AsyncAnthropic,
        mcp_session: ClientSession,
        claude_tools: list,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        messages = [{"role": "user", "content": user_prompt}]
        final_text_parts = []

        while True:
            response = await anthropic_client.messages.create(
                model=MODEL_ID,
                max_tokens=4096,
                system=system_prompt,
                tools=claude_tools,
                messages=messages,
            )
            logger.info("Claude response content: %s", response.content)
            messages.append({"role": "assistant", "content": response.content})

            tool_requests = [c for c in response.content if c.type == "tool_use"]
            if not tool_requests:
                for content in response.content:
                    if content.type == "text":
                        final_text_parts.append(content.text)
                break

            for tool_call in tool_requests:
                name = tool_call.name
                args = tool_call.input
                call_id = tool_call.id
                logger.info("Claude usa: %s", name)
                if name == "get_mcp_resource":
                    res = await mcp_session.read_resource(args["uri"])
                    result_text = res.contents[0].text
                else:
                    res = await mcp_session.call_tool(name, arguments=args)
                    result_text = res.content[0].text
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": call_id,
                        "content": result_text,
                    }],
                })

        return "\n".join(final_text_parts).strip() if final_text_parts else ""

    async def generate_summary_async(self, case_id: str) -> str:
        """
        Genera el resumen del caso vía Claude + MCP (async).
        Conecta a MCP, una sola petición, devuelve el texto.
        """
        anthropic_client = AsyncAnthropic(api_key=self._api_key)
        server_params = StdioServerParameters(
            command=self._path_python,
            args=[self._path_server],
            env=os.environ.copy(),
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()
                mcp_tools_raw = await mcp_session.list_tools()
                mcp_resources = await mcp_session.list_resources()
                claude_tools = self._convert_tools_mcp(mcp_tools_raw)
                system_prompt = self._get_system_instruction(mcp_resources)
                user_prompt = self._get_case_summary_prompt(case_id)
                return await self._run_single_turn(
                    anthropic_client,
                    mcp_session,
                    claude_tools,
                    system_prompt,
                    user_prompt,
                )

    def generate_summary(self, case_id: str) -> str:
        """
        Genera el resumen del caso vía Claude + MCP (sync).
        Pensado para el endpoint POST /api/summary.
        """
        return asyncio.run(self.generate_summary_async(case_id))
