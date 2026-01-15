import os
import sys
import asyncio
import json
import time
import platform
import subprocess
import tempfile
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
# English Voice
VOICE_EN = "en-US-AriaNeural"
# Spanish Voice (Mexican Spanish)
VOICE_ES = "es-MX-DaliaNeural"

MODEL_ID = "llama-3.3-70b-versatile" 
WHISPER_ID = "distil-whisper-large-v3-en" # Note: Groq's "distil" is English focused, but often catches Spanish. 
# For true multilingual on Groq, we ideally want 'whisper-large-v3' if available, 
# but let's try to use the translation capabilities or sticking to standard whisper if available.
# Actually, for Groq, let's use the versatile whisper if possible or standard translation. 
# Re-checking Groq docs: 'distil-whisper-large-v3-en' is English only. 
# We should use 'whisper-large-v3' for multilingual.
WHISPER_MODEL = "whisper-large-v3" 

client = Groq(api_key=GROQ_API_KEY)
rec = sr.Recognizer()
mic = sr.Microphone()

def detect_language_and_pick_voice(text):
    """Simple check to swap accent if response is Spanish."""
    # Common Spanish words to trigger the switch
    spanish_triggers = ["hola", "gracias", "ayuda", "estoy", "donde", "sí", "claro", "momento"]
    
    # Check if a significant portion of words are Spanish triggers
    count = sum(1 for word in text.lower().split() if word.strip(".,!?") in spanish_triggers)
    
    if count > 0 or "¿" in text or "ñ" in text:
        return VOICE_ES
    return VOICE_EN

def speak(text):
    """Speaks text, automatically switching accent for Spanish."""
    
    clean_text = text.replace("[TERMINATE_CALL]", "").replace("[TRANSFER_CALL]", "")
    if not clean_text.strip(): return 
        
    print(f"HAILEY: {clean_text}")
    
    # Smart Voice Switching
    selected_voice = detect_language_and_pick_voice(clean_text)
    
    output_file = "hailey_response.mp3"
    
    async def generate_audio():
        communicate = edge_tts.Communicate(clean_text, selected_voice)
        await communicate.save(output_file)

    try:
        asyncio.run(generate_audio())
        
        current_os = platform.system()
        if current_os == "Darwin":  # Mac
            os.system(f"afplay {output_file}")
        elif current_os == "Windows":  # Windows
            subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{output_file}').PlaySync();"])
            
        if os.path.exists(output_file):
            os.remove(output_file)
    except Exception as e:
        print(f"Voice Error: {e}")

def listen_with_whisper():
    """Records audio and uses Groq Whisper for Multilingual understanding."""
    print("\n(Listening...)")
    with mic as source:
        rec.pause_threshold = 1.0
        rec.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            # Record audio locally
            audio_data = rec.listen(source, timeout=10, phrase_time_limit=20)
            print("(Transcribing...)")
            
            # Save temporary file for Whisper
            with open("temp_audio.wav", "wb") as f:
                f.write(audio_data.get_wav_data())
            
            # Send to Groq Whisper (Multilingual)
            with open("temp_audio.wav", "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=("temp_audio.wav", file.read()),
                    model=WHISPER_MODEL, 
                    response_format="json",
                    temperature=0.0
                )
            
            return transcription.text
            
        except sr.WaitTimeoutError:
            return ""
        except Exception as e:
            # Fallback to Google if Whisper fails (Google is decent at simple Spanish)
            print(f"Whisper Error: {e}, trying Google fallback...")
            try:
                return rec.recognize_google(audio_data)
            except:
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
    
    Return ONLY valid JSON.
    NOTE: Even if conversation was Spanish, translate values to English.
    Fields: 
    - caller_name
    - caller_phone
    - location_address
    - equipment_id
    - issue_description
    - is_emergency (boolean)
    - resolution_status ("{status}")
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
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ticket_{timestamp}.json"
        
        with open(filename, "w") as f:
            f.write(clean)
        print(f"✅ SUCCESS: Saved to {filename}")
        print(clean)
    except Exception as e:
        print(f"Failed to save ticket: {e}")

# --- SERVER LOOP ---
def run_dispatch_server():
    print("================================================")
    print("   NOUVEAU AI DISPATCH SERVER (BILINGUAL)       ")
    print("================================================")

    while True:
        print("\n📞 [SYSTEM READY] Waiting for incoming call...")
        input("--> Press ENTER to simulate an incoming call...") 
        
        chat_history = [{"role": "system", "content": load_brain()}]
        
        greeting = "Nouveau Elevator, this is Hailey. How can I help?"
        speak(greeting)
        chat_history.append({"role": "assistant", "content": greeting})

        call_active = True
        while call_active:
            # CHANGED: Use Whisper instead of Google
            user_input = listen_with_whisper()
            
            if not user_input.strip(): 
                continue
            
            print(f"👤 CALLER: {user_input}")
            chat_history.append({"role": "user", "content": user_input})
            
            response_text = ask_groq(chat_history)
            
            if "[TERMINATE_CALL]" in response_text:
                speak(response_text)
                print("\n🔴 [CALL ENDED]")
                save_ticket(str(chat_history), status="Completed")
                call_active = False
                
            elif "[TRANSFER_CALL]" in response_text:
                speak(response_text)
                print("\n⚠️ [EMERGENCY TRANSFER INITIATED]")
                save_ticket(str(chat_history), status="Escalated")
                call_active = False
            else:
                speak(response_text)
                chat_history.append({"role": "assistant", "content": response_text})
        
        print("------------------------------------------------")
        print("♻️  Resetting system...")
        time.sleep(3)

if __name__ == "__main__":
    try:
        run_dispatch_server()
    except KeyboardInterrupt:
        print("\n[Server Shutdown]")
        