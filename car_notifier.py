import json
import os
import logging
import re
import time
from datetime import datetime
import sys

from helpers.chatGptDescriptionCheck import ChatGptDescriptionCheck
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
        self.db_helper = DbHelper(os.getenv('DATABASE_NAME'), "extracted_cars")  # Use extracted_cars collection
        self.sent_db = DbHelper(os.getenv('DATABASE_NAME'), "sent_listings")
        self.bot_helper = TelegramBotHelper()

        # Initialize the description checker
        self.description_checker = ChatGptDescriptionCheck()
        logger.info("Description checker initialized.")

    def extract_year_from_title(self, title):
        """Extract the first four-digit number in the title (assuming it's the year)."""
        match = re.search(r'\b(19|20)\d{2}\b', title)
        return int(match.group()) if match else None

    def search_for_cars(self):
        total_inserted_ids = []  # To store all inserted car IDs across all configurations

        # Get the current date and time
        now = datetime.now()
        date_time_message = (
            f"🕒 *Car Search Started*\n"
            f"📅 *Date*: {now.strftime('%Y-%m-%d')}\n"
            f"⏰ *Time*: {now.strftime('%H:%M:%S')}\n"
        )

        # Send the first message with date and time
        self.bot_helper.send_result("----------------------")
        self.bot_helper.send_result(date_time_message)

        for car_config in self.cars_config:
            # Initialize inserted_ids for this configuration
            inserted_ids = []  # IDs of cars sent for this configuration

            # Determine if description check is enabled for this configuration
            use_description_check = car_config.get('use_description_check', False)

            # Prepare a nicely formatted message for the search parameters
            search_message = (
                f"*🚨 Car Search* 🚨\n\n"
                f"📋 *Search Criteria*:\n"
                f"💰 *Max Price*: {car_config['max_price']}\n"
                f"📏 *Max Mileage*: {car_config['max_mileage']} km\n"
                f"📍 *Max Proximity*: {car_config['max_proximity']} km\n"
                f"🚙 *Brand*: {car_config['title_contains'].capitalize()}\n"
                f"📅 *Min Year*: {car_config['min_year']}\n"
                f"📝 *Description Check*: {'Enabled' if use_description_check else 'Disabled'}\n"
            )

            # Send the formatted message to Telegram
            self.bot_helper.send_result(search_message)

            # Logging the same search message
            logger.info(f"Searching for cars: {car_config}")

            # Query the extracted_cars collection
            new_cars = list(self.db_helper.db.find({
                "Price": {"$lte": car_config['max_price']},
                "$or": [
                    {"Mileage": {"$lte": car_config['max_mileage']}},
                    {"Mileage": None}
                ],
                "Proximity": {"$lte": car_config['max_proximity']},
                "Title": {"$regex": f".*{car_config['title_contains']}.*", "$options": "i"}
            }))

            for car in new_cars:
                title = car['Title']
                year = self.extract_year_from_title(title)

                # Apply year filter if provided
                if car_config['min_year'] and year and year < car_config['min_year']:
                    continue

                # Check if the car has already been sent
                if not self.sent_db.db.find_one({"ID": car["ID"]}):
                    # If description check is enabled, evaluate the description
                    if use_description_check:
                        description = car.get('Description', '')
                        if description and len(description) >= 3:
                            try:
                                result = self.description_checker.check_the_car(description)
                                if result is True:
                                    verdict = "✅ Good"
                                elif result is False:
                                    verdict = "❌ Bad"
                                    continue  # Skip bad cars
                                elif result is "maybe ok":
                                    verdict = "🤔 Maybe OK"
                                else:
                                    verdict = "Unexpected verdict: " + result    
                            except Exception as e:
                                logger.error(f"Error checking description: {e}")
                                sys.exit(1)  # Exit the script with an error
                        else:
                            verdict = "⚠️ No Description"
                            logger.warning(f"No valid description for car ID {car['ID']}")
                    else:
                        verdict = ""

                    # Prepare the message to send
                    message = (
                        f"🎉 *New Car Found* 🎉:\n\n"
                        f"📝 *Title*: {car['Title']}\n"
                        f"📅 *Year*: {year if year else 'Unknown'}\n"
                        f"💰 *Price*: {car['Price']}\n"
                        f"📏 *Mileage*: {car['Mileage'] if car['Mileage'] else 'Unknown'} km\n"
                        f"📍 *Proximity*: {car['Proximity']} km\n"
                        f"🔗 *Link*: [View Car]({car['Product URL']})\n"
                    )

                    # If description check is enabled, add the verdict to the message
                    if use_description_check:
                        message += f"\n🔍 *Description Check*: {verdict}\n"

                    time.sleep(1)
                    self.bot_helper.send_result(message)
                    self.sent_db.db.insert_one({"ID": car["ID"]})
                    inserted_ids.append(car["ID"])  # Add ID to the list
                    total_inserted_ids.append(car["ID"])  # Add to total list
                    logger.info(f"Car with ID {car['ID']} sent and saved to sent_listings.")

            # Log and send the number of cars sent for this configuration
            logger.info(
                f"Found {len(inserted_ids)} cars for {car_config['title_contains']} that were sent to Telegram.")
            self.bot_helper.send_result(f"Found {len(inserted_ids)} cars for *{car_config['title_contains'].capitalize()}* 🚗")

        # Send a summary log with the total inserted IDs
        if total_inserted_ids:
            summary_message = (
                f"📝 *Summary*: {len(total_inserted_ids)} cars sent to Telegram.\n"
                f"🆔 *Sent IDs*: {', '.join(total_inserted_ids)}"
            )
            self.bot_helper.send_result(summary_message)
            logger.info(f"Sent {len(total_inserted_ids)} car IDs to Telegram.")

    def close_connections(self):
        """Close database connections."""
        self.db_helper.close_connection()
        self.sent_db.close_connection()

if __name__ == '__main__':
    notifier = CarNotifier()
    notifier.search_for_cars()
    notifier.close_connections()
