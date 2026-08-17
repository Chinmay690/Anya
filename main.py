import os
import tempfile
import subprocess
import datetime

import requests
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

from dotenv import load_dotenv



# CONFIGURATION


load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# Local Ollama model
OLLAMA_MODEL = "qwen3:4b-instruct"
OLLAMA_URL = "http://localhost:11434/api/chat"

if not ELEVENLABS_API_KEY:
    raise RuntimeError(
        "ELEVENLABS_API_KEY is missing. Add it to your .env file."
    )

if not ELEVENLABS_VOICE_ID:
    raise RuntimeError(
        "ELEVENLABS_VOICE_ID is missing. Add it to your .env file."
    )



# AUDIO SETTINGS

SAMPLE_RATE = 44100
RECORD_SECONDS = 5



# ANYA PERSONALITY


SYSTEM_PROMPT = """
You are Anya, a friendly anime-inspired desktop AI assistant.

Personality:
- Friendly
- Playful
- Intelligent
- Slightly energetic
- Helpful
- Natural and conversational

Keep normal answers relatively concise because your responses
will be spoken aloud.

You are running on the user's Mac.

You should never claim to have performed a computer action
unless the program actually performed it.

Do not mention that you are Qwen unless the user specifically
asks what AI model you are using.

Speak naturally like a helpful anime-inspired assistant.
"""



# RECORD MICROPHONE


def record_audio():

    print("\n🎤 Anya is listening...")

    try:

        audio = sd.rec(
            int(RECORD_SECONDS * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32"
        )

        sd.wait()

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        )

        temp_file.close()

        sf.write(
            temp_file.name,
            audio,
            SAMPLE_RATE
        )

        print("✅ Recording finished.")

        return temp_file.name

    except Exception as error:

        print("❌ Microphone error:", error)

        return None


# ============================================================
# SPEECH TO TEXT
# ============================================================

def listen():

    audio_file = record_audio()

    if not audio_file:
        return ""

    print("🧠 Anya is understanding you...")

    recognizer = sr.Recognizer()

    try:

        with sr.AudioFile(audio_file) as source:

            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data)

        print(f"\nYou: {text}")

        return text

    except sr.UnknownValueError:

        print("Anya: I couldn't understand that.")

        return ""

    except sr.RequestError as error:

        print("❌ Speech recognition service error:")
        print(error)

        return ""

    finally:

        try:
            os.remove(audio_file)
        except OSError:
            pass



# LOCAL AI BRAIN — OLLAMA + QWEN3

def ask_ai(user_message):

    print("🤖 Anya is thinking...")

    current_time = datetime.datetime.now().strftime(
        "%A, %d %B %Y, %I:%M %p"
    )

    prompt = f"""
Current date and time:
{current_time}

User message:
{user_message}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "think": False
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:

            print("❌ Ollama error:")
            print(response.text)

            return (
                "Sorry, I couldn't connect to my local AI brain."
            )

        result = response.json()

        answer = result["message"]["content"].strip()

        return answer

    except requests.exceptions.ConnectionError:

        print("❌ Could not connect to Ollama.")

        return (
            "My local AI brain isn't running right now. "
            "Please start Ollama and try again."
        )

    except Exception as error:

        print("❌ AI error:")
        print(error)

        return (
            "Sorry, something went wrong with my AI brain."
        )



# ANIME TTS — ELEVENLABS


def speak(text):

    print(f"\n🎀 Anya: {text}")

    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/"
        f"{ELEVENLABS_VOICE_ID}"
    )

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.35,
            "similarity_boost": 0.8,
            "style": 0.5,
            "use_speaker_boost": True
        }
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=60
        )

        if response.status_code != 200:

            print("❌ ElevenLabs error:")
            print(response.text)

            return

        temp_audio = tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        )

        temp_audio.write(response.content)
        temp_audio.close()

        # macOS audio playback
        subprocess.run(
            ["afplay", temp_audio.name],
            check=False
        )

        os.remove(temp_audio.name)

    except Exception as error:

        print("❌ Voice error:")
        print(error)


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    print("\n")
    print("=" * 50)
    print("             🎀 ANYA AI ASSISTANT")
    print("=" * 50)
    print()
    print("Anya is online.")
    print("Say 'goodbye' or 'exit' to shut her down.")
    print()

    speak(
        "Hello Chinmay! I'm Anya. Your AI assistant is now online."
    )

    while True:

        user_message = listen()

        if not user_message:
            continue

        command = user_message.lower().strip()

        # EXIT COMMAND
        if (
            "goodbye" in command
            or "goodbye anya" in command
            or command == "exit"
            or command == "quit"
            or "shut down" in command
        ):

            speak("Okay! I'll see you later.")

            break

        # AI RESPONSE
        answer = ask_ai(user_message)

        speak(answer)

    print("\n👋 Anya has been shut down.")



# START


if __name__ == "__main__":
    main()