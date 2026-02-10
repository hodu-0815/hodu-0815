import google.generativeai as genai
import toml

# Load secrets
try:
    secrets = toml.load(".streamlit/secrets.toml")
    api_key = secrets["GOOGLE_API_KEY"]
except Exception as e:
    print(f"Error loading secrets: {e}")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
