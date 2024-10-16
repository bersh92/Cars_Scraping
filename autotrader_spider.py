import json
import os
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import scrapy
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess

from helpers.dbHelper import DbHelper
from helpers.telegramHelper import TelegramBotHelper

load_dotenv()

def sanitize_price(price):
    if price:  # Check if price is not None
        # Remove non-numeric characters like $ and commas, and convert to float
        price_cleaned = re.sub(r'[^\d.]', '', price)
        return float(price_cleaned) if price_cleaned else None
    return None  # Return None if price is None

def sanitize_mileage(mileage):
    if mileage:  # Check if mileage is not None
        mileage_cleaned = re.sub(r'[^\d]', '', mileage)
        return int(mileage_cleaned) if mileage_cleaned else None
    return None  # Return None if mileage is None

def sanitize_proximity(proximity):
    if proximity:  # Check if proximity is not None
        # Convert proximity value to integer (remove extra text like "km")
        proximity_cleaned = re.sub(r'[^\d]', '', proximity)
        return int(proximity_cleaned) if proximity_cleaned else None
    return None  # Return None if proximity is None


class AutoTraderSpider(scrapy.Spider):
    name = 'autotrader_spider'
    custom_settings = {
        'USER_AGENT': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            ' AppleWebKit/537.36 (KHTML, like Gecko)'
            ' Chrome/90.0.4430.85 Safari/537.36'
        ),
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 2,  # Number of retries for failed requests
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429, 403],
        'HTTPERROR_ALLOWED_CODES': [403],
        'HANDLE_HTTPSTATUS_LIST': [403],
    }

    project_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_dir, 'config.json')

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    start_urls = [config['start_url']]
    db_helper = DbHelper(os.getenv('DATABASE_NAME'), "listings")
    bot_helper = TelegramBotHelper()
    items = []

    def parse(self, response):
        # Check for 'Something went wrong.' message
        text = response.css('#MainPanel h4::text').get(default='')
        if 'Something went wrong.' in text:
            self.log("No car data found, stopping pagination.")
            print(response.body)
            return

        # Check for 403 Forbidden response
        if response.status == 403:
            self.log(f"Received 403 Forbidden at {response.url}")
            return

        # Select the product blocks
        car_data = response.css('div[id="result-item-inner-div"]')

        # Stop pagination if no containers are found
        if not car_data:
            self.log("No car data found, stopping pagination.")
            return

        for car in car_data:
            title = car.css('span.title-with-trim::text').get(default='')
            price = car.css('span.price-amount::text').get(default='')
            url = car.css('a.inner-link::attr(href)').get()
            mileage = car.css('span.odometer-proximity::text').get(default='')
            parent_id = car.xpath('./ancestor::div[1]/@id').get(default='')
            proximity = car.css('.proximity [class="proximity-text"]::text').get(default='')

            # Sanitize and format the data before storing
            sanitized_price = sanitize_price(price)
            sanitized_mileage = sanitize_mileage(mileage)
            sanitized_proximity = sanitize_proximity(proximity)

            self.items.append({
                'Title': title.strip() if title else None,
                'Price': sanitized_price,
                'Mileage': sanitized_mileage,
                'Product URL': response.urljoin(url) if url else None,
                'ID': parent_id.strip() if parent_id else None,
                'Proximity': sanitized_proximity
            })

        # Handle pagination as before
        yield from self.paginate(response)

    def paginate(self, response):
        """Handle pagination by increasing the 'rcs' value based on the current page."""
        current_url = response.url
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)

        # Extract the 'rcs' parameter, defaulting to 0 if not present
        current_rcs = int(query_params.get('rcs', [0])[0])
        next_rcs = current_rcs + 100  # Increment by 100

        # Set a maximum rcs value to avoid triggering server-side limits
        MAX_RCS = 110000  # Adjust based on observations

        if next_rcs >= MAX_RCS:
            self.log(f"Reached the maximum rcs value of {MAX_RCS}, stopping pagination.")
            return

        # Update the 'rcs' parameter in the query string
        query_params['rcs'] = [str(next_rcs)]

        # Rebuild the new URL with the updated query parameters
        new_query = urlencode(query_params, doseq=True)
        next_page_url = urlunparse(parsed_url._replace(query=new_query))

        # Log and request the next page
        yield scrapy.Request(url=next_page_url, callback=self.parse)

    def closed(self, reason):
        try:
            if reason == "finished":
                self.db_helper.delete_all()
                self.db_helper.insert_many(self.items)
                self.bot_helper.send_log(f"Spider finished. New listings: {len(self.items)}")
        except Exception as e:
            self.bot_helper.send_log(f"Spider failed: {e}")
        finally:
            self.db_helper.close_connection()


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(AutoTraderSpider)
    process.start()
