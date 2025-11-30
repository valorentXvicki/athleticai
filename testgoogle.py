import google.generativeai as genai
import os

# Best Practice: Load key from environment variable, NEVER hardcode it
genai.configure(api_key=os.environ["AIzaSyAC9jca81ERbvc3WcOIAm-_yYB9ApRVEk0"]) 

# Using the correct model name
model = genai.GenerativeModel('gemini-1.5-flash')

response = model.generate_content("Hello, Gemini!")
print(response.text)