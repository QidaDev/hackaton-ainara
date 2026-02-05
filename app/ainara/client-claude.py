import asyncio
import os
import sys
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

from anthropic import AsyncAnthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("client")
logger.setLevel(logging.INFO)

# Silenciar ruidos innecesarios
logging.getLogger('anthropic').setLevel(logging.WARNING)
logging.getLogger('pymongo').setLevel(logging.WARNING)

# --- CONFIGURACIÓN ---
PATH_PYTHON = "venv/bin/python" # Asegúrate de que este path sea correcto
PATH_SERVER = "server.py"
ANTHROPIC_API_KEY =""

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY is not set")

MODEL_ID = "claude-3-haiku-20240307" # O la versión más reciente

def convert_tools_mcp(mcp_list_tools_result):
    """Convierte herramientas MCP al formato 'tool' de Anthropic."""
    anthropic_tools = []
    for tool in mcp_list_tools_result.tools:
        anthropic_tools.append({
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema # Anthropic usa 'input_schema'
        })
    
    # Añadimos la herramienta manual para leer recursos
    anthropic_tools.append({
        "name": "get_mcp_resource",
        "description": "Reads the content of a specific MCP resource given its URI.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uri": {"type": "string", "description": "The exact URI of the resource"}
            },
            "required": ["uri"]
        }
    })
    return anthropic_tools

def get_system_instruction(mcp_resources):
    """Genera el system prompt con la lista de recursos."""

    system_instruction = "Eres un asistente útil conectado a un servidor MCP.\n"
    system_instruction += "Tienes acceso a las siguientes herramientas y recursos.\n\n"
    system_instruction += "RECURSOS MCP DISPONIBLES (Usa la herramienta 'get_mcp_resource' con el URI para leer su contenido):\n"
    for res in mcp_resources.resources:
        system_instruction += f"- {res.name}: {res.uri}\n"
    return system_instruction


def _get_summary_client():
    try:
        from app.ainara.summary_client import SummaryClient
    except ImportError:
        from summary_client import SummaryClient
    return SummaryClient()


async def run_on_request(case_id: str) -> str:
    """
    Modo a petición: delega en SummaryClient (clase autocontenida, sin importar archivos).
    Usado por el endpoint /api/summary y por CLI.
    """
    return await _get_summary_client().generate_summary_async(case_id)


async def main():
    # 1. Cliente Anthropic
    anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    # 2. Configurar servidor MCP
    server_params = StdioServerParameters(
        command=PATH_PYTHON,
        args=[PATH_SERVER],
        env=os.environ.copy()
    )

    print("🔌 Conectando al servidor MCP...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            
            # 3. Preparar herramientas y recursos
            mcp_tools_raw = await mcp_session.list_tools()
            mcp_resources = await mcp_session.list_resources()
            
            claude_tools = convert_tools_mcp(mcp_tools_raw)
            system_prompt = get_system_instruction(mcp_resources)
            
            messages = [] # Historial de la conversación

            print(f"🛠️  Herramientas: {[t['name'] for t in claude_tools]}")
            print("\n--- Chat con Claude (Escribe 'exit' para salir) ---")

            while True:
                user_input = input("\n👤 Usuario: ")
                if user_input.lower() in ["salir", "exit"]:
                    break
                
        
                # prompt = "Recupera todas las notas que la Referente Social hace sobre el caso de la familia. El case_id es " + user_input + ". Recupera las fechas de cada nota, que corresponde a la fecha en la que la referente social hace la nota. Resume el contenido de todas las notas, mediante el campo text de cada nota. Incluye las fechas de las notas en el resumen. El resumen no debe ocupar mas de 500 palabras. No devuelvas nada mas, ni introducciones al resumen ni comentarios al final. Genera el resultado en Español. "
                
                prompt = "Genera un resumen del caso de la familia para el case Descarga de MongoDB todas las notas que la Referente Social hace sobre el caso de la familia. Resume el contenido de todas las notas, mediante el campo text de cada nota. Descarga las conversaciones/chats de Whatsapp de todas las conversaciones que la Referente Social ha tenido con el caso de la familia (descarga de MongoDB). Resume el contenido de todas las conversaciones. Descarga las transcripciones de todas las llamadas de telefono que la refererente social con la familia acerca del caso (Descarga de MongoDB). Resume el contenido de las transcripciones. Genera una timeline dentro del propio resumen solo para las fechas de las llamadas o para las notas con el contenido mas importante, indica esas fechas. Manten la coherencia temporal, lo mas antiguo primero. Descarta lo obvio en el resumen y ten en cuenta que puede haber informacion redundante en el resumen entre las notas, las conversaciones de chat y las transcripciones, descarta lo de redundante. Combina el resumen de las notas, el resumen de las conversaciones y el resumen de las trasncripciones para generar un resumen del caso de la familia. El case_id es " + user_input + ". El resumen no debe ocupar mas de 1000 palabras. No devuelvas nada mas, ni introducciones al resumen ni comentarios al final. Genera el resultado en Español. No inventes, si el case_id no existe o no recuperas ningun dato ni de notas, conversaciones de chat ni transcripciones, devuelves que el caso no existe y ya está."
                
                messages.append({"role": "user", "content": prompt})

                # Bucle de interacción (Claude puede pedir usar herramientas varias veces)
                while True:
                    response = await anthropic_client.messages.create(
                        model=MODEL_ID,
                        max_tokens=4096,
                        system=system_prompt,
                        tools=claude_tools,
                        messages=messages
                    )
                    logger.info(f"🤖 Claude response content: {response.content}")
                    # Añadimos la respuesta de Claude al historial
                    messages.append({"role": "assistant", "content": response.content})
                    print(f"🤖 Claude: {response.content}")
                    # ¿Claude quiere usar herramientas?
                    tool_requests = [content for content in response.content if content.type == "tool_use"]
                    
                    if not tool_requests:
                        # Si no hay herramientas, imprimimos el texto final
                        for content in response.content:
                            if content.type == "text":
                                print(f"🤖 Claude: {content.text}")
                        break # Salimos del bucle interno para esperar nuevo input del usuario

                    # Procesar llamadas a herramientas
                    tool_results_for_anthropic = []
                    
                    for tool_call in tool_requests:
                        name = tool_call.name
                        args = tool_call.input
                        call_id = tool_call.id
                        
                        logger.info(f"  🤔 Claude usa: {name}")

                        if name == "get_mcp_resource":
                            logger.info(f"  🤔 Claude usa: {name} con args: {args}")
                            res = await mcp_session.read_resource(args["uri"])
                            result_text = res.contents[0].text
                        else:
                            res = await mcp_session.call_tool(name, arguments=args)
                            result_text = res.content[0].text

                        # Guardar el resultado para enviárselo a Claude
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": call_id,
                                    "content": result_text,
                                }
                            ],
                        })
                    
                    # El bucle continúa para enviar los resultados a Claude

if __name__ == "__main__":
    if len(sys.argv) > 1:
        case_id = sys.argv[1]
        result = asyncio.run(run_on_request(case_id))
        print(result)
    else:
        asyncio.run(main())