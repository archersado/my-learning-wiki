# src/agents/llm_wrapper.py

from langchain_openai import ChatOpenAI

class WrappedLLM:
    def __init__(self, llm_instance=None, model_name="", temperature=0):
        if llm_instance is not None:
            self.llm = llm_instance
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)

    def __call__(self, *args, **kwargs):
        # This allows the WrappedLLM instance to be called directly
        return self.llm.invoke(*args, **kwargs)

    # You can add other methods here to expose more functionality of the underlying LLM
    # For example, a method for streaming responses
    def stream(self, *args, **kwargs):
        return self.llm.stream(*args, **kwargs) 