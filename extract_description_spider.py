import logging
import os
import random
import scrapy
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess

from helpers.dbHelper import DbHelper
from helpers.telegramHelper import TelegramBotHelper  # Import your TelegramBotHelper

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('extract_description_spider')


class DescriptionSpider(scrapy.Spider):
    name = 'description_spider'
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 5,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429, 403, 302],
        'REDIRECT_ENABLED': True,
        'COOKIES_ENABLED': True,  # Enable cookies handling
        'COOKIES_DEBUG': True,
        'LOG_LEVEL': 'INFO',  # Set logging level to INFO
        'LOG_STDOUT': False,
    }

    def __init__(self, *args, **kwargs):
        super(DescriptionSpider, self).__init__(*args, **kwargs)
        project_dir = os.path.dirname(os.path.abspath(__file__))

        # Initialize database helper
        self.db_helper = DbHelper(os.getenv('DATABASE_NAME'), "extracted_cars")

        # Get the list of cars from the extracted_cars collection
        self.cars = list(self.db_helper.db.find({}))

        # Initialize your TelegramBotHelper
        self.bot_helper = TelegramBotHelper()

        # Initialize counters
        self.total_descriptions_extracted = 0

    def start_requests(self):
        # User-Agent list to randomize headers for each request
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'
        ]

        for car in self.cars:
            product_url = car.get('Product URL')
            car_id = car.get('ID')
            if product_url and car_id:
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Referer': 'https://www.google.com/',
                }
                yield scrapy.Request(
                    url=product_url,
                    headers=headers,
                    callback=self.parse,
                    meta={'car_id': car_id, 'product_url': product_url},
                    dont_filter=True,  # Ensures no filtering on URLs
                    errback=self.errback_handle
                )

    def parse(self, response):
        car_id = response.meta['car_id']
        product_url = response.meta['product_url']
        logger.info(f"Processing car ID {car_id}")

        # Initialize description
        description = ''

        # Extract description using meta tag
        description = response.xpath('//meta[@name="description"]/@content').get()

        if description:
            description = description.strip()
            if len(description) >= 3:
                logger.info(f"Extracted description for car ID {car_id}")
                self.total_descriptions_extracted += 1  # Increment counter
            else:
                logger.warning(f"Description too short for car ID {car_id}")
                description = ''  # Optionally set description to empty if too short
        else:
            logger.warning(f"No description found for car ID {car_id}")
            description = ''  # Ensure description is an empty string

        # Update the database entry with the description
        self.db_helper.db.update_one(
            {'ID': car_id},
            {'$set': {'Description': description}}
        )
        logger.info(f"Updated car ID {car_id} with description.")

    def errback_handle(self, failure):
        # Log errors and continue
        request = failure.request
        car_id = request.meta.get('car_id')
        logger.error(f"Request failed for car ID {car_id}: {failure.value}")

    def closed(self, reason):
        # Send message via Telegram with the total descriptions extracted
        message = f"Total descriptions extracted and stored: {self.total_descriptions_extracted}"
        self.bot_helper.send_result(message)
        logger.info(f"Sent Telegram message: {message}")

        # Close database connection
        self.db_helper.close_connection()
        logger.info(f"Spider closed: {reason}")


if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(DescriptionSpider)
    process.start()
