
# Car Scraper & Telegram Notifier

![Car Search Bot](img/1.png)
![Car Search Bot](img/2.png)

## Overview

This project allows you to scrape car listings from a specified source and notify users on Telegram about new cars that match your search criteria. It leverages AI for enhanced description checks to ensure the cars have detailed information.

### Features:
- Scrape used car listings based on customizable search parameters.
- Extract car descriptions using AI for detailed information.
- Send notifications with car details to a Telegram group/chat.
- Configurable via a `config.json` file for flexible search and notification settings.

## Project Structure

- **`autotrader_spider.py`**: Scrapes car listings from the specified website based on your search parameters (price, mileage, etc.).
- **`car_extractor.py`**: Extracts specific car details (e.g., ID, URL) from the listings.
- **`extract_description_spider.py`**: Extracts detailed descriptions for each car, performing an AI-enhanced check for completeness.
- **`car_notifier.py`**: Sends notifications about new cars to a specified Telegram chat.
- **`pipeline.py`**: A script that runs all the above scripts in sequence to automate the full pipeline.

## Requirements

1. **Python 3.x** installed on your system.
2. **Scrapy** and other required libraries. You can install them using:
    ```bash
    pip install -r requirements.txt
    ```

3. **MongoDB** for storing car data. Make sure you have a connection string for MongoDB.
4. **Telegram Bot**: You will need a bot token from Telegram to send notifications.

## Setup Instructions

### 1. Create a `.env` File

In the root directory of the project, create a `.env` file with the following variables:

```env
# MongoDB
MONGO_CONNECTION_STRING="mongodb+srv://your_username:your_password@cluster0.mongodb.net/?retryWrites=true&w=majority"

# Telegram Bot
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"

# Database Name
DATABASE_NAME="AUTO"

# OpenAI API Key
OPENAI_API_KEY="your_openai_api_key"
```

Replace the placeholder values with your actual credentials.

### 2. Configure Search Parameters

Edit the `config.json` file to define your search criteria:

```json
{
    "cars": [
        {
            "max_price": 4000,
            "max_mileage": 250000,
            "max_proximity": 50,
            "title_contains": "hyundai",
            "min_year": 2011,
            "use_description_check": true
        },
        {
            "max_price": 4000,
            "max_mileage": 250000,
            "max_proximity": 50,
            "title_contains": "mazda",
            "min_year": 2011,
            "use_description_check": true
        }
    ],
    "start_url": "https://www.autotrader.ca/cars/on/mississauga/?rcp=100&rcs=0&srt=9",
    "telegram_chat_id_logging": "-your_chat_id_for_logs",
    "telegram_chat_id_results": "-your_chat_id_for_results"
}
```

- **`max_price`**: The maximum price of cars.
- **`max_mileage`**: The maximum mileage of cars.
- **`title_contains`**: The keyword to search for in the car title.
- **`use_description_check`**: Whether to use AI to validate car descriptions.
- **`telegram_chat_id_logging`**: Chat ID where logs will be sent.
- **`telegram_chat_id_results`**: Chat ID where the results will be sent.

### 3. Run the Pipeline

To run the entire scraping and notification process, use the `pipeline.py` script:

```bash
python pipeline.py
```

This script will run each step in sequence:
1. Scrape car listings.
2. Extract car details.
3. Scrape and validate car descriptions.
4. Notify Telegram chat with new car details.

### Customization

- You can modify the search parameters in the `config.json` file as per your requirements.
- Ensure that your `.env` file contains valid credentials for MongoDB, Telegram, and OpenAI.

## Logging

The project is configured to log important events, such as car description extractions and errors, to the console. Adjust the logging level in `pipeline.py` if you need more or less verbosity.

## License

This project is open-source and free to use. Feel free to modify it for your needs.

---

For any questions or issues, please contact the repository maintainer.
