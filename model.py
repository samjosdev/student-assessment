from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv(override=True)


def get_llm_core():
    """
    Returns the LLM core model.
    This model is used for the core functionality of the application.
    """
    # model = ChatOpenAI(model="gpt-4o-mini")
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-05-20")
    return model