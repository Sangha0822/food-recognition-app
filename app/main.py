from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select, desc
from app.database import create_db_and_tables
from app.models import FoodEntry, FoodEntryCreate
from app.database import get_session
from pathlib import Path
import uuid
from fastapi.staticfiles import StaticFiles
from typing import Optional
from sqlalchemy import func
from fastapi.middleware.cors import CORSMiddleware
import google.genai as genai
from dotenv import load_dotenv
import os

@asynccontextmanager # Creates the DB when it starts
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(lifespan = lifespan)

app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents = True, exist_ok = True)

@app.get("/health") # Testing 
def health_check():
    return {"ok": True}

@app.post("/entries") # Adds JSON format into the DB
def create_food_entry(entry: FoodEntryCreate, session: Session =Depends(get_session)):
    food = FoodEntry(final_label = entry.final_label)
    session.add(food)
    session.commit()
    session.refresh(food)
    return food

@app.get("/entries") # Gets the DB entries
def read_food_entries(label: Optional[str] = None, offset: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    dicFoodEntries = {}

    statement = select(FoodEntry)
    if label:
        statement = statement.where(FoodEntry.final_label.ilike(f"%{label}%"))
    count_statement = select(func.count()).select_from(statement.subquery())
    result_statement = statement.order_by(desc(FoodEntry.id)).offset(offset).limit(limit)
    results = session.exec(result_statement).all()
    total = session.exec(count_statement).one()

    dicFoodEntries["total"] = total
    dicFoodEntries["offset"] = offset
    dicFoodEntries["limit"] = limit
    dicFoodEntries["entries"] = results
    dicFoodEntries["has_next"] = True if total - offset > limit else False
    return dicFoodEntries

@app.delete("/entries/{entry_id}") # Deleting unique ID datas from the DB
def delete_entry(entry_id: int, session: Session = Depends(get_session)):
    entry = session.get(FoodEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    else:
        if entry.image_path is not None:
            Path(entry.image_path).unlink(missing_ok=True)
        session.delete(entry)
        session.commit()

    
@app.post("/uploads")# Uploads the image to DB (adds Multipart Form data so it should not be merged with entries saving function)
def create_upload(file: UploadFile =File(...), final_label: Optional[str] = Form(None), session: Session =Depends(get_session)):
    extension = Path(file.filename).suffix
    uuidName = str(uuid.uuid4())
    newFileName = uuidName + extension
    file_path = UPLOAD_DIR / newFileName
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    if not final_label:
        final_label = identify_food(str(file_path))
    food = FoodEntry(image_path = str(file_path), final_label = final_label)
    session.add(food)
    session.commit()
    session.refresh(food)
    return food

app.mount("/static", StaticFiles(directory="uploads"), name="static")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

def identify_food(image_path: str) -> str:
    image_bytes = Path(image_path).read_bytes()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            genai.types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            "What food is this? Reply with just the food name, nothing else."
        ]
    )
    return response.text.strip()