from mcp.server.fastmcp import FastMCP

from bson import json_util
from pathlib import Path
import logging
from typing import List, Dict, Any

from pymongo import MongoClient

# 1. Conexión (usando las credenciales de tu Docker)
client = MongoClient[Any]("mongodb://admin:secretpassword@mongodb:27017/")
db = client['ainara-db']
notes_collection = db['notes']
whatsapp_messages_collection = db['whatsapp_messages']
phone_call_transcriptions_collection = db['phone_call_transcriptions']


# Configure logging for the server
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp_server")

logging.getLogger('pymongo').setLevel(logging.WARNING)


# Get the base directory of the project (where server.py is located)
BASE_DIR = Path(__file__).parent.absolute()


# Initialize the server with a name
mcp = FastMCP("MyMCP")

## TOOLS
# Type hints (int) and docstrings are REQUIRED for the AI to understand how to use it.
@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """
    Suma dos números enteros y devuelve el resultado.
    
    Args:
        a: El primer número a sumar.
        b: El segundo número a sumar.

    Returns:
        El resultado de la suma de los dos números.
    """
    return a + b




@mcp.tool()
def generate_case_summary(case_id: str) -> str:
    """
    Genera un resumen del caso de la familia. Descarga de MongoDB todas las notas que la Referente Social hace sobre el caso de la familia. Resume el contenido de todas las notas, mediante el campo text de cada nota. Descarga las conversaciones/chats de Whatsapp de todas las conversaciones que la Referente Social ha tenido con el caso de la familia (descarga de MongoDB). Resume el contenido de todas las conversaciones. Descarga las transcripciones de todas las llamadas de telefono que la refererente social con la familia acerca del caso (Descarga de MongoDB). Resume el contenido de las transcripciones. Combina el resumen de las notas, el resumen de las conversaciones y el resument de las trasncripcionespara generar un resumen del caso de la familia.
    
    Args:
        case_id: El case_id del caso de la familia a consultar. Es un campo del documento de la base de datos de MongoDB de la collection "notas". Es un campo del documento de la base de datos de MongoDB de la collection "whatsapp_message". Es un campo del documento de la base de datos de MongoDB de la collection "phone_call_transcription".
    Returns:
    Un JSON con los siguientes campos:
        - notes: El resumen de las notas. En formato JSON dentro de una misma String concatenada. Las notas se separan en el String por un salto de linea.
        - whatsapp_messages: El resumen de las conversaciones/chats de Whatsapp. En formato JSON dentro de una misma String concatenada. Los mensajes se separan en el String por un salto de linea.
        - phone_call_transcriptions: El resumen de las transcripciones de las llamadas de telefono. En formato JSON dentro de una misma String concatenada. Las transcripciones se separan en el String por un salto de linea.
    """
    logger.info(f"🔍 generate_case_summary called with arguments:")
    logger.info(f"   - case_id: {repr(case_id)} (type: {type(case_id)})")
    try:
        notes_list = []
        # 3. Realizar la búsqueda
        # Usamos find() si esperas varios documentos (devuelve un cursor)
        notes_list_cursor = notes_collection.find({"case_id": case_id})
        whatsapp_messages_list_cursor = whatsapp_messages_collection.find({"case_id": case_id})
        phone_call_transcriptions_list_cursor = phone_call_transcriptions_collection.find({"case_id": case_id})
        
        logger.debug(f"🔍 NOTES LIST CURSOR: {repr(notes_list_cursor)} (type: {type(notes_list_cursor)})")
        logger.debug(f"🔍 WHATSAPP MESSAGES LIST CURSOR: {repr(whatsapp_messages_list_cursor)} (type: {type(whatsapp_messages_list_cursor)})")
        logger.debug(f"🔍 PHONE CALL TRANSCRIPTIONS LIST CURSOR: {repr(phone_call_transcriptions_list_cursor)} (type: {type(phone_call_transcriptions_list_cursor)})")
        
        string_list: List[str] = []
        
        notes_list = list[Any](notes_list_cursor)
        whatsapp_messages_list = list[Any](whatsapp_messages_list_cursor)
        phone_call_transcriptions_list = list[Any](phone_call_transcriptions_list_cursor)
        
        notes_string: str = ""
        whatsapp_messages_string: str = ""
        phone_call_transcriptions_string: str = ""
    
        string_return: str = ""
        logger.debug(f"🔍 NOTES LIST: {repr(notes_list)} (type: {type(notes_list)})")
        logger.debug(f"🔍 WHATSAPP MESSAGES LIST: {repr(whatsapp_messages_list)} (type: {type(whatsapp_messages_list)})")
        logger.debug(f"🔍 PHONE CALL TRANSCRIPTIONS LIST: {repr(phone_call_transcriptions_list)} (type: {type(phone_call_transcriptions_list)})")
        
        for note in notes_list:
            # string_list.append(str(note))
            string_return += "Nota: " + str(note) + "\n"
            logger.debug(f"🔍 NOTES: string_return: {repr(string_return)})")
        for whatsapp_message in whatsapp_messages_list:
            # string_list.append(str(whatsapp_message))
            string_return += "Whatsapp Message: " + str(whatsapp_message) + "\n"
            logger.debug(f"🔍 WHATSAPP MESSAGES: string_return: {repr(string_return)})")
        for phone_call_transcription in phone_call_transcriptions_list:
            # string_list.append(str(phone_call_transcription))
            string_return += "Phone Call Transcription: " + str(phone_call_transcription) + "\n"
            logger.debug(f"🔍 PHONE CALL TRANSCRIPTIONS: string_return: {repr(string_return)})")

        logger.debug(f"🔍 string_return: {repr(string_return)} (type: {type(string_return)})")
        return string_return
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return f"Error al consultar la base de datos: {str(e)}"




# Run the server
if __name__ == "__main__":
    mcp.run()