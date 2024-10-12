import json
import os
import logging
import re
import time

from helpers.dbHelper import DbHelper
from helpers.telegramHelper import TelegramBotHelper
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class CarNotifier:
    def __init__(self):
        project_dir = os.path.dirname(os.path.abspath(__file__))

        # Load configuration from config.json
        config_path = os.path.join(project_dir, 'config.json')
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)

        # Load multiple car search configurations
        self.cars_config = config['cars']
        self.db_helper = DbHelper(os.getenv('DATABASE_NAME'), "listings")
        self.sent_db = DbHelper(os.getenv('DATABASE_NAME'), "sent_listings")
        self.bot_helper = TelegramBotHelper()

    def extract_year_from_title(self, title):
        """Extract the first four-digit number in the title (assuming it's the year)."""
        match = re.search(r'\b(19|20)\d{2}\b', title)
        return int(match.group()) if match else None

    def search_for_cars(self):
        for car_config in self.cars_config:
            logger.info(f"Searching for cars: {car_config}")
            self.bot_helper.send_result(f"Searching for cars: {car_config}")

            new_cars = list(self.db_helper.db.find({
                "Price": {"$lte": car_config['max_price']},
                "$or": [
                    {"Mileage": {"$lte": car_config['max_mileage']}},
                    {"Mileage": None}
                ],
                "Proximity": {"$lte": car_config['max_proximity']},
                "Title": {"$regex": f".*{car_config['title_contains']}.*", "$options": "i"}
            }))

            cars_to_send = []

            for car in new_cars:
                title = car['Title']
                year = self.extract_year_from_title(title)

                # Apply year filter if provided
                if car_config['min_year'] and year and year < car_config['min_year']:
                    continue

                if not self.sent_db.db.find_one({"ID": car["ID"]}):
                    cars_to_send.append(car)
                    message = (
                        f"New car found: {car['Title']}\n"
                        f"Mileage: {car['Mileage'] if car['Mileage'] else 'Unknown'}\n"
                        f"Price: {car['Price']}\n"
                        f"Proximity: {car['Proximity']} km\n"
                        f"Link: {car['Product URL']}\n"
                        f"Year: {year if year else 'Unknown'}"
                    )
                    time.sleep(1)
                    self.bot_helper.send_result(message)
                    self.sent_db.db.insert_one({"ID": car["ID"]})
                    logger.info(f"Car with ID {car['ID']} sent and saved to sent_listings.")

            logger.info(f"Found {len(cars_to_send)} cars for {car_config['title_contains']} that were sent to Telegram.")
            self.bot_helper.send_result(f"Found {len(cars_to_send)} cars for {car_config['title_contains']}")

if __name__ == '__main__':
    notifier = CarNotifier()
    notifier.search_for_cars()
