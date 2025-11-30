import os
import google.generativeai as genai

# os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY" # REMOVED FOR SECURITY
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
