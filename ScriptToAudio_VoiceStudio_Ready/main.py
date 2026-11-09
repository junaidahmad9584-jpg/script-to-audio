from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import asyncio, uuid, os, sys, traceback, importlib.util

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
app = FastAPI(title="ScriptToAudio Voice Studio")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

class GenerateRequest(BaseModel):
    text: str
    voice: str = "hi-IN-SwaraNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"

class CloneRequest(BaseModel):
    text: str
    sample_name: str = "voice_clone.mp3"
    language: str = "hi"

@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "static" / "index.html").read_text(encoding="utf-8")

@app.get("/api/health")
def health():
    # Check package presence without importing XTTS, which can be slow on low-RAM PCs.
    return {"ok": True, "python": sys.version.split()[0],
            "edge_tts_available": importlib.util.find_spec("edge_tts") is not None,
            "xtts_available": importlib.util.find_spec("TTS") is not None,
            "message": "Backend is responding"}

@app.get("/api/status")
def status():
    return health()

@app.post("/api/generate")
async def generate(req: GenerateRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(400, "Please enter text first.")
    try:
        import edge_tts
    except Exception as e:
        raise HTTPException(500, "Edge-TTS package missing. Run install.bat again. Details: " + str(e))
    job_id = uuid.uuid4().hex[:10]
    output = OUT / f"speech_{job_id}.mp3"
    try:
        communicate = edge_tts.Communicate(text, req.voice, rate=req.rate, pitch=req.pitch)
        await communicate.save(str(output))
    except Exception as e:
        raise HTTPException(500, "Audio generation failed. Check internet connection. Details: " + str(e))
    return {"ok": True, "file": f"/outputs/{output.name}", "name": output.name}

@app.post("/api/upload-sample")
async def upload_sample(file: UploadFile = File(...)):
    allowed = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, "Supported sample formats: WAV, MP3, M4A, AAC, OGG, FLAC.")
    data = await file.read(25 * 1024 * 1024 + 1)
    if not data:
        raise HTTPException(400, "The selected sample file is empty.")
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(400, "Voice sample must be 25 MB or smaller.")
    safe_name = "uploaded_voice_sample" + suffix
    target = ROOT / safe_name
    target.write_bytes(data)
    return {"ok": True, "name": safe_name, "message": "Voice sample uploaded."}

@app.post("/api/clone")
def clone(req: CloneRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(400, "Please enter text first.")
    sample = (ROOT / req.sample_name).resolve()
    if ROOT.resolve() not in sample.parents or not sample.exists():
        raise HTTPException(400, f"Voice sample not found: {req.sample_name}. Put your sample in the project folder.")
    try:
        from TTS.api import TTS
    except Exception as e:
        raise HTTPException(500, "XTTS is not ready in this Python environment. Standard text-to-speech still works. Import error: " + str(e))
    output = OUT / f"clone_{uuid.uuid4().hex[:10]}.wav"
    try:
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
        tts.tts_to_file(text=text, speaker_wav=str(sample), language=req.language, file_path=str(output))
    except Exception as e:
        raise HTTPException(500, "XTTS voice cloning failed: " + str(e))
    return {"ok": True, "file": f"/outputs/{output.name}", "name": output.name}

@app.get("/outputs/{filename}")
def get_output(filename: str):
    path = (OUT / filename).resolve()
    if OUT.resolve() not in path.parents or not path.is_file():
        raise HTTPException(404, "Audio file not found.")
    return FileResponse(path, filename=path.name)
