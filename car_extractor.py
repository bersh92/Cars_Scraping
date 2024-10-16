# CarsExtractor.py

import json
import os
import re
import logging
from dotenv import load_dotenv

from helpers.dbHelper import DbHelper
from helpers.telegramHelper import TelegramBotHelper  # Import your TelegramBotHelper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class CarsExtractor:
    def __init__(self):
        project_dir = os.path.dirname(os.path.abspath(__file__))

        # Load configuration from config.json
        config_path = os.path.join(project_dir, 'config.json')
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)

        # Load multiple car search configurations
        self.cars_config = config['cars']
        self.db_helper = DbHelper(os.getenv('DATABASE_NAME'), "listings")
        # Collection for storing extracted cars
        self.extracted_cars_db = DbHelper(os.getenv('DATABASE_NAME'), "extracted_cars")

        # Initialize your TelegramBotHelper
        self.bot_helper = TelegramBotHelper()

    def extract_year_from_title(self, title):
        """Extract the first four-digit number in the title (assuming it's the year)."""
        match = re.search(r'\b(19|20)\d{2}\b', title)
        return int(match.group()) if match else None

    def extract_cars(self):
        self.extracted_cars_db.delete_all()
        extracted_car_ids = []  # To store IDs of extracted cars

        for car_config in self.cars_config:
            # Logging the search parameters
            logger.info(f"Extracting cars with configuration: {car_config}")

            # Query the database
            matching_cars = list(self.db_helper.db.find({
                "Price": {"$lte": car_config['max_price']},
                "$or": [
                    {"Mileage": {"$lte": car_config['max_mileage']}},
                    {"Mileage": None}
                ],
                "Proximity": {"$lte": car_config['max_proximity']},
                "Title": {"$regex": f".*{car_config['title_contains']}.*", "$options": "i"}
            }))

            for car in matching_cars:
                title = car['Title']
                year = self.extract_year_from_title(title)

                # Apply year filter if provided
                if car_config['min_year'] and year and year < car_config['min_year']:
                    continue

                # Check if the car is already in the extracted_cars collection
                if not self.extracted_cars_db.db.find_one({"ID": car["ID"]}):
                    # Insert the car into the extracted_cars collection
                    self.extracted_cars_db.db.insert_one(car)
                    extracted_car_ids.append(str(car["ID"]))
                    logger.info(f"Car with ID {car['ID']} extracted and stored.")

            logger.info(
                f"Extracted {len(extracted_car_ids)} cars for {car_config['title_contains']}."
            )

        # Log the summary
        total_extracted = len(extracted_car_ids)
        logger.info(f"Total cars extracted and stored: {total_extracted}")
        if extracted_car_ids:
            logger.info(f"Extracted Car IDs: {', '.join(extracted_car_ids)}")

        # Prepare the message to send via Telegram
        message = f"Total cars extracted and stored based on search parameters: {total_extracted}"

        # Send the message using your TelegramBotHelper
        self.bot_helper.send_result(message)

    def close_connections(self):
        """Close database connections."""
        self.db_helper.close_connection()
        self.extracted_cars_db.close_connection()

if __name__ == '__main__':
    extractor = CarsExtractor()
    extractor.extract_cars()
    extractor.close_connections()
