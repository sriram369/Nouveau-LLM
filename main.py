import os
import sys
import asyncio
import json
import time
import platform
import subprocess
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
MODEL_ID = "llama-3.3-70b-versatile" 

client = Groq(api_key=GROQ_API_KEY)
rec = sr.Recognizer()
mic = sr.Microphone()

def speak(text):
    """Speaks text, works on both Windows and Mac."""
    
    # Clean hidden commands so she doesn't say them out loud
    clean_text = text.replace("[TERMINATE_CALL]", "").replace("[TRANSFER_CALL]", "")
    
    if not clean_text.strip():
        return 
        
    print(f"HAILEY: {clean_text}")
    
    output_file = "hailey_response.mp3"
    
    async def generate_audio():
        communicate = edge_tts.Communicate(clean_text, VOICE_NAME)
        await communicate.save(output_file)

    try:
        asyncio.run(generate_audio())
        
        # Cross-Platform Player
        current_os = platform.system()
        if current_os == "Darwin":  # Mac
            os.system(f"afplay {output_file}")
        elif current_os == "Windows":  # Windows
            subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{output_file}').PlaySync();"])
            
        if os.path.exists(output_file):
            os.remove(output_file)
    except Exception as e:
        print(f"Voice Error: {e}")

def listen():
    """Listens with patience (doesn't cut you off)."""
    print("\n(Listening...)")
    with mic as source:
        rec.pause_threshold = 1.0  # Wait 1 seconds of silence
        rec.energy_threshold = 300 
        rec.dynamic_energy_threshold = True 
        rec.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = rec.listen(source, timeout=5, phrase_time_limit=20)
            print("(Thinking...)")
            return rec.recognize_google(audio)
        except sr.WaitTimeoutError:
            return "" # Silence
        except sr.UnknownValueError:
            return "" # Unintelligible
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
    print(f"\n📝 [GENERATING TICKET PAYLOAD - STATUS: {status}]")
    
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
        if start != -1:
            clean = clean[start:end]
            
        # Unique filename using timestamp down to the second
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ticket_{timestamp}.json"
        
        with open(filename, "w") as f:
            f.write(clean)
        print(f"✅ SUCCESS: Saved to {filename}")
        print(clean)
    except Exception as e:
        print(f"Failed to save ticket: {e}")

# --- THE NEW INFINITE DISPATCH LOOP ---
def run_dispatch_server():
    print("================================================")
    print("   NOUVEAU AI DISPATCH SERVER: ONLINE           ")
    print("   (Press Ctrl+C to stop the server)            ")
    print("================================================")

    while True:
        # 1. Reset Memory for New Call
        print("\n📞 [SYSTEM READY] Waiting for incoming call...")
        # Simulate a "Ring" delay or wait for user to hit Enter to start demo
        input("--> Press ENTER to simulate an incoming call...") 
        
        chat_history = [{"role": "system", "content": load_brain()}]
        
        # 2. Start Conversation
        greeting = "Nouveau Elevator, this is Hailey. How can I help?"
        speak(greeting)
        chat_history.append({"role": "assistant", "content": greeting})

        # 3. Conversation Loop
        call_active = True
        while call_active:
            user_input = listen()
            
            # If silence, just wait (don't send empty text to AI)
            if not user_input: 
                continue
            
            print(f"👤 CALLER: {user_input}")
            chat_history.append({"role": "user", "content": user_input})
            
            # Get AI Response
            response_text = ask_groq(chat_history)
            
            # --- LOGIC GATES ---
            if "[TERMINATE_CALL]" in response_text:
                speak(response_text)
                print("\n🔴 [CALL ENDED]")
                save_ticket(str(chat_history), status="Completed")
                call_active = False # Break inner loop
                
            elif "[TRANSFER_CALL]" in response_text:
                speak(response_text)
                print("\n⚠️ [EMERGENCY TRANSFER INITIATED]")
                print(">> DIALING HUMAN OPERATOR (555-0199)...")
                # Simulate transfer beep
                time.sleep(1) 
                print(">> CONNECTED.")
                save_ticket(str(chat_history), status="Escalated")
                call_active = False # Break inner loop
                
            else:
                # Normal reply
                speak(response_text)
                chat_history.append({"role": "assistant", "content": response_text})
        
        # 4. End of Call Cleanup
        print("------------------------------------------------")
        print("♻️  Resetting system for next caller in 3 seconds...")
        time.sleep(3)

if __name__ == "__main__":
    try:
        run_dispatch_server()
    except KeyboardInterrupt:
        print("\n[Server Shutdown]")