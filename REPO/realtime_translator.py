import gradio as gr
import numpy as np
import requests
import io
import base64
import tempfile
from pydub import AudioSegment
from datetime import datetime

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

# --- API Call Functions ---
def call_stt_api(audio_segment: AudioSegment, api_key: str, lang_code: str = "auto"):
    wav_io = io.BytesIO()
    audio_segment.export(wav_io, format="wav")
    wav_io.seek(0)
    files = {"file": ("audio.wav", wav_io.getvalue(), "audio/wav")}
    headers = {"api-subscription-key": api_key}
    data = {"language_code": lang_code if lang_code != "auto" else ""}
    try:
        response = requests.post(SARVAM_STT_URL, headers=headers, files=files, data=data, timeout=7)
        response.raise_for_status()
        response_data = response.json()
        transcript = response_data.get("transcript", "").strip()
        detected_language = response_data.get("language_code", lang_code)
        return transcript, detected_language
    except Exception:
        return "", lang_code

def call_translate_api(text: str, source_lang_code: str, target_lang_code: str, api_key: str):
    if not text.strip():
        return ""
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
        response = requests.post(SARVAM_TRANSLATE_URL, headers=headers, json=data, timeout=7)
        response.raise_for_status()
        result = response.json()
        return result.get("translated_text", "Translation failed").strip()
    except Exception as e:
        return f"Translation Error: {str(e)}"

def call_tts_api(text: str, target_lang_code: str, api_key: str):
    if not text.strip():
        return None
    try:
        headers = {"api-subscription-key": api_key, "Content-Type": "application/json"}
        data = {
            "inputs": [text],
            "target_language_code": target_lang_code,
            "speaker": "meera",
            "pitch": 0,
            "pace": 1.65,
            "loudness": 1.5,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v1"
        }
        response = requests.post(SARVAM_TTS_URL, headers=headers, json=data, timeout=7)
        response.raise_for_status()
        result = response.json()
        audio_base64 = result.get("audios", [None])[0]
        if audio_base64:
            audio_bytes = base64.b64decode(audio_base64)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes)
                return tmp_file.name
        return None
    except Exception:
        return None

# --- Real-time Streaming Function with Buffering ---
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
        sr = self.buffer[0][0]
        y = np.concatenate([c[1] for c in self.buffer], axis=0)
        y_int16 = y.astype(np.int16)
        audio_segment = AudioSegment(y_int16.tobytes(), frame_rate=sr, sample_width=y_int16.dtype.itemsize, channels=1)
        return audio_segment

    def clear(self):
        self.buffer = []

# --- Gradio State for Buffer ---
audio_buffer_state = AudioBuffer()

def format_history_display(history_list):
    if not history_list:
        return "No translations yet. Start speaking to see your history here."
    formatted_entries = []
    for entry in history_list[-5:]:
        formatted_entries.append(
            f"🕒 {entry['timestamp']}\n"
            f"🎤 {entry['source_lang']}: {entry['original']}\n"
            f"🔄 {entry['target_lang']}: {entry['translated']}\n"
            f"{'─' * 40}"
        )
    return "\n".join(formatted_entries)

def clear_all():
    audio_buffer_state.clear()
    return [], "", "", None, "", ""

# --- Gradio UI ---
with gr.Blocks(theme=gr.themes.Default(primary_hue="blue")) as demo:
    gr.Markdown("""
    # 🇮🇳 Real-Time Any-to-Any Multilingual Speech Translator
    <div style='margin-bottom: 0; padding-bottom: 0;'>Speak in any supported language, get instant translation and voice in your chosen language!</div>
    """, elem_id="main-title")
    # Custom CSS for scrollable textboxes and speaker icon, and layout fixes
    gr.HTML('''
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
    html, body, #root, .gradio-container, .main {
        font-family: 'Poppins', Arial, sans-serif !important;
        overflow-x: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        background: #fff !important;
        color: #111 !important;
    }
    .gr-block, .gr-box, .gradio-container, .gr-row, .gr-column, .gradio-app, .gradio-interface, .gradio-main {
        font-family: 'Poppins', Arial, sans-serif !important;
    }
    .scrollable-box textarea, .equal-box textarea {
        min-height: 28vh !important;
        max-height: 32vh !important;
        height: 30vh !important;
        width: 100% !important;
        overflow-y: auto !important;
        font-size: 1.1em;
        resize: none !important;
        box-sizing: border-box;
        margin-bottom: 0 !important;
        border: 1.5px solid #000 !important;
        background: #fff !important;
        color: #111 !important;
    }
    .equal-box {
        width: 100% !important;
        margin-bottom: 0 !important;
    }
    .gradio-container .gr-box, .gradio-container .gr-block, .gradio-container .gr-row, .gradio-container .gr-column {
        border-color: #000 !important;
    }
    .gradio-container .gr-button, .gradio-container .gr-dropdown, .gradio-container .gr-textbox, .gradio-container .gr-audio {
        font-family: 'Poppins', Arial, sans-serif !important;
        border: 1.5px solid #000 !important;
        color: #111 !important;
        background: #fff !important;
    }
    .speaker-btn {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 1.5em;
        margin-left: 0.5em;
        vertical-align: middle;
        padding: 0;
    }
    .speaker-btn:active {
        color: #3b82f6;
    }
    #orig-label, #trans-label {
        margin-bottom: 0.2em !important;
        margin-top: 0.2em !important;
        display: flex;
        align-items: center;
        font-weight: bold;
        font-size: 1.08em;
    }
    #original_box, #translated_box {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    /* Responsive layout for all main columns */
    @media (max-width: 1200px) {
        .gradio-container .gr-row, .gradio-container .gr-block {
            flex-direction: column !important;
        }
        .gradio-container .gr-column {
            width: 100% !important;
            min-width: 0 !important;
        }
        .scrollable-box textarea, .equal-box textarea {
            min-height: 22vh !important;
            max-height: 28vh !important;
            height: 24vh !important;
        }
    }
    @media (max-width: 900px) {
        .scrollable-box textarea, .equal-box textarea {
            min-height: 18vh !important;
            max-height: 22vh !important;
            height: 18vh !important;
        }
    }
    @media (max-width: 700px) {
        .scrollable-box textarea, .equal-box textarea {
            min-height: 14vh !important;
            max-height: 18vh !important;
            height: 14vh !important;
        }
        .gradio-container .gr-row, .gradio-container .gr-block {
            flex-direction: column !important;
        }
    }
    ::-webkit-scrollbar {
        width: 0 !important;
        background: transparent !important;
    }
    .scrollable-box textarea::-webkit-scrollbar {
        width: 8px !important;
        background: #eee !important;
    }
    .scrollable-box textarea {
        scrollbar-width: thin;
        scrollbar-color: #bbb #eee;
    }
    /* Always show footer at the bottom */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100vw;
        background: #fff;
        color: #111;
        border-top: 1.5px solid #000;
        text-align: center;
        font-size: 1em;
        font-family: 'Poppins', Arial, sans-serif !important;
        z-index: 1000;
        padding: 0.5em 0;
    }
    </style>
    ''')
    # Inject browser TTS script with manual and auto playback
    gr.HTML('''
    <script>
    let lastSpoken = "";
    let autoLang = 'en-IN';
    function speakText(newText, lang) {
        if (!window.speechSynthesis) return;
        if (newText && newText.length > 0) {
            let utter = new window.SpeechSynthesisUtterance(newText);
            if (lang) utter.lang = lang;
            window.speechSynthesis.speak(utter);
        }
    }
    // Observe the translated textbox for changes (auto-speak)
    function observeTranslatedBox() {
        const box = document.querySelector('textarea[aria-label="Translated Text"]');
        if (!box) { setTimeout(observeTranslatedBox, 500); return; }
        let prev = box.value;
        setInterval(() => {
            if (box.value !== prev) {
                // Get language code from dropdown
                let langSel = document.querySelector('select[aria-label="Output Language"]');
                let lang = langSel ? langSel.value : 'en-IN';
                autoLang = lang;
                let toSpeak = box.value.replace(lastSpoken, "").trim();
                if (toSpeak.length > 0) {
                    speakText(toSpeak, lang);
                }
                lastSpoken = box.value;
                prev = box.value;
            }
        }, 700);
    }
    // Manual speaker buttons
    function setupSpeakerButtons() {
        // Original
        let origBtn = document.getElementById('speak-original');
        let origBox = document.querySelector('textarea[aria-label="Original Speech"]');
        if (origBtn && origBox) {
            origBtn.onclick = () => {
                // Try to get input language
                let langSel = document.querySelector('select[aria-label="Input Language"]');
                let lang = langSel ? langSel.value : 'en-IN';
                speakText(origBox.value, lang);
            };
        }
        // Translated
        let transBtn = document.getElementById('speak-translated');
        let transBox = document.querySelector('textarea[aria-label="Translated Text"]');
        if (transBtn && transBox) {
            transBtn.onclick = () => {
                speakText(transBox.value, autoLang);
            };
        }
    }
    window.addEventListener('DOMContentLoaded', () => {
        observeTranslatedBox();
        setTimeout(setupSpeakerButtons, 1000);
    });
    </script>
    ''')
    # Remove the persistent footer (delete any gr.HTML with class="footer")
    # Restore previous layout: controls in center top, Original Speech left, Translated Text right, History below controls
    with gr.Row():
        with gr.Column(scale=2):
            with gr.Row():
                gr.Markdown("<span id='orig-label'>Original Speech <button id=\"speak-original\" class=\"speaker-btn\" title=\"Speak Original\">🔊</button></span>", elem_id="orig-label")
            original_box = gr.Textbox(label="Original Speech", lines=10, interactive=False, elem_id="original_box", elem_classes=["scrollable-box", "equal-box"])
        with gr.Column(scale=3):
            with gr.Row():
                input_audio = gr.Audio(
                    sources=["microphone"],
                    type="numpy",
                    label="🎙️ Speak Now",
                    streaming=True,
                )
            with gr.Row():
                input_lang = gr.Dropdown(
                    choices=LANGUAGE_CHOICES,
                    value="auto",
                    label="🎯 Input Language",
                )
                output_lang = gr.Dropdown(
                    choices=LANGUAGE_CHOICES[1:],  # exclude auto-detect for output
                    value="te-IN",
                    label="🌐 Output Language",
                )
            with gr.Row():
                clear_btn = gr.Button("🗑️ Clear All")
            # History block below controls
            history_box = gr.Textbox(label="History", lines=16, interactive=False, elem_id="history_box", elem_classes=["scrollable-box", "equal-box"])
        with gr.Column(scale=2):
            with gr.Row():
                gr.Markdown("<span id='trans-label'>Translated Text <button id=\"speak-translated\" class=\"speaker-btn\" title=\"Speak Translation\">🔊</button></span>", elem_id="trans-label")
            translated_box = gr.Textbox(label="Translated Text", lines=10, interactive=False, elem_id="translated_box", elem_classes=["scrollable-box", "equal-box"])
    # Update CSS for this layout
    gr.HTML('''
    <style>
    html, body, #root, .gradio-container, .main {
        height: 100vh !important;
        min-height: 100vh !important;
        font-family: 'Poppins', Arial, sans-serif !important;
        background: #fff !important;
        color: #111 !important;
    }
    .gradio-container > .gr-block > .gr-row {
        height: 70vh !important;
        align-items: stretch !important;
    }
    .gr-block > .gr-row > .gr-column {
        height: 100% !important;
        display: flex;
        flex-direction: column;
        justify-content: stretch;
    }
    #original_box, #translated_box {
        flex: 1 1 auto !important;
        height: 100% !important;
        min-height: 0 !important;
        max-height: none !important;
        margin-bottom: 0 !important;
    }
    .scrollable-box textarea, .equal-box textarea {
        height: 100% !important;
        min-height: 0 !important;
        max-height: none !important;
        width: 100% !important;
        overflow-y: auto !important;
        font-size: 1.1em;
        resize: none !important;
        box-sizing: border-box;
        margin-bottom: 0 !important;
        border: 1.5px solid #000 !important;
        background: #fff !important;
        color: #111 !important;
    }
    #history_box {
        margin-top: 1em;
    }
    @media (max-width: 1200px) {
        .gradio-container > .gr-block > .gr-row {
            height: auto !important;
        }
        .scrollable-box textarea, .equal-box textarea {
            min-height: 18vh !important;
            max-height: 28vh !important;
            height: 18vh !important;
        }
    }
    </style>
    ''')
    history_state = gr.State(value=[])
    original_text_state = gr.State("")
    translated_text_state = gr.State("")

    # --- Maintain continuous transcript ---
    def stream_transcribe_translate_tts(new_chunk, selected_input_lang_code, selected_output_lang_code, history_state, original_text_accum, translated_text_accum):
        # Ensure accumulators are always strings
        if original_text_accum is None:
            original_text_accum = ""
        if translated_text_accum is None:
            translated_text_accum = ""
        current_status = ""
        if new_chunk is not None:
            audio_buffer_state.add_chunk(new_chunk)
            if not audio_buffer_state.should_send():
                yield history_state, original_text_accum, translated_text_accum, format_history_display(history_state), original_text_accum, translated_text_accum
                return
            audio_segment = audio_buffer_state.get_audio_segment()
            audio_buffer_state.clear()
        else:
            yield history_state, original_text_accum, translated_text_accum, format_history_display(history_state), original_text_accum, translated_text_accum
            return
        current_timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            transcript, detected_source_lang = call_stt_api(audio_segment, SARVAM_API_KEY, selected_input_lang_code)
            if not transcript.strip():
                yield history_state, original_text_accum, translated_text_accum, format_history_display(history_state), original_text_accum, translated_text_accum
                return
            final_source_lang = detected_source_lang if selected_input_lang_code == "auto" else selected_input_lang_code
            # Append to accumulators
            original_text_accum = (original_text_accum + " " + transcript).strip()
            translated_text = call_translate_api(transcript, final_source_lang, selected_output_lang_code, SARVAM_API_KEY)
            translated_text_accum = (translated_text_accum + " " + translated_text).strip()
            history_entry = {
                'timestamp': current_timestamp,
                'source_lang': LANGUAGE_MAPPINGS.get(final_source_lang, final_source_lang),
                'target_lang': LANGUAGE_MAPPINGS.get(selected_output_lang_code, selected_output_lang_code),
                'original': transcript,
                'translated': translated_text
            }
            history_state.append(history_entry)
            if len(history_state) > 10:
                history_state.pop(0)
            yield history_state, original_text_accum, translated_text_accum, format_history_display(history_state), original_text_accum, translated_text_accum
        except Exception as e:
            yield history_state, original_text_accum, translated_text_accum, format_history_display(history_state), original_text_accum, translated_text_accum

    # --- Gradio State for accumulators ---
    original_text_state = gr.State("")
    translated_text_state = gr.State("")

    # --- Update Gradio stream and clear logic ---
    input_audio.stream(
        fn=stream_transcribe_translate_tts,
        inputs=[input_audio, input_lang, output_lang, history_state, original_text_state, translated_text_state],
        outputs=[history_state, original_box, translated_box, history_box, original_text_state, translated_text_state],
        show_progress='hidden',
        queue=True
    )
    clear_btn.click(
        fn=lambda: ([], "", "", "", "", ""),
        outputs=[history_state, original_box, translated_box, history_box, original_text_state, translated_text_state]
    )

if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7861, debug=True) 