# 🛗 Nouveau Voice Dispatch AI (MVP)

This is a voice-to-voice AI dispatch agent designed for Nouveau Elevator. It acts as a first-line support agent, handling maintenance calls, filtering emergencies, and generating structured JSON tickets automatically.

## 🚀 Features
- **Real-Time Voice Conversation:** Uses Llama 3.3 (70B) & Whisper for near-zero latency.
- **Cross-Platform:** Runs natively on **Windows** and **macOS**.
- **Infinite Server Mode:** Automatically resets after every call to handle back-to-back testing.
- **Emergency Logic Gates:** Detects "stuck" or "hurt" passengers and triggers an escalation protocol.
- **Smart Data Extraction:** Saves a JSON ticket with Name, Phone, Address, and Issue after every call.

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/sriram369/Nouveau-LLM.git
cd Nouveau-LLM
```

### 2. Add API Key
1. Create a file named `key.txt` in the main folder.
2. Paste your **Groq API Key** inside it.
   *(Note: This file is ignored by Git for security)*.

---

### 3. Install Dependencies (Choose your OS)

#### 🪟 For Windows Users (Greg)
Run these commands in PowerShell or Command Prompt:
```bash
# 1. Install microphone driver helper
pip install pipwin

# 2. Install the specific audio driver
pipwin install pyaudio

# 3. Install the rest of the AI libraries
pip install -r requirements.txt
```

#### 🍎 For Mac Users
```bash
# 1. Install PortAudio (Requires Homebrew)
brew install portaudio

# 2. Install Python libraries
pip install -r requirements.txt
```

---

## ▶️ How to Run
Once installed, start the dispatch server:

```bash
python main.py
```

1. The server will initialize.
2. Press **ENTER** to simulate an incoming phone call.
3. Speak clearly into your microphone.
4. When the call ends, the system will generate a `ticket_timestamp.json` file and reset for the next caller.

---

## 📂 Project Structure
- `main.py`: The core logic (Audio, AI Brain, File Saving).
- `system_prompt.txt`: The personality and logic rules for "Hailey".
- `requirements.txt`: List of python libraries needed.
- `key.txt`: (You must create this) Stores the secret API key.

