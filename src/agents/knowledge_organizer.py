from .base_agent import BaseAgent
# Assume tools are passed in __init__ or accessed globally/via context
from datetime import datetime
from bson.son import SON

class KnowledgeOrganizer(BaseAgent):
    def __init__(self, llm=None, tools=None):
        super().__init__(llm, tools)
        self.last_processed_timestamp = None # Keep track of the last time data was processed

    def process(self, state: dict) -> dict:
        """
        Checks for new raw data, organizes it, updates knowledge base,
        and passes relevant info to the next agent.
        This is the entry point for the main content workflow.
        """
        print(f"[{datetime.now()}] Knowledge Organizer is checking for new information.")
        try:
            pipeline = [
                {"$unwind": "$categories"},  # 展开数组字段
                {"$group": {
                    "_id": "$categories",    # 按标签分组
                    "count": {"$sum": 1}     # 计算出现次数
                }},
                {"$sort": SON([("count", -1), ("_id", 1)])}  # 先按数量降序，再按标签升序
            ]
            # Insert articles. Use insert_many for efficiency.
            # Add update logic if you need to avoid duplicates based on link or title
            # For now, a simple insert_many

            results = self.db_client.get_raw_data_collection().aggregate(pipeline)
            print(f"Successfully get category: {results.to_list()}.")

        except Exception as e:
            print(f"Error inserting articles into MongoDB: {e}")

        # # 1. Retrieve new raw data since last run
        # new_raw_data = self.raw_data_storage.get_new_raw_data(self.last_processed_timestamp)

        # if not new_raw_data:
        #     print("No new raw data found to organize. Workflow may end here.")
        #     state["new_knowledge_available"] = False # Flag for conditional edge
        #     state["organized_knowledge_chunk"] = None # No new knowledge chunk
        #     return state # No new data, potentially transition to END

        # print(f"Found {len(new_raw_data)} new raw data items.")
        # self.last_processed_timestamp = datetime.now() # Update timestamp after retrieval

        # # 2. Process and organize the raw data
        # # Placeholder for complex organization logic (using LLM or rules)
        # print("Organizing raw data into knowledge structure.")
        # organized_knowledge_items = []
        # processed_data_ids = []
        # for item in new_raw_data:
        #     # Example: simple processing
        #     organized_item = {
        #         "title": f"Knowledge from: {item.get('content', 'No Content')[:20]}...",
        #         "content": item.get("content", ""),
        #         "source_timestamp": item.get("timestamp"),
        #         "processed_timestamp": datetime.now(),
        #         # Add categorization, summarization etc. here
        #     }
        #     organized_knowledge_items.append(organized_item)
        #     # Assuming items have IDs or a way to reference them for marking
        #     # processed_data_ids.append(item.get('id')) # Replace with actual ID retrieval

        # # 3. Update the Knowledge Base
        # print("Updating knowledge base with organized data.")
        # for item in organized_knowledge_items:
        #     self.knowledge_base_manager.save_organized_knowledge(item)

        # # 4. Mark raw data as processed (optional but good practice)
        # # if processed_data_ids:
        # #     self.raw_data_storage.mark_data_processed(processed_data_ids)

        # # 5. Prepare output for the next agent
        # # Pass a chunk of the newly organized knowledge to the next agent
        # # You might process all new data but only pass the "most important" or a sample
        # state["new_knowledge_available"] = True
        # # Pass the organized items or a summary/reference to them
        # state["organized_knowledge_chunk"] = organized_knowledge_items # Or a subset/summary

        # print("Knowledge organization complete. Passing to next agent.")
        return state 