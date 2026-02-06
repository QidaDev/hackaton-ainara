import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Unified config for the app and MCP server (MCP reads from env set by app or from .env)."""
    mongo_connection_string = os.environ.get(
        "MONGO_CONNECTION_STRING",
        "mongodb://admin:secretpassword@mongodb:27017/",
    )
    mongo_database_name = os.environ.get("MONGO_DATABASE_NAME", "ainara-db")
