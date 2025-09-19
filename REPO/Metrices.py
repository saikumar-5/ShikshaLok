import time
import logging
import io
import os
from pydub import AudioSegment
import numpy as np
import requests
from datetime import datetime

# --- Configuration (copy from your main app for consistency) ---
# Configure logging to see detailed API errors in the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Sarvam API Key (replace with your actual key)
SARVAM_API_KEY = "sk_aov2qcwm_v6DDreRZzU6ntWRM5ixh8voS" 

# API Endpoints
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech" 

# Supported Languages (for testing purposes, ensure these are valid Sarvam codes)
TEST_SOURCE_LANGUAGE = "en-IN" # Example: English
TEST_TARGET_LANGUAGE = "hi-IN" # Example: Hindi

# --- Dummy Cost Model Parameters (adjust these based on Sarvam's pricing) ---
# These are placeholder values. You'll need to check Sarvam AI's actual pricing.
# Example: 1 USD = 83 INR (approx)
# If Sarvam charges per second of audio for STT and per character for translation.
COST_PER_SECOND_STT_USD = 0.00001 
COST_PER_CHAR_TRANSLATE_USD = 0.000005 

# --- API Call Functions (copied from your main app) ---
def call_stt_api(audio_segment: AudioSegment, api_key: str, lang_code: str = "auto"):
    wav_io = io.BytesIO()
    audio_segment = audio_segment.set_channels(1).set_frame_rate(16000).set_sample_width(2)
    audio_segment.export(wav_io, format="wav")
    wav_io.seek(0)
    files = {"file": ("audio.wav", wav_io.getvalue(), "audio/wav")}
    headers = {"api-subscription-key": api_key}
    data = {"language_code": lang_code if lang_code != "auto" else ""}

    start_time = time.time()
    try:
        response = requests.post(SARVAM_STT_URL, headers=headers, files=files, data=data, timeout=15) # Increased timeout for tests
        response.raise_for_status()
        end_time = time.time()
        latency = end_time - start_time

        response_data = response.json()
        transcript = response_data.get("transcript", "").strip()
        detected_language = response_data.get("language_code", lang_code)
        
        audio_duration_seconds = len(audio_segment) / 1000.0
        cost = audio_duration_seconds * COST_PER_SECOND_STT_USD

        return transcript, detected_language, latency, cost
    except requests.exceptions.HTTPError as e:
        logging.error(f"STT API HTTP Error: {e.response.status_code} {e.response.reason} - {e.response.text}")
        return "", lang_code, 0.0, 0.0
    except requests.exceptions.RequestException as e:
        logging.error(f"STT API Request Error: {e}")
        return "", lang_code, 0.0, 0.0
    except Exception as e:
        logging.error(f"STT API Unexpected Error: {e}")
        return "", lang_code, 0.0, 0.0

def call_translate_api(text: str, source_lang_code: str, target_lang_code: str, api_key: str):
    if not text.strip():
        return "", 0.0, 0.0
    
    start_time = time.time()
    try:
        headers = {"api-subscription-key": api_key, "Content-Type": "application/json"}
        data = {
            "input": text,
            "source_language_code": source_lang_code,
            "target_language_code": target_lang_code,
            "speaker_gender": "Male",
            "mode": "formal",
            "model": "mayura:v1",
            "enable_preprocessing": True
        }
        response = requests.post(SARVAM_TRANSLATE_URL, headers=headers, json=data, timeout=15) # Increased timeout for tests
        response.raise_for_status()
        end_time = time.time()
        latency = end_time - start_time

        result = response.json()
        translated_text = result.get("translated_text", "Translation failed").strip()
        
        cost = len(text) * COST_PER_CHAR_TRANSLATE_USD

        return translated_text, latency, cost
    except requests.exceptions.HTTPError as e:
        logging.error(f"Translate API HTTP Error: {e.response.status_code} {e.response.reason} - {e.response.text}")
        return f"Translation API Error: {e.response.text}", 0.0, 0.0
    except requests.exceptions.RequestException as e:
        logging.error(f"Translate API Request Error: {e}")
        return f"Translation Error: {str(e)}", 0.0, 0.0
    except Exception as e:
        logging.error(f"Translate API Unexpected Error: {e}")
        return f"Translation Error: {str(e)}", 0.0, 0.0

# --- Test Data Setup ---

# Placeholder for creating dummy audio files if you don't have real ones.
# IMPORTANT: For actual STT testing, replace these with paths to real audio files.
def create_dummy_audio_file(filename, duration_sec, sample_rate=16000, channels=1, sample_width=2):
    """Creates a silent WAV file for testing purposes. STT will return empty."""
    samples = np.zeros(int(duration_sec * sample_rate), dtype=np.int16)
    audio_segment = AudioSegment(samples.tobytes(), frame_rate=sample_rate, sample_width=sample_width, channels=channels)
    audio_segment.export(filename, format="wav")
    return filename

# List of real audio files (WAV, MP3, etc.) for STT testing
# You MUST replace these with actual paths to your test audio files.
AUDIO_TEST_FILES = {
    "short_audio_1": "audio_samples/short_sample.wav",  # Example: "Hello, how are you?" (5 sec)
    "medium_audio_1": "audio_samples/medium_sample.wav", # Example: A paragraph (15 sec)
    "long_audio_1": "audio_samples/long_sample.wav",     # Example: A minute-long speech (30 sec max for single call)
    # Add more as needed
}

# Example of creating dummy audio files for initial testing if you don't have real ones
# Ensure 'dummy_audio_files' directory exists
if not os.path.exists("dummy_audio_files"):
    os.makedirs("dummy_audio_files")
# dummy_audio_short_path = create_dummy_audio_file("dummy_audio_files/dummy_short.wav", 5)
# dummy_audio_medium_path = create_dummy_audio_file("dummy_audio_files/dummy_medium.wav", 15)
# dummy_audio_long_path = create_dummy_audio_file("dummy_audio_files/dummy_long.wav", 30)

# Replace the above AUDIO_TEST_FILES with the dummy paths for initial no-real-audio runs:
# AUDIO_TEST_FILES = {
#     "dummy_short": dummy_audio_short_path,
#     "dummy_medium": dummy_audio_medium_path,
#     "dummy_long": dummy_audio_long_path,
# }


# Text data for text-to-text translation testing
TEXT_TEST_CASES = {
    "short_text_1": "Hello, how are you?",
    "medium_text_1": "The quick brown fox jumps over the lazy dog. This is a medium-length sentence to test translation latency.",
    "long_text_1": "In the bustling city, amidst the towering skyscrapers and vibrant markets, a sense of quiet introspection settled upon the solitary traveler. He pondered the vastness of the universe and his minuscule place within it, finding both comfort and awe in the thought. The sounds of the city faded into a distant hum as his mind delved deeper into philosophical musings, searching for answers that perhaps did not exist, yet the journey of seeking itself was fulfilling."
}

# --- Metric Test Functions ---
def run_audio_stt_and_translate_test(file_path, test_name, source_lang, target_lang):
    results = {
        "Test Name": test_name,
        "Input Type": "Audio",
        "Source Language": source_lang,
        "Target Language": target_lang,
        "Audio Duration (s)": 0.0,
        "STT Latency (s)": 0.0,
        "Translate Latency (s)": 0.0,
        "Total API Latency (s)": 0.0,
        "STT Cost (USD)": 0.0,
        "Translate Cost (USD)": 0.0,
        "Total API Cost (USD)": 0.0,
        "STT Transcript": "",
        "Translated Text": "",
        "Notes": ""
    }
    
    try:
        audio_segment = AudioSegment.from_file(file_path)
        results["Audio Duration (s)"] = len(audio_segment) / 1000.0

        # Step 1: Speech-to-Text
        transcript, detected_lang, stt_latency, stt_cost = call_stt_api(audio_segment, SARVAM_API_KEY, source_lang)
        results["STT Latency (s)"] = stt_latency
        results["STT Cost (USD)"] = stt_cost
        results["STT Transcript"] = transcript
        results["Notes"] += f"STT detected lang: {detected_lang}. "

        if not transcript:
            results["Notes"] += "STT returned empty transcript. "
            return results

        # Step 2: Translate
        final_source_lang = detected_lang if source_lang == "auto" else source_lang
        translated_text, translate_latency, translate_cost = call_translate_api(transcript, final_source_lang, target_lang, SARVAM_API_KEY)
        results["Translate Latency (s)"] = translate_latency
        results["Translate Cost (USD)"] = translate_cost
        results["Translated Text"] = translated_text

        results["Total API Latency (s)"] = stt_latency + translate_latency
        results["Total API Cost (USD)"] = stt_cost + translate_cost

    except FileNotFoundError:
        results["Notes"] = f"Error: Audio file not found at {file_path}"
    except Exception as e:
        results["Notes"] = f"An unexpected error occurred: {e}"
    
    return results

def run_text_translate_test(text_input, test_name, source_lang, target_lang):
    results = {
        "Test Name": test_name,
        "Input Type": "Text",
        "Source Language": source_lang,
        "Target Language": target_lang,
        "Text Length (chars)": len(text_input),
        "Translate Latency (s)": 0.0,
        "Translate Cost (USD)": 0.0,
        "Translated Text": "",
        "Notes": ""
    }
    
    try:
        translated_text, translate_latency, translate_cost = call_translate_api(text_input, source_lang, target_lang, SARVAM_API_KEY)
        results["Translate Latency (s)"] = translate_latency
        results["Translate Cost (USD)"] = translate_cost
        results["Translated Text"] = translated_text
        results["Total API Latency (s)"] = translate_latency
        results["Total API Cost (USD)"] = translate_cost

    except Exception as e:
        results["Notes"] = f"An unexpected error occurred: {e}"
    
    return results

def main():
    print("--- Starting Metrics Test ---")
    all_results = []

    # --- Audio Tests ---
    print("\nRunning Audio-to-Text & Translate Tests...")
    for name, path in AUDIO_TEST_FILES.items():
        print(f"Testing audio file: {name} ({path})...")
        result = run_audio_stt_and_translate_test(path, f"Audio_{name}", TEST_SOURCE_LANGUAGE, TEST_TARGET_LANGUAGE)
        all_results.append(result)
        logging.info(f"Audio Test Result for {name}: Latency={result['Total API Latency (s)']:.4f}s, Cost=${result['Total API Cost (USD)']:.6f}")
        logging.debug(f"STT: {result['STT Transcript']}")
        logging.debug(f"Translation: {result['Translated Text']}")
        print("-" * 30)

    # --- Text-to-Text Tests ---
    print("\nRunning Text-to-Text Translate Tests...")
    for name, text in TEXT_TEST_CASES.items():
        print(f"Testing text input: {name} (Length: {len(text)} chars)...")
        result = run_text_translate_test(text, f"Text_{name}", TEST_SOURCE_LANGUAGE, TEST_TARGET_LANGUAGE)
        all_results.append(result)
        logging.info(f"Text Test Result for {name}: Latency={result['Translate Latency (s)']:.4f}s, Cost=${result['Translate Cost (USD)']:.6f}")
        logging.debug(f"Original: {text}")
        logging.debug(f"Translation: {result['Translated Text']}")
        print("-" * 30)

    print("\n--- Test Summary ---")
    for result in all_results:
        print(f"\n{result['Test Name']}:")
        print(f"  Input Type: {result['Input Type']}")
        if result["Input Type"] == "Audio":
            print(f"  Audio Duration: {result['Audio Duration (s)']:.2f}s")
            print(f"  STT Latency: {result['STT Latency (s)']:.4f}s")
            print(f"  STT Cost: ${result['STT Cost (USD)']:.6f}")
            print(f"  STT Transcript: {result['STT Transcript'][:100]}...")
        
        print(f"  Translation Latency: {result['Translate Latency (s)']:.4f}s")
        print(f"  Translation Cost: ${result['Translate Cost (USD)']:.6f}")
        print(f"  Total API Latency: {result['Total API Latency (s)']:.4f}s")
        print(f"  Total API Cost: ${result['Total API Cost (USD)']:.6f}")
        print(f"  Translated Text: {result['Translated Text'][:100]}...")
        if result["Notes"]:
            print(f"  Notes: {result['Notes']}")
    
    print("\n--- Important Notes for your Demo Video ---")
    print("1. Accuracy Assessment:")
    print("   To calculate accuracy (e.g., Word Error Rate for ASR, BLEU score for NMT), you need a 'ground truth' dataset (human-verified transcripts and translations).")
    print("   Manually compare the 'STT Transcript' and 'Translated Text' outputs from the logs above with your ground truth data.")
    print("   Automated tools for WER/BLEU would require installing additional libraries and providing labeled datasets.")
    print("\n2. Cost Calculation in Rupees:")
    print(f"   The costs above are in USD, based on the dummy rates (STT: ${COST_PER_SECOND_STT_USD}/s, Translate: ${COST_PER_CHAR_TRANSLATE_USD}/char).")
    print("   To convert to Rupees, multiply by the current USD to INR exchange rate (e.g., 1 USD = 83 INR).")
    print("   Total cost for a demo scenario: Sum all 'Total API Cost (USD)' values and convert to INR.")
    print("\n3. Space & Time Complexity:")
    print("   These are theoretical measures, not runtime metrics displayed by the API or this script.")
    print("   - Time Complexity (API): For each API call, it's effectively O(1) from the client's perspective (a network request to a complex backend).")
    print("   - Time Complexity (Client-side): Audio buffering, string concatenation, and history management are highly efficient for typical inputs. String operations are optimized, and history is a fixed small size (O(1)).")
    print("   - Space Complexity (Client-side): Memory usage scales with audio chunk size, accumulated text, and history. Remains low.")
    print("   You can explain these concepts as part of your demo narration, referring to the efficient design.")
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    main()