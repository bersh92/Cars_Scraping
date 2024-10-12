import certifi
import pymongo
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Global logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress pymongo debug logs
logging.getLogger('pymongo').setLevel(logging.WARNING)

class DbHelper():
    def __init__(self, db_name, collection_name):
        self.client = pymongo.MongoClient(
            os.getenv('MONGO_CONNECTION_STRING'), tlsCAFile=certifi.where())
        self.db = self.client[db_name][collection_name]
        logger.info(f"Connected to MongoDB database: {db_name}, collection: {collection_name}")

    def insert_many(self, list_of_objects):
        self.db.insert_many(list_of_objects)
        logger.info(f"Inserted {len(list_of_objects)} documents into the database.")

    def delete_all(self):
        result = self.db.delete_many({})
        logger.info(f"Deleted {result.deleted_count} documents from the collection.")

    def insert_one(self, element):
        self.db.insert_one(element)
        logger.info(f"Inserted one document: {element}")

    def rename_field(self, old_field_name, new_field_name):
        self.db.update_many({}, {'$rename': {old_field_name: new_field_name}})
        logger.info(f"Renamed field from {old_field_name} to {new_field_name}.")

    def update_value_in_db(self, myquery, newvalues):
        result = self.db.update_one(myquery, newvalues)
        logger.info(f"Updated document with query {myquery}. Modified {result.modified_count} document(s).")

    def check_value_in_db(self, element_for_check):
        count = self.db.count_documents(element_for_check)
        logger.info(f"Checked for {element_for_check}, found {count} document(s).")
        return count

    def close_connection(self):
        self.client.close()
        logger.info("Closed MongoDB connection.")
