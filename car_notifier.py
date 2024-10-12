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
        inserted_ids = []  # To store inserted car IDs

        for car_config in self.cars_config:
            # Prepare a nicely formatted message for the search parameters
            search_message = (
                f"🔍🚗 *🚨 Car Search Alert!* 🚨\n\n"
                f"📋 *Search Criteria*:\n"
                f"💰 *Max Price*: {car_config['max_price']}\n"
                f"📏 *Max Mileage*: {car_config['max_mileage']} km\n"
                f"📍 *Max Proximity*: {car_config['max_proximity']} km\n"
                f"🚗 *Brand*: {car_config['title_contains'].capitalize()}\n"
                f"📅 *Min Year*: {car_config['min_year']}\n"
            )

            # Send the formatted message to Telegram
            self.bot_helper.send_result(search_message)

            # Logging the same search message
            logger.info(f"Searching for cars: {car_config}")

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
                        f"🎉 *New Car Found* 🎉:\n\n"
                        f"📝 *Title*: {car['Title']}\n"
                        f"📅 *Year*: {year if year else 'Unknown'}\n"
                        f"💰 *Price*: {car['Price']}\n"
                        f"📏 *Mileage*: {car['Mileage'] if car['Mileage'] else 'Unknown'} km\n"
                        f"📍 *Proximity*: {car['Proximity']} km\n"
                        f"🔗 *Link*: [View Car]({car['Product URL']})"
                    )
                    time.sleep(1)
                    self.bot_helper.send_result(message)
                    self.sent_db.db.insert_one({"ID": car["ID"]})
                    inserted_ids.append(car["ID"])  # Add ID to the list
                    logger.info(f"Car with ID {car['ID']} sent and saved to sent_listings.")

            logger.info(
                f"Found {len(cars_to_send)} cars for {car_config['title_contains']} that were sent to Telegram.")
            self.bot_helper.send_result(
                f"✅ Found {len(cars_to_send)} cars for *{car_config['title_contains'].capitalize()}* 🚗")

        # Send a summary log with the inserted IDs
        if inserted_ids:
            summary_message = (
                f"📝 *Summary*: {len(inserted_ids)} cars inserted to the database.\n"
                f"🆔 *Inserted IDs*: {', '.join(inserted_ids)}"
            )
            self.bot_helper.send_result(summary_message)
            logger.info(f"Inserted {len(inserted_ids)} car IDs into the database.")


if __name__ == '__main__':
    notifier = CarNotifier()
    notifier.search_for_cars()
