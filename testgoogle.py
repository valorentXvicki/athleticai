import google.generativeai as genai
import os

# Best Practice: Load key from environment variable, NEVER hardcode it
# Set GEMINI_API_KEY in your .env file or environment before running
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY environment variable is not set.")
    print("Please set it in your .env file or environment:")
    print("  export GEMINI_API_KEY=your-api-key-here")
    exit(1)

genai.configure(api_key=api_key)

# Using the correct model name
model = genai.GenerativeModel('gemini-1.5-flash')

response = model.generate_content("Hello, Gemini!")
print(response.text)