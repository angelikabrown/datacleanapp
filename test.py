import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
print("Loaded API Key:", os.getenv("OPENAI_API_KEY"))  # Debugging line

# Get the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set. Please check your .env file or environment variables.")

# Set the OpenAI API key
openai.api_key = api_key

# Make a request to OpenAI
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello!"}
    ]
)

# Print the response
print(response['choices'][0]['message']['content'])