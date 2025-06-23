import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv(override=True)

class Config:
    # Determine if we're running on Hugging Face Spaces
    IS_SPACES = os.getenv('SPACE_ID') is not None
    
    # Database settings
    DB_FILE = "agent_memory.sqlite"
    SESSION_FILE = "session.json"
    
    # API Keys - try environment variables first, then .env file
    SERPER_API_KEY = os.getenv('SERPER_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Server settings
    if IS_SPACES:
        SERVER_NAME = "0.0.0.0"  # Listen on all interfaces in Spaces
        SHARE = False  # Don't create share link in Spaces
    else:
        SERVER_NAME = "127.0.0.1"  # Local development
        SHARE = False  # Set to True to create share link locally
    
    SERVER_PORT = 7860
    
    @classmethod
    def check_environment(cls):
        """Check if all required environment variables are set"""
        missing_vars = []
        if not cls.SERPER_API_KEY:
            missing_vars.append("SERPER_API_KEY")
        if not cls.GOOGLE_API_KEY:
            missing_vars.append("GOOGLE_API_KEY")
        
        return len(missing_vars) == 0, missing_vars

    @classmethod
    def get_server_settings(cls):
        """Get server settings based on environment"""
        return {
            "server_name": cls.SERVER_NAME,
            "server_port": cls.SERVER_PORT,
            "share": cls.SHARE,
            "show_error": True
        } 