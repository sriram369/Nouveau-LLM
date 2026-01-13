# Nouveau Elevator Dispatch Bot (MVP)

An AI-powered voice dispatch agent designed for Nouveau Elevator. 
It answers calls, detects emergencies, and logs maintenance tickets automatically using the "Retell AI" logic flow.

## Features
- **Voice Interface:** Zero-latency conversation using Groq (Llama 3.3).
- **Emergency Logic:** Automatically detects entrapments and triggers escalation.
- **Data Capture:** Extracts JSON payloads for Name, ID, Address, and Issue.
- **Bilingual:** Supports English and Spanish.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Add your Groq API Key to a file named `key.txt`.
3. Run the bot: `python3 main.py`