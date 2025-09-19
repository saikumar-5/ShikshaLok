import gradio as gr
import time
import numpy as np
import os
import requests
import base64
import io
from pydub import AudioSegment
import tempfile # Needed for TTS audio files
from datetime import datetime # Needed for timestamps
import warnings
warnings.filterwarnings('ignore') # Suppress warnings

# Replace 'your_api_key_here' with your actual Sarvam AI API key
SARVAM_API_KEY = "sk_aov2qcwm_v6DDreRZzU6ntWRM5ixh8voS"

# Define API endpoints
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text" # Pure STT
SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate" # Text-to-Text Translate
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech" # Text-to-Speech

# Language mappings for display and API calls
LANGUAGE_MAPPINGS = {
    "hi-IN": {"name": "Hindi", "flag": "🇮🇳"},
    "bn-IN": {"name": "Bengali", "flag": "🇧🇩"},
    "ta-IN": {"name": "Tamil", "flag": "🇮🇳"},
    "te-IN": {"name": "Telugu", "flag": "🇮🇳"},
    "gu-IN": {"name": "Gujarati", "flag": "🇮🇳"},
    "pa-IN": {"name": "Punjabi", "flag": "🇮🇳"},
    "kn-IN": {"name": "Kannada", "flag": "🇮🇳"},
    "ml-IN": {"name": "Malayalam", "flag": "🇮🇳"},
    "mr-IN": {"name": "Marathi", "flag": "🇮🇳"},
    "od-IN": {"name": "Odia", "flag": "🇮🇳"},
    "en-IN": {"name": "English", "flag": "🇺🇸"},
    "unknown": {"name": "Unknown", "flag": "❓"} # For initial dropdown value
}

def call_stt_api(audio_segment: AudioSegment, api_key: str):
    """
    Calls Sarvam AI Speech-to-Text API to get transcript and detected language.
    Does NOT translate.
    """
    if AudioSegment is None:
        raise RuntimeError("pydub.AudioSegment is required but not imported. Please install pydub and ffmpeg.")

    wav_io = io.BytesIO()
    audio_segment.export(wav_io, format="wav")
    wav_io.seek(0)

    files = {"file": ("audio.wav", wav_io.getvalue(), "audio/wav")}
    headers = {"api-subscription-key": api_key}
    
    # Try multiple languages for detection for better accuracy
    # Sarvam STT can often auto-detect, but providing a list helps.
    # The first successful transcription with meaningful text is returned.
    detection_languages = ["en-IN", "hi-IN", "bn-IN", "ta-IN", "te-IN", "ml-IN", "mr-IN", "gu-IN", "pa-IN", "kn-IN", "od-IN"]
    
    for lang_code_attempt in detection_languages:
        try:
            data = {"language_code": lang_code_attempt}
            response = requests.post(SARVAM_STT_URL, headers=headers, files=files, data=data, timeout=7)
            response.raise_for_status() 
            response_data = response.json()
            transcript = response_data.get("transcript", "").strip()
            detected_language = response_data.get("language_code", lang_code_attempt)
            
            if transcript: # If we get any transcript, assume detection was successful
                return transcript, detected_language
        except requests.exceptions.RequestException as e:
            # print(f"STT attempt for {lang_code_attempt} failed: {e}") # Debugging
            continue # Try next language
        except Exception as e:
            # print(f"STT attempt for {lang_code_attempt} failed (general error): {e}") # Debugging
            continue

    return "", "en-IN" # Default if no detection or transcription is successful

def call_translate_api(text: str, source_lang_code: str, target_lang_code: str, api_key: str):
    """
    Calls Sarvam AI Text-to-Text Translation API.
    Supports any-to-any (English, Indic-to-Indic).
    """
    if not text.strip():
        return ""
    try:
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "input": text,
            "source_language_code": source_lang_code,
            "target_language_code": target_lang_code,
            "speaker_gender": "Male", # This param is for TTS after translation, but often included
            "mode": "formal",
            "model": "mayura:v1", # Or other translation models if specified
            "enable_preprocessing": True
        }
        response = requests.post(SARVAM_TRANSLATE_URL, headers=headers, json=data, timeout=7)
        response.raise_for_status()
        result = response.json()
        return result.get("translated_text", "Translation failed").strip()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [401, 403]:
            return f"API Error: Invalid API Key or Unauthorized for MT."
        return f"Translation API Error: {e.response.status_code} - {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Translation Network Error: {str(e)}"
    except Exception as e:
        return f"Translation Error: {str(e)}"

def call_tts_api(text: str, target_lang_code: str, api_key: str):
    """
    Calls Sarvam AI Text-to-Speech API.
    """
    if not text.strip():
        return None
    try:
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "inputs": [text],
            "target_language_code": target_lang_code,
            "speaker": "meera", # Default speaker for many Indic languages in Sarvam
            "pitch": 0,
            "pace": 1.65,
            "loudness": 1.5,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v1" # Default TTS model for many Indic languages
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
    except requests.exceptions.RequestException as e:
        # print(f"TTS API/Network Error: {e}") # For debugging
        return None
    except Exception as e:
        # print(f"TTS General Error: {e}") # For debugging
        return None

def stream_transcribe_and_translate(
    history_state: list, # List of dicts for history
    new_chunk: tuple,    # (sr, np.array) from gr.Audio
    selected_input_lang_code: str, # From dropdown
    selected_output_lang_code: str # From dropdown
):
    """
    Processes streaming audio: STT -> Translate -> TTS.
    Yields updates to Gradio UI outputs.
    """
    # Initialize output variables
    current_original_text = ""
    current_translated_text = ""
    current_audio_output = None
    current_status = "🔄 Processing your speech..."

    # Handle initial state or no chunk
    if new_chunk is None:
        return history_state, current_status, current_original_text, current_translated_text, current_audio_output, format_history_display(history_state)

    sr, y = new_chunk
    
    # Process audio chunk (mono, int16, AudioSegment)
    if y.ndim > 1:
        y = y.mean(axis=1)
    y_int16 = y.astype(np.int16)
    audio_segment = AudioSegment(
        y_int16.tobytes(),
        frame_rate=sr,
        sample_width=y_int16.dtype.itemsize,
        channels=1
    )

    current_timestamp = datetime.now().strftime("%H:%M:%S")

    try:
        # Step 1: Speech-to-Text (STT) - Get transcript and auto-detected language
        # Even if input_language_code is 'unknown', Sarvam STT can often detect.
        # We pass it as a hint.
        transcript, detected_source_lang = call_stt_api(audio_segment, SARVAM_API_KEY)
        
        # If STT failed or no meaningful text was transcribed
        if not transcript.strip() or "Error" in transcript:
            current_status = f"⏳ Listening for clear speech... ({transcript})"
            return history_state, current_status, "", "", None, format_history_display(history_state)
        
        # Determine actual source language for translation.
        # If the user selected 'unknown', rely solely on detected_source_lang.
        # Otherwise, trust the user's explicit selection if available.
        final_source_lang = selected_input_lang_code if selected_input_lang_code != "unknown" and selected_input_lang_code else detected_source_lang
        
        source_lang_info = LANGUAGE_MAPPINGS.get(final_source_lang, {"name": "Unknown", "flag": "❓"})
        current_original_text = f"{transcript}"

        # Step 2: Text-to-Text Translation
        target_lang_info = LANGUAGE_MAPPINGS.get(selected_output_lang_code, {"name": "Unknown", "flag": "❓"})
        translated_text = call_translate_api(transcript, final_source_lang, selected_output_lang_code, SARVAM_API_KEY)
        
        current_translated_text = f"{translated_text}"

        # Step 3: Text-to-Speech (TTS)
        current_audio_output = call_tts_api(translated_text, selected_output_lang_code, SARVAM_API_KEY)

        # Update history state
        history_entry = {
            'timestamp': current_timestamp,
            'source_lang': source_lang_info['name'],
            'target_lang': target_lang_info['name'],
            'original': transcript,
            'translated': translated_text
        }
        history_state.append(history_entry)
        if len(history_state) > 10:
            history_state.pop(0)

        # Yield current state for UI update
        yield history_state, "✅ Translation completed successfully", current_original_text, current_translated_text, current_audio_output, format_history_display(history_state)

    except Exception as e:
        current_status = f"❌ Processing error: {str(e)}"
        yield history_state, current_status, current_original_text, current_translated_text, current_audio_output, format_history_display(history_state)


def format_history_display(history_list: list):
    """Helper to format history for display in the Textbox."""
    if not history_list:
        return "No translations yet. Start speaking to see your history here."
    
    formatted_entries = []
    for entry in history_list[-5:]:  # Show last 5 entries
        formatted_entries.append(
            f"🕒 {entry['timestamp']}\n"
            f"🎤 {entry['source_lang']}: {entry['original']}\n"
            f"🔄 {entry['target_lang']}: {entry['translated']}\n"
            f"{'─' * 50}"
        )
    return "\n".join(formatted_entries)

def clear_all_outputs_and_state():
    """Clears all UI elements and resets the history state."""
    return [], "", "", "", None, "✅ Ready for translation"

# --- Gradio UI Definition ---
with gr.Blocks(
    theme=gr.themes.Default(
        primary_hue="blue",
        secondary_hue="gray",
        neutral_hue="slate",
    ),
    css="""
    /* Global Styles */
    .gradio-container {
        max-width: 1400px !important;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
        font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif !important;
        min-height: 100vh;
        padding: 0 !important;
    }
    
    /* Header Styles */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem 3rem;
        margin: 0 0 2rem 0;
        border-radius: 0 0 24px 24px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.1;
    }
    
    .main-header h1 {
        font-size: 3rem !important;
        font-weight: 800 !important;
        margin: 0 0 0.5rem 0 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        font-size: 1.2rem !important;
        opacity: 0.95;
        margin: 0 !important;
        position: relative;
        z-index: 1;
    }
    
    /* Card Styles */
    .premium-card {
        background: white !important;
        border-radius: 20px !important;
        padding: 2rem !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1) !important;
        border: 1px solid rgba(255,255,255,0.8) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
        margin-bottom: 1.5rem !important;
    }
    
    .premium-card:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 50px rgba(0,0,0,0.15) !important;
    }
    
    .audio-card {
        background: linear-gradient(145deg, #ffffff, #f8fafc) !important;
        border: 2px dashed #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
    }
    
    .audio-card:hover {
        border-color: #667eea !important;
        background: linear-gradient(145deg, #f8fafc, #ffffff) !important;
    }
    
    /* Status Display */
    .status-display {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        font-weight: 600 !important;
        text-align: center !important;
        padding: 1rem 1.5rem !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        font-size: 1.1rem !important;
    }
    
    /* Translation Boxes */
    .translation-input {
        background: linear-gradient(145deg, #f8fafc, #ffffff) !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        color: #1a202c !important;
        min-height: 120px !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.06) !important;
    }
    
    .translation-input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Dropdowns */
    .language-dropdown {
        background: white !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #374151 !important;
        transition: all 0.2s ease !important;
    }
    
    .language-dropdown:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Buttons */
    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.875rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
    }
    
    .btn-secondary {
        background: linear-gradient(135deg, #718096 0%, #4a5568 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.875rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 15px rgba(113, 128, 150, 0.3) !important;
    }
    
    .btn-secondary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(113, 128, 150, 0.4) !important;
        background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%) !important;
    }
    
    /* Labels */
    label {
        font-weight: 600 !important;
        color: #374151 !important;
        font-size: 1rem !important;
        margin-bottom: 0.5rem !important;
        display: block !important;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        color: #1a202c !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 3px solid #667eea !important;
        display: inline-block !important;
    }
    
    /* History Display */
    .history-display {
        background: linear-gradient(145deg, #f7fafc, #edf2f7) !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace !important;
        font-size: 0.9rem !important;
        line-height: 1.5 !important;
        color: #2d3748 !important;
        min-height: 200px !important;
        white-space: pre-wrap !important;
        overflow-y: auto !important;
        max-height: 400px !important;
    }
    
    /* Audio Component */
    .gr-audio {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    }
    
    /* Company Logo Section */
    .company-section {
        background: white !important;
        border-radius: 20px !important;
        padding: 2rem !important;
        text-align: center !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1) !important;
        border: 1px solid rgba(255,255,255,0.8) !important;
        margin-top: 2rem !important;
    }
    
    .logo-placeholder {
        width: 200px !important;
        height: 80px !important;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%) !important;
        border: 2px dashed #cbd5e0 !important;
        border-radius: 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto 1rem auto !important;
        color: #718096 !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .logo-placeholder:hover {
        border-color: #667eea !important;
        background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%) !important;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .gradio-container {
            padding: 1rem !important;
        }
        
        .main-header {
            padding: 1.5rem 1rem !important;
        }
        
        .main-header h1 {
            font-size: 2rem !important;
        }
        
        .premium-card {
            padding: 1.5rem !important;
        }
        
        .btn-primary, .btn-secondary {
            padding: 0.75rem 1.5rem !important;
            font-size: 0.9rem !important;
        }
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .premium-card {
        animation: fadeIn 0.6s ease-out !important;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a67d8, #6b46c1);
    }
    """
) as demo:

    # Main Header
    gr.HTML("""
    <div class="main-header">
        <h1>🌍 AI Translation Studio</h1>
        <p>Professional real-time speech translation powered by advanced AI</p>
    </div>
    """)

    with gr.Row(equal_height=False):
        # Left Column - Audio Input and Controls
        with gr.Column(scale=3):
            with gr.Group(elem_classes="premium-card"):
                gr.HTML('<h3 class="section-header">🎤 Audio Input</h3>')
                
                with gr.Group(elem_classes="audio-card"):
                    gr.HTML("""
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: #374151; margin: 0 0 0.5rem 0; font-size: 1.1rem;">Live Voice Recording</h4>
                        <p style="color: #6b7280; margin: 0; font-size: 0.95rem;">Click record and speak naturally. Translation happens in real-time.</p>
                    </div>
                    """)
                    
                    input_audio_microphone = gr.Audio(
                        sources=["microphone"],
                        type="numpy",
                        label="🎙️ Microphone",
                        streaming=True,
                    )
                
                with gr.Row():
                    clear_button = gr.Button(
                        "🗑️ Clear All", 
                        variant="secondary",
                        elem_classes="btn-secondary"
                    )
                    process_last_recording_btn = gr.Button(
                        "🚀 Process Recording", 
                        variant="primary", 
                        elem_classes="btn-primary"
                    )

        # Right Column - Controls and Status
        with gr.Column(scale=2):
            with gr.Group(elem_classes="premium-card"):
                gr.HTML('<h3 class="section-header">⚙️ Settings</h3>')
                
                status_display = gr.Textbox(
                    value="✅ Ready for translation",
                    label="🔄 System Status",
                    interactive=False,
                    elem_classes="status-display"
                )
                
                input_language_code_box = gr.Dropdown(
                    choices=[(val["flag"] + " " + val["name"], key) for key, val in LANGUAGE_MAPPINGS.items() if key != "unknown"],
                    label="🎯 Input Language (Auto-detect if unsure)",
                    value="en-IN",
                    interactive=True,
                    elem_classes="language-dropdown"
                )

                output_language_code_box = gr.Dropdown(
                    choices=[(val["flag"] + " " + val["name"], key) for key, val in LANGUAGE_MAPPINGS.items() if key != "unknown"],
                    label="🌐 Target Language",
                    value="hi-IN",
                    interactive=True,
                    elem_classes="language-dropdown"
                )

    # Translation Results Row
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group(elem_classes="premium-card"):
                gr.HTML('<h3 class="section-header">📝 Original Speech</h3>')
                original_output_display = gr.Textbox(
                    label="Your spoken words will appear here",
                    lines=5,
                    placeholder="Start speaking to see your transcribed speech here...",
                    interactive=False,
                    elem_classes="translation-input"
                )

        with gr.Column(scale=1):
            with gr.Group(elem_classes="premium-card"):
                gr.HTML('<h3 class="section-header">🔄 Live Translation</h3>')
                translated_output_display = gr.Textbox(
                    label="Real-time translation output",
                    lines=5,
                    placeholder="Translation will appear here instantly...",
                    interactive=False,
                    elem_classes="translation-input"
                )

    # Audio Output and History Row
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group(elem_classes="premium-card"):
                gr.HTML('<h3 class="section-header">🔊 Audio Output</h3>')
                generated_audio_output = gr.Audio(
                    label="Generated speech in target language",
                    interactive=False
                )

        with gr.Column(scale=1):
            with gr.Group(elem_classes="premium-card"):
                gr.HTML('<h3 class="section-header">📜 Translation History</h3>')
                history_display_box = gr.Textbox(
                    label="Recent translations",
                    lines=8,
                    placeholder="Your translation history will appear here...",
                    interactive=False,
                    elem_classes="history-display"
                )

    # Company Logo Section
    with gr.Row():
        with gr.Column():
            with gr.Group(elem_classes="company-section"):
                gr.HTML("""
                <div class="logo-placeholder">
                    <span>Your Company Logo Here</span>
                </div>
                <p style="color: #6b7280; font-size: 0.9rem; margin: 0;">
                    Powered by Advanced AI Technology • Replace this section with your company branding
                </p>
                """)

    # Features and Instructions
    gr.HTML("""
    <div style="background: white; border-radius: 20px; padding: 2rem; margin-top: 2rem; box-shadow: 0 10px 40px rgba(0,0,0,0.1);">
        <h3 style="color: #1a202c; font-size: 1.4rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 3px solid #667eea; display: inline-block;">✨ Key Features</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 1.5rem;">
            <div style="background: linear-gradient(145deg, #f8fafc, #ffffff); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <h4 style="color: #374151; margin-top: 0;">🌐 Multi-Language Support</h4>
                <p style="color: #6b7280; margin: 0.5rem 0 0 0;">Translate between multiple languages including Hindi, Bengali, Tamil, Telugu, and more.</p>
            </div>
            <div style="background: linear-gradient(145deg, #f8fafc, #ffffff); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <h4 style="color: #374151; margin-top: 0;">🎙️ Real-Time Translation</h4>
                <p style="color: #6b7280; margin: 0.5rem 0 0 0;">Experience seamless real-time speech-to-speech translation with minimal latency.</p>
            </div>
            <div style="background: linear-gradient(145deg, #f8fafc, #ffffff); border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <h4 style="color: #374151; margin-top: 0;">🔊 Text-to-Speech</h4>
                <p style="color: #6b7280; margin: 0.5rem 0 0 0;">Hear translations spoken aloud with natural-sounding text-to-speech synthesis.</p>
            </div>
        </div>
    </div>
    """)

    # State and Event Handlers
    history_state = gr.State(value=[])

    # Link the audio stream to the core processing function
    input_audio_microphone.stream(
        fn=stream_transcribe_and_translate,
        inputs=[history_state, input_audio_microphone, input_language_code_box, output_language_code_box],
        outputs=[history_state, status_display, original_output_display, translated_output_display, generated_audio_output, history_display_box],
        show_progress='hidden',
        queue=True
    )

    # Process the last recorded segment
    process_last_recording_btn.click(
        fn=stream_transcribe_and_translate,
        inputs=[history_state, input_audio_microphone, input_language_code_box, output_language_code_box],
        outputs=[history_state, status_display, original_output_display, translated_output_display, generated_audio_output, history_display_box]
    )

    # Clear button functionality
    clear_button.click(
        fn=clear_all_outputs_and_state,
        outputs=[history_state, original_output_display, translated_output_display, generated_audio_output, history_display_box, status_display]
    )

# Launch the Gradio app
if __name__ == "__main__":
    demo.queue()
    demo.launch(
        debug=True,
        server_name="0.0.0.0",
        server_port=7860,
        quiet=False
    )
