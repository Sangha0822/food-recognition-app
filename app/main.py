from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select, desc
from app.database import create_db_and_tables
from app.models import FoodEntry, FoodEntryCreate, UserCreate
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
import app.auth as auth
from app.models import User
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    try:
        decodedToken = auth.decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail = "Invalid or expired token")
    userEmail = decodedToken.get("sub")
    user = session.exec(select(User).where(User.email == userEmail)).first()
    if not user:
        raise HTTPException(status_code=401, detail = "Invalid or expired token")
    return user

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
def delete_entry(entry_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    entry = session.get(FoodEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    else:
        if entry.image_path is not None:
            Path(entry.image_path).unlink(missing_ok=True)
        session.delete(entry)
        session.commit()

    
@app.post("/uploads")# Uploads the image to DB (adds Multipart Form data so it should not be merged with entries saving function)
def create_upload(file: UploadFile =File(...), final_label: Optional[str] = Form(None), current_user: User = Depends(get_current_user), session: Session =Depends(get_session)):
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

@app.post("/register")
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    emailExist = session.exec(select(User).where(User.email == user_data.email)).first()
    if emailExist:    
        raise HTTPException(status_code=400, detail="Email is already registered")
    hashPWD = auth.hash_password(user_data.password)
    user = User(email = user_data.email, hashed_password = hashPWD)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "User registered successfully"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    emailExist = session.exec(select(User).where(User.email == form_data.username)).first()
    if not emailExist or not auth.verify_password(form_data.password, emailExist.hashed_password):
        raise HTTPException(status_code=401, detail="Email or the password is wrong. Please check again.")
    encodedJWT = auth.create_access_token({"sub": form_data.username})
    return {"access_token": encodedJWT, "token_type": "bearer"}


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

