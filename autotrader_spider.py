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
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'DOWNLOAD_DELAY': 1
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
        # Select the product blocks
        car_data = response.css('div[id="result-item-inner-div"]')

        # Stop pagination if no containers are found
        if not car_data:
            self.log("No car data found, stopping pagination.")
            return

        for car in car_data:
            title = car.css('span.title-with-trim::text').get()
            price = car.css('span.price-amount::text').get()
            url = car.css('a.inner-link::attr(href)').get()
            mileage = car.css('span.odometer-proximity::text').get()
            parent_id = car.xpath('./ancestor::div[1]/@id').get()
            proximity = car.css('.proximity [class="proximity-text"]::text').get()

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

        # Check if we've exceeded the limit (in your case, 110000)
        if next_rcs >= 200:
            self.log(f"Reached the limit of {next_rcs}, stopping pagination.")
            return

        # Update the 'rcs' parameter in the query string
        query_params['rcs'] = [str(next_rcs)]

        # Rebuild the new URL with the updated query parameters
        new_query = urlencode(query_params, doseq=True)
        next_page_url = urlunparse(parsed_url._replace(query=new_query))

        # Log and request the next page
        # self.log(f"Next page URL: {next_page_url}")
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
