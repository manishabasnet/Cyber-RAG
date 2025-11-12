import os
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("key")
print(openai_api_key)