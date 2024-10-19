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
            "You are an expert vehicle evaluator specializing in assessing car listings in Canada. "
            "Based on the description provided, determine whether the car is in good condition and suitable for purchase. "
            "Specifically, consider the following factors:\n"
            "- Can the car pass a roadworthiness test and be legally driven on roads without issues?\n"
            "- Does the car have any significant mechanical problems, such as issues with the engine, transmission, or brakes?\n"
            "- Does the car require significant repairs or maintenance to be operational?\n"
            "- Is there any indication that the listing might be a scam or fraudulent?\n"
            "\n"
            "Respond with 'good' if the car appears to be in good condition and ready to drive without major issues. "
            "Respond with 'bad' if the car has significant problems, requires major repairs, or seems suspicious. "
            "Provide your response using only one of these words and nothing else."
        )

    def check_the_car(self, description):
        try:
            # Call the ChatCompletion endpoint
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": description}
                ],
                max_tokens=3,
                temperature=0.0,
                n=1
            )

            # Get the assistant's reply
            result = response.choices[0].message['content'].strip().lower()
            logger.info(f"OpenAI response: '{result}'")

            # Check for exact matches
            if result == "good":
                return True
            elif result == "bad":
                return False
            else:
                # Handle unexpected responses
                message = f"Unexpected response from OpenAI: '{result}'"
                logger.warning(message)
                return message
        except Exception as e:
            # Handle exceptions (e.g., API errors)
            logger.error(f"OpenAI API error: {e}")
            raise  # Re-raise the exception to make the script fail
