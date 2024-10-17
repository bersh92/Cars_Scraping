# helpers/chatGptDescriptionCheck.py

import os
import openai
from dotenv import load_dotenv
import logging

# Load API key from .env file
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatGptDescriptionCheck:
    def __init__(self):
        self.system_prompt = (
            "You are an assistant helping to evaluate car listings in Canada. "
            "Based on the description provided, respond with one of the following words exactly: 'good', 'bad', or 'maybe ok'. "
            "Consider if the car might be a scam, if it has issues with the engine or transmission, "
            "if it needs a lot of repairs, or if it can pass a road test. "
            "Respond only with 'good', 'bad', or 'maybe ok', and nothing else."
        )

    def check_the_car(self, description):
        try:
            # Call the ChatCompletion endpoint
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Use "gpt-4" if you have access
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": description}
                ],
                max_tokens=3,
                temperature=0.0,
                n=1,
                stop=None
            )

            # Get the assistant's reply
            result = response.choices[0].message['content'].strip().lower()
            logger.info(f"OpenAI response: '{result}'")

            # Check for exact matches
            if result == "good":
                return True
            elif result == "bad":
                return False
            elif result == "maybe ok":
                return None  # maybe ok
            else:
                # Handle unexpected responses
                message = f"Unexpected response from OpenAI: '{result}'"
                logger.warning(message)
                return message
        except Exception as e:
            # Handle exceptions (e.g., API errors)
            logger.error(f"OpenAI API error: {e}")
            raise  # Re-raise the exception to make the script fail
