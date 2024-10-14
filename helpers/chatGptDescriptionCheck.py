import os
import openai
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class ChatGptDescriptionCheck:
    def __init__(self):
        self.prompt_template = (
            "I am in Canada looking for a car. Based on the description below, "
            "determine if the car is 'good', 'bad', or 'maybe ok'. Consider if "
            "the car might be a scam, if it has issues with the engine or transmission, "
            "if it needs a lot of repairs, or if it can pass a road test. Respond only with "
            "'good', 'bad', or 'maybe ok'. Here is the description:\n\n{}"
        )

    def check_the_car(self, description):
        # Prepare the prompt
        prompt = self.prompt_template.format(description)

        # Call ChatGPT API
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=50,
            temperature=0.5
        )

        # Get the answer and return True for good, False for bad, maybe ok otherwise
        result = response.choices[0].text.strip().lower()
        if result == "good":
            return True
        elif result == "bad":
            return False
        else:
            return None  # maybe ok