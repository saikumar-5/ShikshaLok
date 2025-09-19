import gradio as gr
import time
import numpy as np
import os
import requests
import io
from pydub import AudioSegment

# Replace 'your_api_key_here' with your actual Sarvam AI API key
SARVAM_API_KEY = "sk_aov2qcwm_v6DDreRZzU6ntWRM5ixh8voS"

def translate_audio(audio, input_language_code, output_language_code):
    api_url = "https://api.sarvam.ai/speech-to-text-translate"
    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }
    model_data = {
        "model": "saaras:v2",
        "with_diarization": False,
        "input_language_code": input_language_code,
        "output_language_code": output_language_code
    }

    chunk_buffer = io.BytesIO()
    audio.export(chunk_buffer, format="wav")
    chunk_buffer.seek(0)
    files = {'file': ('audiofile.wav', chunk_buffer, 'audio/wav')}

    try:
        response = requests.post(api_url, headers=headers, files=files, data=model_data)
        print(f"API Request URL: {api_url}")
        print(f"API Request Headers: {headers}")
        print(f"API Request Data: {model_data}")
        print(f"API Response Status Code: {response.status_code}")
        print(f"API Response Content: {response.text}")

        if response.status_code == 200 or response.status_code == 201:
            response_data = response.json()
            transcript = response_data.get("transcript", "")
            detected_language = response_data.get("language_code", "")
            print(f"Transcript: {transcript}")
            print(f"Detected Language: {detected_language}")
        elif response.status_code == 401 or response.status_code == 403:
            raise ValueError("❌ Invalid API key. Please check your Sarvam AI key.")
        else:
            raise RuntimeError(f"❌ Request failed with status code: {response.status_code}. Details: {response.text}")
    except Exception as e:
        raise e
    finally:
        chunk_buffer.close()

    return transcript, detected_language

def stream_transcribe(history, new_chunk, input_language_code, output_language_code):
    if history is None:
        history = ""

    try:
        sr, y = new_chunk
        # Convert to mono if stereo
        if y.ndim > 1:
            y = y.mean(axis=1)
        # Convert to int16 for AudioSegment
        y_int16 = y.astype(np.int16)
        # Create AudioSegment from raw PCM data
        audio_segment = AudioSegment(
            data=y_int16.tobytes(),
            sample_width=2,
            frame_rate=sr,
            channels=1
        )
        transcription, detected_language = translate_audio(audio_segment, input_language_code, output_language_code)

        history = history + '\n' + f'({detected_language})==> ' + transcription
        return history, history
    except ValueError as ve:
        return history, str(ve)
    except Exception as e:
        print(f"Error during Transcription: {e}")
        return history, str(e)

def clear():
    return ""

def clear_state():
    return None

with gr.Blocks(theme=gr.themes.Soft()) as microphone:
    with gr.Column():
        input_language_options = [
            "hi-IN", "bn-IN", "kn-IN", "ml-IN", "mr-IN", "od-IN",
            "pa-IN", "ta-IN", "te-IN", "en-IN", "gu-IN", "unknown"
        ]

        output_language_options = [
            "en-IN", "hi-IN", "bn-IN", "kn-IN", "ml-IN", "mr-IN",
            "od-IN", "pa-IN", "ta-IN", "te-IN", "gu-IN"
        ]

        input_language_code_box = gr.Dropdown(
            choices=input_language_options,
            label="Select Input Language Code",
            value="unknown"
        )

        output_language_code_box = gr.Dropdown(
            choices=output_language_options,
            label="Select Output Language Code",
            value="te-IN"  # Default to Telugu as an example
        )

        input_audio_microphone = gr.Audio(streaming=True)
        output = gr.Textbox(label="Transcription", lines=10, max_lines=100, show_copy_button=True, value="")

        with gr.Row():
            clear_button = gr.Button("Clear Output")

        state = gr.State(value="")

        input_audio_microphone.stream(
            stream_transcribe,
            [state, input_audio_microphone, input_language_code_box, output_language_code_box],
            [state, output],
            time_limit=30,
            stream_every=5,
            concurrency_limit=None,
        )

        clear_button.click(clear_state, outputs=[state]).then(clear, outputs=[output])

demo = microphone
demo.launch()
