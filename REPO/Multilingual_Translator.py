import gradio as gr
import numpy as np
import requests
import io
import base64
import tempfile
import os
from pydub import AudioSegment
from datetime import datetime
import logging
import time
import hashlib
import shutil

# Configure logging to see detailed API errors
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Sarvam API Key (replace with your actual key)
SARVAM_API_KEY = "sk_aov2qcwm_v6DDreRZzU6ntWRM5ixh8voS"

# API Endpoints
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

# Supported Languages
LANGUAGE_MAPPINGS = {
    "auto": "Auto-detect",
    "hi-IN": "Hindi",
    "bn-IN": "Bengali",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "gu-IN": "Gujarati",
    "pa-IN": "Punjabi",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "od-IN": "Odia",
    "en-IN": "English",
}

LANGUAGE_CHOICES = [(v, k) for k, v in LANGUAGE_MAPPINGS.items()]

# Output languages (excluding auto-detect for dropdown, English is allowed for TTS/Translate)
OUTPUT_LANGUAGE_CHOICES = [(v, k) for k, v in LANGUAGE_MAPPINGS.items() if k not in ["auto"]]

# Dummy Cost Model Parameters (for logging purposes)
COST_PER_SECOND_STT_USD = 0.00001
COST_PER_CHAR_TRANSLATE_USD = 0.000005
COST_PER_CHAR_TTS_USD = 0.000003

# Create a directory for serving audio files through Gradio
GRADIO_AUDIO_DIR = os.path.join(tempfile.gettempdir(), "gradio_audio_files")
os.makedirs(GRADIO_AUDIO_DIR, exist_ok=True)

# API Call Functions
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
        response = requests.post(SARVAM_STT_URL, headers=headers, files=files, data=data, timeout=15)
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
        response = requests.post(SARVAM_TRANSLATE_URL, headers=headers, json=data, timeout=15)
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

def call_tts_api(text: str, lang_code: str, api_key: str):
    if not text.strip():
        logging.warning("TTS: No text provided for synthesis.")
        return None, 0.0, 0.0

    # Use a hash of text+lang_code as the filename
    hash_input = (text + lang_code).encode('utf-8')
    tts_hash = hashlib.sha256(hash_input).hexdigest()
    cache_dir = os.path.join(tempfile.gettempdir(), "bhashasetu_tts_cache")
    os.makedirs(cache_dir, exist_ok=True)
    cached_path = os.path.join(cache_dir, f"tts_{tts_hash}.wav")

    # Create a path that Gradio can serve
    gradio_filename = f"tts_{tts_hash}.wav"
    gradio_path = os.path.join(GRADIO_AUDIO_DIR, gradio_filename)

    if os.path.exists(cached_path):
        logging.info(f"TTS: Using cached audio at {cached_path}")
        # Copy to Gradio directory if not already there
        if not os.path.exists(gradio_path):
            shutil.copy2(cached_path, gradio_path)
        return gradio_path, 0.0, 0.0

    start_time = time.time()
    try:
        headers = {"api-subscription-key": api_key, "Content-Type": "application/json"}
        data = {
            "text": text,
            "language_code": lang_code,
            "gender": "male",
            "sampling_rate": 22050
        }
        logging.info(f"TTS: Sending request to {SARVAM_TTS_URL} with data: {data}")
        response = requests.post(SARVAM_TTS_URL, headers=headers, json=data, timeout=15)
        logging.info(f"TTS: Response status code: {response.status_code}")
        end_time = time.time()
        latency = end_time - start_time

        try:
            response_json = response.json()
            logging.info(f"TTS: Response JSON: {response_json}")
        except Exception as e:
            logging.error(f"TTS: Failed to parse response JSON: {e}")
            response_json = {}

        audio_content_base64 = response_json.get("audio_content", "")
        # If not found, try 'audios' (list)
        if not audio_content_base64:
            audios = response_json.get("audios", [])
            if audios and isinstance(audios, list):
                audio_content_base64 = audios[0]  # Use the first audio if available

        if not audio_content_base64:
            logging.error("TTS API returned no audio content.")
            return None, 0.0, 0.0

        audio_bytes = base64.b64decode(audio_content_base64)

        # Save to both cache and Gradio directory
        with open(cached_path, "wb") as cache_file:
            cache_file.write(audio_bytes)
        with open(gradio_path, "wb") as gradio_file:
            gradio_file.write(audio_bytes)

        logging.info(f"TTS: Audio file saved at {gradio_path}")
        cost = len(text) * COST_PER_CHAR_TTS_USD
        return gradio_path, latency, cost

    except requests.exceptions.HTTPError as e:
        logging.error(f"TTS API HTTP Error: {e.response.status_code} {e.response.reason} - {e.response.text}")
        return None, 0.0, 0.0
    except requests.exceptions.RequestException as e:
        logging.error(f"TTS API Request Error: {e}")
        return None, 0.0, 0.0
    except Exception as e:
        logging.error(f"TTS API Unexpected Error: {e}")
        return None, 0.0, 0.0

# Function to handle playing TTS when speaker icon is clicked
def play_text_to_speech(text_to_speak, lang_code):
    logging.info(f"play_text_to_speech: Called with text='{text_to_speak[:30]}...' and lang_code='{lang_code}'")
    if not text_to_speak.strip():
        logging.warning("play_text_to_speech: No text to speak.")
        return None, "No text to speak."

    tts_audio_path, tts_latency, tts_cost = call_tts_api(text_to_speak, lang_code, SARVAM_API_KEY)

    if tts_audio_path:
        logging.info(f"TTS Playback - Latency: {tts_latency:.4f}s, Estimated Cost: ${tts_cost:.6f}, File: {tts_audio_path}")
        return tts_audio_path, "Playing audio..."
    else:
        logging.error("play_text_to_speech: Failed to generate audio.")
        return None, "Failed to generate audio."

# Real-time Streaming Function with Buffering
class AudioBuffer:
    def __init__(self, min_duration_sec=2.0, sample_rate=16000):
        self.min_duration_sec = min_duration_sec
        self.sample_rate = sample_rate
        self.buffer = []
        self.last_sent_time = None

    def add_chunk(self, chunk):
        self.buffer.append(chunk)

    def should_send(self):
        total_samples = sum([c[1].shape[0] for c in self.buffer])
        duration = total_samples / self.sample_rate
        return duration >= self.min_duration_sec

    def get_audio_segment(self):
        if not self.buffer:
            return None
        sr = self.buffer[0][0] # Sample rate from the first chunk
        y = np.concatenate([c[1] for c in self.buffer], axis=0)
        if y.dtype != np.int16:
            max_val = np.iinfo(np.int16).max
            y_int16 = (y / np.max(np.abs(y)) * max_val).astype(np.int16)
        else:
            y_int16 = y
        audio_segment = AudioSegment(y_int16.tobytes(), frame_rate=sr, sample_width=y_int16.dtype.itemsize, channels=1)
        return audio_segment

    def clear(self):
        self.buffer = []

audio_buffer_state = AudioBuffer()

def format_history_display(history_list):
    if not history_list:
        return "No translations yet. Start speaking or upload a file to see your history here."
    formatted_entries = []
    for entry in reversed(history_list[-10:]):
        formatted_entries.append(
            f"🕒 {entry['timestamp']}\n"
            f"🎤 {entry['source_lang']}: {entry['original']}\n"
            f"🔄 {entry['target_lang']}: {entry['translated']}\n"
            f"{'─' * 40}"
        )
    return "\n".join(formatted_entries)

def clear_all_outputs(original_markdown_comp, translated_markdown_comp):
    audio_buffer_state.clear()
    logging.info("Cleared all states.")
    # Reset all relevant components
    return [], "", "", None, None, "", "", "", \
           gr.update(value="Original Speech"), \
           gr.update(value="Translated Text"), \
           None, gr.update(value=""), \
           None, gr.update(value="")

def translate_full_text(text, source_lang_code, target_lang_code, history_state):
    """Translates the entire text at once from text input."""
    if not text.strip():
        logging.info("translate_full_text called with empty text.")
        return history_state, "", format_history_display(history_state), "", None, "", None, "" # Returns for both translated and original audio/status

    translated_text, translate_latency, translate_cost = call_translate_api(text, source_lang_code, target_lang_code, SARVAM_API_KEY)

    current_timestamp = datetime.now().strftime("%H:%M:%S")
    history_entry = {
        'timestamp': current_timestamp,
        'source_lang': LANGUAGE_MAPPINGS.get(source_lang_code, source_lang_code),
        'target_lang': LANGUAGE_MAPPINGS.get(target_lang_code, target_lang_code),
        'original': text,
        'translated': translated_text
    }
    history_state.append(history_entry)
    if len(history_state) > 10:
        history_state.pop(0)
    total_cost = translate_cost
    total_latency = translate_latency
    logging.info(f"TEXT INPUT - Latency: {total_latency:.4f}s, Estimated Cost: ${total_cost:.6f}")
    logging.debug(f"Original Text: '{text}'")
    logging.debug(f"Translated Text: '{translated_text}'")
    # For text input, no original audio
    return history_state, translated_text, format_history_display(history_state), text, \
           None, "", None, "" # Return None for TTS audio path and empty string for play status for both translated and original

def stream_transcribe_translate_tts(new_chunk, selected_input_lang_code, selected_output_lang_code, history_state, original_text_accum, translated_text_accum):
    """Processes microphone input in chunks and appends."""
    if original_text_accum is None:
        original_text_accum = ""
    if translated_text_accum is None:
        translated_text_accum = ""
    if new_chunk is not None:
        audio_buffer_state.add_chunk(new_chunk)
        if not audio_buffer_state.should_send():
            return gr.update(value=original_text_accum), gr.update(value=translated_text_accum), \
                    history_state, format_history_display(history_state), \
                    original_text_accum, translated_text_accum, \
                    None, "", None, "" # Both translated and original audio/status
        audio_segment = audio_buffer_state.get_audio_segment()
        audio_buffer_state.clear()
    else:
        return gr.update(value=original_text_accum), gr.update(value=translated_text_accum), \
                history_state, format_history_display(history_state), \
                original_text_accum, translated_text_accum, \
                None, "", None, "" # Both translated and original audio/status

    current_timestamp = datetime.now().strftime("%H:%M:%S")
    stt_latency, stt_cost = 0.0, 0.0
    translate_latency, translate_cost = 0.0, 0.0
    transcript = ""
    translated_chunk_text = ""
    final_source_lang = selected_input_lang_code
    try:
        # Step 1: STT
        transcript, detected_source_lang, stt_latency, stt_cost = call_stt_api(audio_segment, SARVAM_API_KEY, selected_input_lang_code)

        final_source_lang = detected_source_lang if selected_input_lang_code == "auto" else selected_input_lang_code
        if not transcript.strip():
            logging.warning("Microphone stream: No transcript obtained from audio chunk.")
            logging.info(f"MICROPHONE INPUT - STT Latency: {stt_latency:.4f}s, Estimated STT Cost: ${stt_cost:.6f}, Accuracy: (Requires Manual Check)%")
            return gr.update(value=original_text_accum), gr.update(value=translated_text_accum), \
                    history_state, format_history_display(history_state), \
                    original_text_accum, translated_text_accum, \
                    None, "", None, "" # Original and Translated audio/status

        # Step 2: Translate
        translated_chunk_text, translate_latency, translate_cost = call_translate_api(transcript, final_source_lang, selected_output_lang_code, SARVAM_API_KEY)

        total_api_latency = stt_latency + translate_latency
        total_api_cost = stt_cost + translate_cost
        word_count = len(transcript.split())
        new_original_text_for_display = (original_text_accum + " " + transcript).strip()
        new_translated_text_for_display = (translated_text_accum + " " + translated_chunk_text).strip()
        history_entry = {
            'timestamp': current_timestamp,
            'source_lang': LANGUAGE_MAPPINGS.get(final_source_lang, final_source_lang),
            'target_lang': LANGUAGE_MAPPINGS.get(selected_output_lang_code, selected_output_lang_code),
            'original': transcript,
            'translated': translated_chunk_text
        }
        history_state.append(history_entry)
        if len(history_state) > 10:
            history_state.pop(0)
        logging.info(f"MICROPHONE INPUT - Latency: {total_api_latency:.4f}s / {word_count} words, Estimated Cost: ${total_api_cost:.6f}, Accuracy: (Requires Manual Check)%")
        logging.debug(f"STT Transcript: '{transcript}'")
        logging.debug(f"Translated Text: '{translated_chunk_text}'")

        return gr.update(value=new_original_text_for_display), gr.update(value=new_translated_text_for_display), \
                history_state, format_history_display(history_state), \
                new_original_text_for_display, new_translated_text_for_display, \
                None, "", None, "" # Return None for TTS audio and empty string for play status for both translated and original
    except Exception as e:
        logging.error(f"Error during stream_transcribe_translate_tts: {e}", exc_info=True)
        logging.info(f"MICROPHONE INPUT - Error during processing: Latency: {stt_latency + translate_latency:.4f}s, Cost: ${stt_cost + translate_cost:.6f}, Accuracy: N/A")
        return gr.update(value=original_text_accum), gr.update(value=translated_text_accum), \
                history_state, format_history_display(history_state), \
                original_text_accum, translated_text_accum, \
                None, "", None, "" # Both translated and original audio/status

def process_uploaded_file(file_path, input_lang_code, output_lang_code, history_state):
    """Processes uploaded audio/video files in chunks and appends."""
    if file_path is None:
        logging.info("No file path provided for upload.")
        return history_state, "", "", format_history_display(history_state), None, "", None, ""

    total_stt_latency_file = 0.0
    total_translate_latency_file = 0.0
    total_file_cost = 0.0
    total_original_text_chunks = []
    total_translated_text_chunks = []
    total_word_count = 0
    CHUNK_LENGTH_MS = 29 * 1000
    try:
        logging.info(f"Processing uploaded file: {file_path}")
        full_audio = AudioSegment.from_file(file_path)
        logging.info(f"Full audio extracted. Duration: {len(full_audio) / 1000:.2f} seconds")
        for i in range(0, len(full_audio), CHUNK_LENGTH_MS):
            audio_chunk = full_audio[i : i + CHUNK_LENGTH_MS]
            if not audio_chunk:
                continue
            transcript, detected_source_lang, stt_latency, stt_cost = call_stt_api(audio_chunk, SARVAM_API_KEY, input_lang_code)
            total_stt_latency_file += stt_latency
            total_file_cost += stt_cost

            if not transcript.strip():
                logging.warning(f"File upload: No transcript obtained for chunk {i // CHUNK_LENGTH_MS + 1}.")
                total_original_text_chunks.append("")
                total_translated_text_chunks.append("")
            else:
                total_original_text_chunks.append(transcript)
                total_word_count += len(transcript.split())
                final_source_lang = detected_source_lang if input_lang_code == "auto" else input_lang_code
                translated_text, translate_latency, translate_cost = call_translate_api(transcript, final_source_lang, output_lang_code, SARVAM_API_KEY)
                total_translate_latency_file += translate_latency
                total_file_cost += translate_cost
                total_translated_text_chunks.append(translated_text)

        final_original_text = " ".join(total_original_text_chunks).strip()
        final_translated_text = " ".join(total_translated_text_chunks).strip()
        if final_original_text.strip() or final_translated_text.strip():
            current_timestamp = datetime.now().strftime("%H:%M:%S")
            history_entry = {
                'timestamp': current_timestamp,
                'source_lang': LANGUAGE_MAPPINGS.get(input_lang_code, input_lang_code) if input_lang_code != "auto" else LANGUAGE_MAPPINGS.get(detected_source_lang, detected_source_lang),
                'target_lang': LANGUAGE_MAPPINGS.get(output_lang_code, output_lang_code),
                'original': final_original_text,
                'translated': final_translated_text
            }
            history_state.append(history_entry)
            if len(history_state) > 10:
                history_state.pop(0)
        logging.info(f"FILE UPLOAD - Latency: {total_stt_latency_file + total_translate_latency_file:.4f}s / {total_word_count} words, Estimated Cost: ${total_file_cost:.6f}, Accuracy: (Requires Manual Check)%")
        logging.debug(f"Total STT Transcript: '{final_original_text[:200]}...'")
        logging.debug(f"Total Translated Text: '{final_translated_text[:200]}...'")
        return history_state, final_original_text, final_translated_text, format_history_display(history_state), \
               None, "", None, "" # Return None for TTS audio and empty string for play status for both translated and original
    except Exception as e:
        logging.error(f"Error processing uploaded file: {e}", exc_info=True)
        logging.info(f"FILE UPLOAD - Error during processing: Latency: {total_stt_latency_file + total_translate_latency_file:.4f}s, Cost: ${total_file_cost:.6f}, Accuracy: N/A")
        return history_state, "", f"Error processing file: {str(e)}", format_history_display(history_state), \
               None, "", None, ""

# UI Visibility and Dynamic Text Control Function
def update_input_visibility_and_text(choice):
    mic_visible = gr.update(visible=(choice == "Microphone"))
    upload_visible = gr.update(visible=(choice == "Upload File"))
    original_box_interactive = gr.update(interactive=(choice == "Text Input"))

    # Dynamic Markdown Headings
    original_markdown_text = "## Original Speech"
    translated_markdown_text = "## Translated Text"
    if choice == "Microphone":
        original_markdown_text = "## Audio Input"
        translated_markdown_text = "## Live Translation"
    elif choice == "Upload File":
        original_markdown_text = "## File Input"
        translated_markdown_text = "## File Translation"
    elif choice == "Text Input":
        original_markdown_text = "## Text Input"
        translated_markdown_text = "## Text Translation"
    return (
        mic_visible,
        upload_visible,
        original_box_interactive,
        gr.update(value=original_markdown_text), # Update original markdown
        gr.update(value=translated_markdown_text) # Update translated markdown
    )

# Gradio UI
with gr.Blocks(theme=gr.themes.Default(primary_hue="blue")) as demo:
    gr.HTML("""
<script>
console.log('Custom JS loaded!'); // Confirm script is loaded

function playOrStopAudio(audioUrl) {
    if (!audioUrl) {
        console.log('No audio URL provided');
        return;
    }
    if (!audioUrl.startsWith('http')) {
        audioUrl = window.location.origin + audioUrl;
    }
    console.log('Final audio URL for playback:', audioUrl);
    if (window.lastAudio && !window.lastAudio.paused && window.lastAudioUrl === audioUrl) {
        window.lastAudio.pause();
        window.lastAudio.currentTime = 0;
        return;
    }
    if (window.lastAudio) {
        window.lastAudio.pause();
        window.lastAudio.currentTime = 0;
    }
    window.lastAudio = new Audio(audioUrl);
    window.lastAudioUrl = audioUrl;
    window.lastAudio.play().catch(error => {
        console.error('Error playing audio:', error);
    });
}

function attachSpeakerHandlers() {
    const origBox = document.getElementById('orig-audio-url');
    const transBox = document.getElementById('trans-audio-url');
    const speakerButtons = document.querySelectorAll('.speaker-button-inside');
    if (!speakerButtons.length) {
        console.log('No speaker buttons found');
        return;
    }
    speakerButtons.forEach((btn, idx) => {
        // Remove previous event listeners by cloning
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        newBtn.addEventListener('click', function() {
            if (idx === 0 && origBox) {
                console.log('Original speaker button clicked');
                playOrStopAudio(origBox.value);
            } else if (idx === 1 && transBox) {
                console.log('Translated speaker button clicked');
                playOrStopAudio(transBox.value);
            } else {
                console.log('Speaker button clicked but no audio box found');
            }
        });
    });
}

// Initial attach
window.addEventListener('DOMContentLoaded', attachSpeakerHandlers);

// Use MutationObserver to re-attach after DOM changes
const observer = new MutationObserver((mutationsList, observer) => {
    for (const mutation of mutationsList) {
        if (mutation.type === 'childList' || mutation.type === 'subtree') {
            attachSpeakerHandlers();
            break;
        }
    }
});
observer.observe(document.body, { childList: true, subtree: true });
</script>

    """)

    # Custom CSS
    gr.HTML("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        html, body { margin: 0 !important; padding: 0 !important; height: 100vh !important; width: 100%; font-family: 'Poppins', Arial, sans-serif !important; overflow: hidden !important; }
        .gradio-container { height: calc(100vh - 35px) !important; display: flex !important; flex-direction: column !important; background: #fff !important; color: #111 !important; padding: 0 !important; }
        .gradio-app, .gradio-interface, .gradio-container > div:first-child { padding: 0 !important; margin: 0 !important; flex: 1 !important; display: flex !important; flex-direction: column !important; min-height: 0 !important; overflow: hidden !important; }
        .gradio-container > div:first-child > div[class*="svelte-"]:first-child { padding: 0 !important; margin: 0 !important; }
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 27px;
            border-bottom: 1px solid #e0e0e0;
            background: #fff;
            height: 75px;
            flex-shrink: 0;
        }
        .main-title-wrapper {
            flex-grow: 1;
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
        }
        .main-title {
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
            margin: 0;
            white-space: nowrap;
        }
        .header-logo {
            max-height: 70px;
            width: auto;
            object-fit: contain;
            margin-left: 10px;
        }
        .right-header-item {
            display: flex;
            align-items: center;
        }

        .main-content-wrapper { flex: 1; display: flex; flex-direction: column; padding: 10px; gap: 10px; overflow-y: auto; overflow-x: hidden; min-height: 0; }
        .main-content-wrapper::-webkit-scrollbar { width: 8px; }
        .main-content-wrapper::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
        .main-content-wrapper::-webkit-scrollbar-thumb { background: #888; border-radius: 10px; }
        .main-content-wrapper::-webkit-scrollbar-thumb:hover { background: #555; }
        footer.svelte-czcr5b, a.built-with, div.divider.show-api-divider { display: none !important; visibility: hidden !important; height: 0 !important; overflow: hidden !important; margin: 0 !important; padding: 0 !important; }
        .footer-container { position: fixed; bottom: 0; left: 0; width: 100%; display: flex; justify-content: center; align-items: center; padding: 6px 20px; border-top: 1px solid #e0e0e0; background: #f8f9fa; height: 35px; box-sizing: border-box; z-index: 1000; }
        .footer-left { display: flex; align-items: center; gap: 5px; }
        .powered-by-text { font-size: 12px; color: #666; font-weight: 500; margin: 0; }
        .footer-logo { max-height: 20px; width: auto; object-fit: contain; vertical-align: middle; }

        /* Dark theme styles */
        body.dark-theme, html.dark-theme { background-color: #2c3e50 !important; color: #ecf0f1 !important; }
        body.dark-theme .header-container, body.dark-theme .footer-container { background-color: #34495e !important; border-color: #4a5568 !important; }
        body.dark-theme .main-title { color: #ecf0f1 !important; }
        body.dark-theme .powered-by-text { color: #bdc3c7 !important; }
        body.dark-theme .main-content-wrapper::-webkit-scrollbar-track { background: #444; }
        body.dark-theme .main-content-wrapper::-webkit-scrollbar-thumb { background: #666; }
        body.dark-theme .main-content-wrapper::-webkit-scrollbar-thumb:hover { background: #777; }
        .main-content-wrapper > .gr-row { flex: 1 !important; height: 100% !important; align-items: stretch !important; gap: 10px !important; min-height: 0 !important; }
        .main-content-wrapper > .gr-row > .gr-column { display: flex !important; flex-direction: column !important; height: 100% !important; padding: 0 !important; gap: 10px !important; min-height: 0 !important; }
        .gr-column .gr-box.scrollable-box { flex: 1; min-height: 0; overflow: auto; }
        .scrollable-box textarea, .equal-box textarea { height: 100%; min-height: 50px; overflow-y: auto; font-size: 1.1em; resize: none; box-sizing: border-box; border: 1.5px solid #000; }
        #history_box { flex: 0.5; min-height: 0; overflow: auto; }
        .gradio-audio, .gradio-dropdown, .gradio-button, .gradio-radio, .gradio-file { margin-bottom: 0.5em !important; margin-top: 0.5em !important; }
        .gradio-audio { width: 100% !important; }
        /* Custom styles for textbox with inline speaker button */
        .textbox-with-speaker {
            display: flex !important;
            align-items: stretch !important;
            gap: 5px !important;
            height: 100% !important;
        }

        .speaker-button-inside {
            background: #f0f0f0 !important;
            border: 1.5px solid #000 !important;
            border-left: none !important;
            padding: 8px !important;
            cursor: pointer !important;
            font-size: 1.2em !important;
            line-height: 1 !important;
            color: #4CAF50 !important;
            min-width: 40px !important;
            max-width: 40px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 0 8px 8px 0 !important;
        }
        .speaker-button-inside:hover {
            background: #e0e0e0 !important;
            color: #388E3C !important;
        }

        /* Adjust the textbox to work with inline button */
        .textbox-with-speaker .gr-textbox {
            border-radius: 8px 0 0 8px !important;
        }
        /* Hide the default audio player */
        .tts-audio-player { display: none !important; }
        /* Remove Gradio's default top padding/margin */
        div.html-container, .svelte-phx28p, .svelte-phx28p.padding {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        body, html {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        /* Remove all top margin/padding from Gradio and its parents */
        body, html {
            margin: 0 !important;
            padding: 0 !important;
            height: 100% !important;
        }
        .gradio-container, .gradio-container.gradio-container {
            margin: 0 !important;
            padding: 0 !important;
            height: 100vh !important;
            box-sizing: border-box !important;
        }
        main.svelte-1t6rnd3, .main-content-wrapper {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        .fillable.svelte-1t6rnd3.app {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        body, html, .gradio-container {
            background: #fff !important;
        }
        /* Hide Gradio's processing spinner and status text */
        .svelte-1ipelgc, .svelte-1ipelgc * {
            display: none !important;
        }
        .status.svelte-1ipelgc {
            display: none !important;
        }
    </style>
    <div class="header-container">
        <div></div>
        <div class="main-title-wrapper">
            <h1 class="main-title">BhashaSetu – Real-Time Language Tech for Bharat</h1>
        </div>
        <div class="right-header-item">
            <img src="https://wikiwandv2-19431.kxcdn.com/_next/image?url=https:%2F%2Fupload.wikimedia.org%2Fwikipedia%2Fcommons%2Fthumb%2Fc%2Fcb%2FMinistry_of_Information_and_Broadcasting.svg%2F1500px-Ministry_of_Information_and_Broadcasting.svg.png&w=828&q=50" alt="Ministry of Information and Broadcasting Logo" class="header-logo">
        </div>
    </div>
    """)

    # Define UI components
    with gr.Column(elem_classes=["main-content-wrapper"]):
        with gr.Row():
            with gr.Column(scale=2):
                # Original Speech Section
                original_markdown = gr.Markdown("## Original Speech", label=None, elem_id="original_markdown") # Dynamic Markdown Heading
                with gr.Row(elem_classes=["textbox-with-speaker"]):
                    original_box = gr.Textbox(label="Original Speech", lines=10, interactive=False, elem_id="original_box", elem_classes=["scrollable-box", "equal-box"], scale=9)
                    original_speaker_button = gr.Button("🔊", elem_classes=["speaker-button-inside"], interactive=True, scale=1, size="sm")
                # Hidden textbox for audio URL (used by JS)
                original_audio_url = gr.Textbox(visible=False, elem_id="orig-audio-url")
                original_play_status_text = gr.Textbox(label="Original Audio Playback Status", interactive=False, visible=False)

            with gr.Column(scale=3):
                input_source_choice = gr.Radio(
                    ["Microphone", "Upload File", "Text Input"],
                    label="Select Input Source",
                    value="Microphone",
                    interactive=True
                )
                microphone_input_group = gr.Group(visible=True)
                with microphone_input_group:
                    input_audio = gr.Audio(
                        sources=["microphone"],
                        type="numpy",
                        label="🎙️ Speak Now",
                        streaming=True,
                    )
                file_upload_group = gr.Group(visible=False)
                with file_upload_group:
                    file_upload_component = gr.File(
                        label="Upload Audio/Video File",
                        file_types=[".mp3", ".wav", ".mp4", ".avi", ".mov", ".flv", ".webm", ".mkv"],
                        file_count="single"
                    )

                with gr.Row():
                    input_lang = gr.Dropdown(
                        choices=LANGUAGE_CHOICES,
                        value="en-IN",
                        label="🎯 Input Language",
                    )
                    output_lang = gr.Dropdown(
                        choices=OUTPUT_LANGUAGE_CHOICES,
                        value="te-IN",
                        label="🌐 Output Language",
                    )
                with gr.Row():
                    clear_btn = gr.Button("🗑️ Clear All")
                history_box = gr.Textbox(label="History", lines=10, interactive=False, elem_id="history_box", elem_classes=["scrollable-box", "equal-box"])

            with gr.Column(scale=2):
                # Translated Speech Section
                translated_markdown = gr.Markdown("## Translated Text", label=None, elem_id="translated_markdown") # Dynamic Markdown Heading
                with gr.Row(elem_classes=["textbox-with-speaker"]):
                    translated_box = gr.Textbox(label="Translated Speech", lines=10, interactive=False, elem_id="translated_box", elem_classes=["scrollable-box", "equal-box"], scale=9)
                    translated_speaker_button = gr.Button("🔊", elem_classes=["speaker-button-inside"], interactive=True, scale=1, size="sm")
                # Hidden textbox for audio URL (used by JS)
                translated_audio_url = gr.Textbox(visible=False, elem_id="trans-audio-url")
                translated_play_status_text = gr.Textbox(label="Translated Audio Playback Status", interactive=False, visible=False)

    # Custom HTML for footer
    gr.HTML(f"""
    <div class="footer-container">
        <div class="footer-left">
            <span class="powered-by-text">Powered by</span>
            <img src="https://anandr07.github.io/assets/img/innodatatics_logo.png" alt="InnoDatatics Logo" class="footer-logo">
        </div>
    </div>
    """)

    # Gradio State variables
    history_state = gr.State(value=[])
    original_text_state = gr.State("") # Accumulated for streaming/file upload
    translated_text_state = gr.State("") # Accumulated for streaming/file upload

    # Gradio Event Listeners
    input_source_choice.change(
        fn=update_input_visibility_and_text,
        inputs=input_source_choice,
        outputs=[microphone_input_group, file_upload_group, original_box, original_markdown, translated_markdown]
    )

    original_box.change(
        fn=translate_full_text,
        inputs=[original_box, input_lang, output_lang, history_state],
        outputs=[history_state, translated_box, history_box, original_box, translated_audio_url, translated_play_status_text, original_audio_url, original_play_status_text]
    ).then(
        fn=lambda x: x,
        inputs=[original_box],
        outputs=[original_text_state]
    )

    output_lang.change(
        fn=translate_full_text,
        inputs=[original_text_state, input_lang, output_lang, history_state],
        outputs=[history_state, translated_box, history_box, original_box, translated_audio_url, translated_play_status_text, original_audio_url, original_play_status_text]
    )

    input_audio.stream(
        fn=stream_transcribe_translate_tts,
        inputs=[input_audio, input_lang, output_lang, history_state, original_text_state, translated_text_state],
        outputs=[original_box, translated_box, history_state, history_box, original_text_state, translated_text_state, translated_audio_url, translated_play_status_text, original_audio_url, original_play_status_text],
        show_progress='hidden',
        queue=True
    )

    file_upload_component.upload(
        fn=process_uploaded_file,
        inputs=[file_upload_component, input_lang, output_lang, history_state],
        outputs=[history_state, original_box, translated_box, history_box, translated_audio_url, translated_play_status_text, original_audio_url, original_play_status_text]
    ).then(
        fn=lambda x: x,
        inputs=[original_box],
        outputs=[original_text_state]
    )

    clear_btn.click(
        fn=clear_all_outputs,
        inputs=[original_markdown, translated_markdown], # Both markdown components are inputs to reset their text
        outputs=[history_state, original_box, translated_box, input_audio, file_upload_component, original_text_state, translated_text_state, history_box, original_markdown, translated_markdown, translated_audio_url, translated_play_status_text, original_audio_url, original_play_status_text]
    )

    # Event listener for the Original Speech speaker button
    def get_audio_url_and_status(text, lang):
        path, status = play_text_to_speech(text, lang)
        import os
        if path and os.path.exists(path):
            url = f"/file={os.path.basename(path)}"
            return url, status
        return "", status

    original_speaker_button.click(
        fn=get_audio_url_and_status,
        inputs=[original_box, input_lang],
        outputs=[original_audio_url, original_play_status_text]
    )

    # Event listener for the Translated Speech speaker button
    translated_speaker_button.click(
        fn=get_audio_url_and_status,
        inputs=[translated_box, output_lang],
        outputs=[translated_audio_url, translated_play_status_text]
    )

if __name__ == "__main__":
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7000,
        debug=True,
        show_api=False,
    )