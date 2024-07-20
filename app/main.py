import pathlib
import io
import uuid
import logging
from functools import lru_cache
from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    Depends,
    Request,
    File,
    UploadFile
)
import pytesseract
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings
from PIL import Image
from typing import Optional

# Update this path to the location of tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    debug: bool = False
    echo_active: bool = True
    skip_auth: bool = False

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

BASE_DIR = pathlib.Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads/images"

app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
def home_view(request: Request, settings: Settings = Depends(get_settings)):
    return templates.TemplateResponse("home.html", {"request": request, "abc": 123})

@app.post("/")
async def prediction_view(file: UploadFile = File(...), settings: Settings = Depends(get_settings)):
    bytes_str = io.BytesIO(await file.read())
    try:
        img = Image.open(bytes_str)
    except Exception as e:
        logger.error(f"Error opening image: {e}")
        raise HTTPException(detail="Invalid image", status_code=400)
    preds = pytesseract.image_to_string(img)
    predictions = [x for x in preds.split("\n")]
    return {"results": predictions, "original": preds}

@app.get("/", response_class=HTMLResponse)
def home_view(request: Request, settings: Settings = Depends(get_settings)):
    return templates.TemplateResponse("home.html", {"request": request, "abc": 123})

@app.post("/")
async def prediction_view(file: UploadFile = File(...), settings: Settings = Depends(get_settings)):
    bytes_str = io.BytesIO(await file.read())
    try:
        img = Image.open(bytes_str)
    except Exception as e:
        logger.error(f"Error opening image: {e}")
        raise HTTPException(detail="Invalid image", status_code=400)
    preds = pytesseract.image_to_string(img)
    predictions = [x for x in preds.split("\n")]
    return {"results": predictions, "original": preds}

@app.post("/img-echo/", response_class=FileResponse)
async def img_echo_view(file: UploadFile = File(...), settings: Settings = Depends(get_settings)):
    if not settings.echo_active:
        raise HTTPException(detail="Endpoint not active", status_code=400)
    
    UPLOAD_DIR.mkdir(exist_ok=True)
    logger.info("Received file upload request")
    
    try:
        bytes_str = io.BytesIO(await file.read())
        logger.info(f"File read successfully: {file.filename}")
        img = Image.open(bytes_str)
    except Exception as e:
        logger.error(f"Error opening image: {e}")
        raise HTTPException(detail="Invalid image", status_code=400)
    
    fname = pathlib.Path(file.filename)
    fext = fname.suffix
    dest = UPLOAD_DIR / f"{uuid.uuid1()}{fext}"
    logger.info(f"Saving file to: {dest}")
    
    try:
        img.save(dest)
        logger.info(f"File saved successfully to: {dest}")
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        raise HTTPException(detail="Failed to save image", status_code=500)
    
    return FileResponse(dest)
