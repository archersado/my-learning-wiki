# Placeholder for database interaction tools

# Assume necessary database libraries are installed (e.g., pymongo, psycopg2, etc.)
# from pymongo import MongoClient
# import psycopg2

from ..config.settings import RAW_DATA_DB_CONFIG, KNOWLEDGE_BASE_DB_CONFIG
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging


# Assume DBManager class is split or refactored to use these
# For simplicity in Agent code, maybe pass instances of these to agents

class DBManager:
    _instance = None
    _raw_data_client: Optional[MongoClient] = None
    _knowledge_base_client: Optional[MongoClient] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database connections."""
        if not hasattr(self, 'initialized'):
            self._connect_raw_data()
            # self._connect_knowledge_base()
            self.initialized = True

    def _connect_raw_data(self):
        """Establish connection to raw data MongoDB."""
        try:
            if self._raw_data_client is None:
                self._raw_data_client = MongoClient(
                    host=RAW_DATA_DB_CONFIG['host'],
                    port=RAW_DATA_DB_CONFIG['port'],
                    maxPoolSize=100,
                    serverSelectionTimeoutMS=5000
                )
                # Verify the connection
                self._raw_data_client.admin.command('ping')
                logging.info("Successfully connected to raw data MongoDB")
        except ConnectionFailure as e:
            logging.error(f"Failed to connect to raw data MongoDB: {e}")
            raise

    def _connect_knowledge_base(self):
        """Establish connection to knowledge base MongoDB."""
        try:
            if self._knowledge_base_client is None:
                self._knowledge_base_client = MongoClient(
                    host=KNOWLEDGE_BASE_DB_CONFIG['host'],
                    port=KNOWLEDGE_BASE_DB_CONFIG['port'],
                    maxPoolSize=100,
                    serverSelectionTimeoutMS=5000
                )
                # Verify the connection
                self._knowledge_base_client.admin.command('ping')
                logging.info("Successfully connected to knowledge base MongoDB")
        except ConnectionFailure as e:
            logging.error(f"Failed to connect to knowledge base MongoDB: {e}")
            raise

    def get_raw_data_db(self):
        """Get raw data database instance."""
        if self._raw_data_client is None:
            self._connect_raw_data()
        return self._raw_data_client[RAW_DATA_DB_CONFIG['db_name']]

    def get_knowledge_base_db(self):
        """Get knowledge base database instance."""
        if self._knowledge_base_client is None:
            self._connect_knowledge_base()
        return self._knowledge_base_client[KNOWLEDGE_BASE_DB_CONFIG['db_name']]

    def save_knowledge(self, knowledge_data: dict):
        """Save knowledge data to the knowledge base."""
        try:
            db = self.get_knowledge_base_db()
            collection = db['knowledge']
            
            # Add metadata
            knowledge_data['created_at'] = datetime.utcnow()
            knowledge_data['updated_at'] = datetime.utcnow()
            
            result = collection.insert_one(knowledge_data)
            logging.info(f"Knowledge saved with ID: {result.inserted_id}")
            return result.inserted_id
        except OperationFailure as e:
            logging.error(f"Failed to save knowledge: {e}")
            raise

    def get_knowledge(self, query: dict) -> List[Dict[str, Any]]:
        """Retrieve knowledge data from the knowledge base."""
        try:
            db = self.get_knowledge_base_db()
            collection = db['knowledge']
            return list(collection.find(query))
        except OperationFailure as e:
            logging.error(f"Failed to retrieve knowledge: {e}")
            raise

    def get_raw_data_collection(self):
        try:
            db = self.get_raw_data_db()
            collection = db['rss_raw_content']
            return collection
        except OperationFailure as e:
            logging.error(f"Failed to retrieve raw data collection: {e}")
            raise

    def save_raw_data(self, data: dict):
        """Save raw data to the raw data database."""
        try:
            db = self.get_raw_data_db()
            collection = db[RAW_DATA_DB_CONFIG['collection_name']]
            
            # Add metadata
            data['created_at'] = datetime.utcnow()
            data['status'] = 'pending'
            
            result = collection.insert_one(data)
            logging.info(f"Raw data saved with ID: {result.inserted_id}")
            return result.inserted_id
        except OperationFailure as e:
            logging.error(f"Failed to save raw data: {e}")
            raise

    def get_new_raw_data(self, last_processed_timestamp: datetime = None) -> List[Dict[str, Any]]:
        """Retrieve new raw data since the last processed timestamp."""
        try:
            db = self.get_raw_data_db()
            collection = db['raw_data']
            
            query = {'status': 'pending'}
            if last_processed_timestamp:
                query['created_at'] = {'$gt': last_processed_timestamp}
            
            return list(collection.find(query))
        except OperationFailure as e:
            logging.error(f"Failed to retrieve raw data: {e}")
            raise

    def mark_data_processed(self, data_ids: List[str]):
        """Mark raw data entries as processed."""
        try:
            db = self.get_raw_data_db()
            collection = db['raw_data']
            
            result = collection.update_many(
                {'_id': {'$in': data_ids}},
                {
                    '$set': {
                        'status': 'processed',
                        'processed_at': datetime.utcnow()
                    }
                }
            )
            logging.info(f"Marked {result.modified_count} documents as processed")
            return result.modified_count
        except OperationFailure as e:
            logging.error(f"Failed to mark data as processed: {e}")
            raise

    def close(self):
        """Close all database connections."""
        if self._raw_data_client is not None:
            self._raw_data_client.close()
            self._raw_data_client = None
            logging.info("Raw data MongoDB connection closed")
            
        if self._knowledge_base_client is not None:
            self._knowledge_base_client.close()
            self._knowledge_base_client = None
            logging.info("Knowledge base MongoDB connection closed")

    def __del__(self):
        """Destructor to ensure connections are closed."""
        self.close()

# 初始化 DBManager
# db_manager = DBManager()

# # 保存数据
# knowledge_data = {
#     "title": "AI Trends",
#     "content": "Latest AI developments...",
#     "tags": ["AI", "ML", "Deep Learning"]
# }
# db_manager.save_knowledge(knowledge_data)

# # 查询数据
# query = {"tags": "AI"}
# results = db_manager.get_knowledge(query)

# # 更新数据
# update_query = {"title": "AI Trends"}
# update_data = {"content": "Updated content..."}
# db_manager.save_knowledge(update_data)

# # 删除数据
# delete_query = {"title": "AI Trends"}
# db_manager.save_knowledge(delete_query)

# 关闭连接
# db_manager.close() 