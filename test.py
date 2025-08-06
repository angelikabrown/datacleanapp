import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Validate API key
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY is not set. Please check your .env file or environment variables.")

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
