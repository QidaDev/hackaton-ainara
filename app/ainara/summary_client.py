"""
Cliente de resumen de caso vía Claude + MCP.
Clase autocontenida: no importa ni carga otros archivos de cliente.
Usado desde el endpoint POST /api/summary y desde la CLI (client-claude.py).
"""

import asyncio
import logging
import os
import re
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

MODEL_ID = "claude-sonnet-4-20250514"


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

    @staticmethod
    def _strip_html_xml(raw: str) -> str:
        """Remove HTML/XML tags from model output to avoid structured leakage."""
        if not raw or not raw.strip():
            return raw
        return re.sub(r"<[^>]+>", "", raw).strip()

    def _get_system_instruction(self, mcp_resources):
        text = (
            "Eres un motor de extracción y resumen de datos estrictamente basado en hechos. NO eres un asistente creativo.\n"
            "Tu única función es transformar datos crudos JSON provenientes de la herramienta `generate_case_summary` en un resumen legible.\n\n"
            "PROTOCOLOS DE SEGURIDAD CONTRA ALUCINACIONES:\n"
            "1. CERO INVENCIÓN: Si la herramienta devuelve listas vacías, nulos o falta de información, NO inventes nombres, ni fechas, ni situaciones (ej. no inventes 'Sra. Carmen', ni 'hija Laura'). Si no hay datos, no escribes nada sobre eso."
            "2. VERIFICACIÓN DE VACÍO: Si la respuesta de la herramienta indica que no hay notas, ni llamadas, ni mensajes, tu ÚNICA respuesta debe ser: \"El caso no existe.. En el caso de existir, no incluyas ninguna verificacion de que el caso existe."
            "3. FUENTE ÚNICA: Solo existe lo que está en el JSON de retorno. Si el JSON no menciona una enfermedad, la persona está sana. Si no menciona familiares, la persona vive sola."
            "Reglas de formato: Texto plano, sin markdown complejo, sin meta-comentarios."
)
        for res in mcp_resources.resources:
            text += f"- {res.name}: {res.uri}\n"
        return text

    def _get_case_summary_prompt(self, case_id: str) -> str:
        return (
            
                f"""
                case_id to use (mandatory): {case_id}
                You must call the generate_case_summary tool exactly with this case_id: "{case_id}".

                CRITICAL INSTRUCTION - DATA VALIDATION:
                Upon receiving the tool output, you must perform a check BEFORE writing any summary:
                1. Look at the content of 'notes', 'whatsapp', and 'transcriptions'.
                2. If ALL of them are empty, null, or contain no substantive text, you must output exactly: "El caso no existe." and stop immediately.
                3. DO NOT fabricate a default case (e.g., do not invent a "Sra. Carmen" or "Laura").
                4. Only proceed to the summary if actual text data is returned.

                If data exists, follow these instructions for the summary:
                - **Focus exclusively on the person (the subject of care). Do not mention the advisor (asesora).**
                - Base the summary ONLY on the text returned by the tool.
                - Remove redundant information.
                - Maintain temporal coherence (oldest to newest).
                - Timeline: Include dates of relevant notes and phone calls (with brief descriptions) at the end. Order chronologically (DD/MM/YYYY).

                Format:
                - Max 1000 words.
                - Spanish language only.
                - Plain text (no HTML/XML).
                - Do not include meta-comments like "Here is the summary".

                Output Structure:
                [Summary Content]
                [Timeline]
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

        raw = "\n".join(final_text_parts).strip() if final_text_parts else ""
        return self._strip_html_xml(raw) if raw else ""

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
