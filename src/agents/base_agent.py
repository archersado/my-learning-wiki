"""Base agent with optional MongoDB connection."""
from abc import ABC, abstractmethod
from ..tools.db_manager import DBManager
from ..config.settings import USE_LOCAL_STORAGE

class BaseAgent(ABC):
    def __init__(self, llm=None, tools=None, skip_db: bool = False):
        self.llm = llm
        self.tools = tools or []
        if not skip_db and not USE_LOCAL_STORAGE:
            self.db_client = DBManager()
        else:
            self.db_client = None

    @abstractmethod
    def process(self, state: dict) -> dict:
        """Process the input state and return the updated state."""
        pass

# This can be used as a base class if agents share common functionality or need access to LLMs/tools. 