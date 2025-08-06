import os
from dotenv import load_dotenv
import openai

load_dotenv()
print("Loaded API Key:", os.getenv("OPENAI_API_KEY"))  # Debugging line

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set. Please check your .env file or environment variables.")

openai.api_key = api_key

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello!"}
    ]
)

print(response['choices'][0]['message']['content'])
