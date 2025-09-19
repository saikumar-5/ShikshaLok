from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydub import AudioSegment
import os
import tempfile
import uuid
import requests
import io
import base64
import logging
import mimetypes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy translation function (replace with your logic)
def translate_text(text, source_lang, target_lang):
    # TODO: Replace with actual translation logic or API call
    return f"[Translated {source_lang}->{target_lang}]: {text}"

# Dummy TTS function (replace with your logic)
def text_to_speech(text, lang):
    # TODO: Replace with actual TTS logic or API call
    # For now, just return a dummy wav file
    dummy_wav = os.path.join(tempfile.gettempdir(), f"dummy_{uuid.uuid4()}.wav")
    silent = AudioSegment.silent(duration=1000)  # 1 second silence
    silent.export(dummy_wav, format="wav")
    return dummy_wav

SARVAM_API_KEY = "sk_aov2qcwm_v6DDreRZzU6ntWRM5ixh8voS"
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

@app.post("/translate")
async def translate(text: str = Form(...), source_lang: str = Form(...), target_lang: str = Form(...)):
    translated = translate_text(text, source_lang, target_lang)
    return {"translated_text": translated}

@app.post("/tts")
async def tts(text: str = Form(...), lang: str = Form(...)):
    wav_path = text_to_speech(text, lang)
    return FileResponse(wav_path, media_type="audio/wav")

@app.post("/api/speech-to-text")
async def speech_to_text(file: UploadFile = File(...), language_code: str = Form("auto")):
    logging.info(f"Received file: {file.filename}, content_type: {file.content_type}, lang: {language_code}")
    try:
        file.file.seek(0)
        mime = file.content_type
        if mime in ["audio/webm", "audio/ogg"]:
            audio = AudioSegment.from_file(file.file, format="webm" if "webm" in mime else "ogg")
        else:
            audio = AudioSegment.from_file(file.file)
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        duration_sec = len(audio) / 1000.0
        logging.info(f"Audio duration: {duration_sec:.2f} seconds")
        chunk_length_ms = 30 * 1000
        transcripts = []
        if duration_sec > 30:
            logging.info("Audio longer than 30s, splitting into chunks...")
            for i in range(0, len(audio), chunk_length_ms):
                chunk = audio[i:i+chunk_length_ms]
                wav_io = io.BytesIO()
                chunk.export(wav_io, format="wav")
                wav_io.seek(0)
                files = {"file": ("audio.wav", wav_io.getvalue(), "audio/wav")}
                headers = {"api-subscription-key": SARVAM_API_KEY}
                data = {"language_code": language_code}
                logging.info(f"Sending chunk {i//chunk_length_ms+1} to Sarvam STT API...")
                response = requests.post(SARVAM_STT_URL, headers=headers, files=files, data=data)
                sarvam_json = response.json()
                logging.info(f"Chunk {i//chunk_length_ms+1} Sarvam response: {sarvam_json}")
                transcript = sarvam_json.get("transcript", "")
                if not transcript:
                    logging.error(f"No transcript for chunk {i//chunk_length_ms+1}")
                transcripts.append(transcript)
            full_transcript = ' '.join([t for t in transcripts if t])
            if not full_transcript:
                return JSONResponse(content={"error": "No transcript returned from STT API for any chunk."}, status_code=200)
            return JSONResponse(content={"transcript": full_transcript})
        else:
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_io.seek(0)
            files = {"file": ("audio.wav", wav_io.getvalue(), "audio/wav")}
            headers = {"api-subscription-key": SARVAM_API_KEY}
            data = {"language_code": language_code}
            logging.info("Sending request to Sarvam STT API...")
            response = requests.post(SARVAM_STT_URL, headers=headers, files=files, data=data)
            logging.info(f"Sarvam STT API response status: {response.status_code}")
            sarvam_json = response.json()
            logging.info(f"Sarvam STT API response: {sarvam_json}")
            transcript = sarvam_json.get("transcript", "")
            if not transcript:
                logging.error("No transcript returned from Sarvam STT API.")
                return JSONResponse(content={"error": "No transcript returned from STT API.", "sarvam_response": sarvam_json}, status_code=200)
            return JSONResponse(content=sarvam_json)
    except Exception as e:
        logging.error(f"Error in /api/speech-to-text: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/translate")
async def translate_api(request: Request):
    data = await request.json()
    logging.info(f"Received translate request: {data}")
    headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
    try:
        response = requests.post(SARVAM_TRANSLATE_URL, headers=headers, json=data)
        logging.info(f"Sarvam Translate API response status: {response.status_code}")
        sarvam_json = response.json()
        logging.info(f"Sarvam Translate API response: {sarvam_json}")
        translated = sarvam_json.get("translated_text", "")
        if not translated:
            logging.error("No translated_text returned from Sarvam Translate API.")
            return JSONResponse(content={"error": "No translated_text returned from Translate API.", "sarvam_response": sarvam_json}, status_code=200)
        return JSONResponse(content=sarvam_json)
    except Exception as e:
        logging.error(f"Error in /api/translate: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/text-to-speech")
async def text_to_speech_api(request: Request):
    data = await request.json()
    logging.info(f"Received TTS request: {data}")
    headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
    try:
        response = requests.post(SARVAM_TTS_URL, headers=headers, json=data)
        logging.info(f"Sarvam TTS API response status: {response.status_code}")
        result = response.json()
        logging.info(f"Sarvam TTS API response: {result}")
        audio_content = result.get("audio_content")
        if not audio_content:
            audios = result.get("audios", [])
            if audios and isinstance(audios, list):
                audio_content = audios[0]  # Use the first audio if available
        if audio_content:
            audio_bytes = base64.b64decode(audio_content)
            temp_wav = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4()}.wav")
            with open(temp_wav, "wb") as f:
                f.write(audio_bytes)
            return FileResponse(temp_wav, media_type="audio/wav")
        logging.error("No audio_content returned from Sarvam TTS API.")
        return JSONResponse(content={"error": "No audio content returned from TTS API.", "sarvam_response": result}, status_code=200)
    except Exception as e:
        logging.error(f"Error in /api/text-to-speech: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
def health():
    return {"status": "ok"} 