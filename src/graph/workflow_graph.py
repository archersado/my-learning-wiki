from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from src.agents.custom_llm import CustomChatModel

from ..config.settings import LLM_CONFIG
from ..agents.custom_llm import CustomChatModel

# Import agent classes
from ..agents.scraping_expert import ScrapingExpert
from ..agents.knowledge_organizer import KnowledgeOrganizer
from src.agents.tech_content_picker import TechPicker
from ..agents.professional_editor import ProfessionalEditor
from ..agents.reviewer import Reviewer
from ..agents.channel_processor import ChannelContentProcessor
from ..agents.distribution_expert import DistributionExpert

from datetime import datetime

# Define the state for the graph
class GraphState(TypedDict):
    new_knowledge_available: bool
    scrape_list: List[dict] | None
    pick_article: List[dict] | None
    reports: List[dict] | None
    summary: str | None
    formatted_content: str | None
    publish_type: str | None
    categories: str | None
    formatted_content: dict | None
    publishing_results: dict | None
    summary_structed: list | None

# Initialize agents using config
ds = CustomChatModel(**LLM_CONFIG["deepseek"])
gpt4o = CustomChatModel(**LLM_CONFIG["gpt4o"])
knowledge_organizer_agent = KnowledgeOrganizer() # This is the entry point
professional_editor_agent = ProfessionalEditor(llm=gpt4o)
reviewer_agent = Reviewer()
scraper = ScrapingExpert(llm=gpt4o)
channel_processor_agent = ChannelContentProcessor(llm=gpt4o)
distribution_expert_agent = DistributionExpert(llm=gpt4o)
techPicker = TechPicker(llm=gpt4o)

def build_content_workflow_graph():
    """Builds the main content production Langgraph workflow."""
    workflow = StateGraph(GraphState)

    # Add nodes for the agents in the main workflow

    workflow.add_node("scrape", scraper.process)
    workflow.add_node("pick", techPicker.process)
    workflow.add_node("edit", professional_editor_agent.process)
    # workflow.add_node("channel", channel_processor_agent.process)
    workflow.add_node("format", channel_processor_agent.process)
    workflow.add_node("publish", distribution_expert_agent.process)

    # Define the entry point
    workflow.set_entry_point("scrape") # Workflow starts with checking/organizing data

    # Define edges
    # Use a conditional edge after organize
    # workflow.add_conditional_edges(
    #     "pick",
    #     # This function determines the next node based on the state
    #     lambda state: "edit" if state.get("reports") else END,
    #     {"edit": "edit", END: END} # Mapping states to node names
    # )

    # Sequential edges for the rest of the flow
    workflow.add_edge("scrape", "pick")
    workflow.add_edge("pick", "edit")
    workflow.add_edge("edit", "format")    
    # workflow.add_edge("review", "format")
    workflow.add_edge("format", "publish")

    # Set the finish point
    workflow.add_edge("publish", END)

    # Compile the graph
    app = workflow.compile()
    return app

# Example usage in main.py:
# if __name__ == "__main__":
#     graph = build_content_workflow_graph()
#     # Initial state for the graph (might be empty or contain parameters for organize)
#     # organize node will check DB for new data
#     initial_state = {}
#     for s in graph.stream(initial_state):
#         print(s) 