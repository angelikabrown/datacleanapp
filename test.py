import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Get the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set. Please check your .env file or environment variables.")

# Initialize the new OpenAI client with your API key
openai.api_key = api_key

# Make a request to OpenAI using the client object
response = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello!"}
    ]
)

# Print the response
print(response.choices[0].message.content)