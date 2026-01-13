import os
import sys
import asyncio
import json
from datetime import datetime
from groq import Groq
import speech_recognition as sr
import edge_tts

# --- CONFIGURATION ---
def load_key():
    try:
        if os.path.exists("key.txt"):
            with open("key.txt", "r") as f:
                return f.read().strip()
        else:
            print("CRITICAL: Create 'key.txt' with your Groq API Key!")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

GROQ_API_KEY = load_key()
VOICE_NAME = "en-US-AriaNeural"
MODEL_ID = "llama-3.3-70b-versatile" # The stable Groq model

client = Groq(api_key=GROQ_API_KEY)
rec = sr.Recognizer()
mic = sr.Microphone()

def speak(text):
    """Speaks text, but ignores special command tokens like [TERMINATE_CALL]."""
    
    # 1. Clean the text for Audio (Don't say the robot commands)
    clean_text = text.replace("[TERMINATE_CALL]", "").replace("[TRANSFER_CALL]", "")
    
    if not clean_text.strip():
        return # Nothing to say
        
    print(f"HAILEY: {clean_text}")
    
    output_file = "hailey_response.mp3"
    async def generate_audio():
        communicate = edge_tts.Communicate(clean_text, VOICE_NAME)
        await communicate.save(output_file)

    try:
        asyncio.run(generate_audio())
        os.system(f"afplay {output_file}")
        if os.path.exists(output_file):
            os.remove(output_file)
    except Exception:
        pass

def listen():
    print("\n(Listening...)")
    with mic as source:
        rec.adjust_for_ambient_noise(source)
        try:
            audio = rec.listen(source, timeout=5)
            print("(Thinking...)")
            return rec.recognize_google(audio)
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""

def load_brain():
    try:
        with open("system_prompt.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        print("Error: system_prompt.txt not found!")
        sys.exit(1)

def ask_groq(history):
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=history,
            temperature=0.6,
            max_tokens=1024
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"System Error: {e}"

def save_ticket(conversation_history, status="Routine"):
    print(f"\n[GENERATING TICKET PAYLOAD - STATUS: {status}]")
    
    prompt = f"""
    Analyze this conversation and extract JSON data.
    HISTORY:
    {conversation_history}
    
    Return ONLY valid JSON with fields: 
    - caller_name
    - caller_phone
    - location_address
    - equipment_id
    - issue_description
    - is_emergency (boolean)
    - resolution_status (Set this to: "{status}")
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        clean = completion.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        start = clean.find('{')
        end = clean.rfind('}') + 1
        if start != -1 and end != -1:
            clean = clean[start:end]
            
        filename = f"ticket_{datetime.now().strftime('%H%M%S')}.json"
        with open(filename, "w") as f:
            f.write(clean)
        print(f"SUCCESS: Saved to {filename}")
        print(clean)
    except Exception as e:
        print(f"Failed to save ticket: {e}")

def hailey_phone_call():
    print("------------------------------------------------")
    print(f"   NOUVEAU ELEVATOR: RETELL LOGIC MODE          ")
    print("------------------------------------------------")
    
    chat_history = [{"role": "system", "content": load_brain()}]
    greeting = "Nouveau Elevator, this is Hailey. What is the address of the building?"
    speak(greeting)
    chat_history.append({"role": "assistant", "content": greeting})

    while True:
        user_input = listen()
        if not user_input: continue
        
        print(f"CALLER: {user_input}")
        chat_history.append({"role": "user", "content": user_input})
        
        # Get AI Response
        response_text = ask_groq(chat_history)
        
        # CHECK FOR RETELL COMMAND SIGNALS
        if "[TERMINATE_CALL]" in response_text:
            speak(response_text) # Say the goodbye part
            print("\n[SIGNAL DETECTED: TERMINATE_CALL]")
            save_ticket(str(chat_history), status="Completed")
            break
            
        if "[TRANSFER_CALL]" in response_text:
            speak(response_text)
            print("\n[SIGNAL DETECTED: WARM TRANSFER INITIATED]")
            print("Transferring to Human Operator (555-0199)...")
            save_ticket(str(chat_history), status="Escalated")
            break

        # Normal conversation flow
        speak(response_text)
        chat_history.append({"role": "assistant", "content": response_text})

if __name__ == "__main__":
    hailey_phone_call()