import google.generativeai as genai

# PASTE YOUR KEY HERE
genai.configure(api_key="AIzaSyBYmyEp9LuG6_JHEAN_Qtz4VGWtc0kZds4")

print("Listing available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
