from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select, desc
from app.database import create_db_and_tables
from app.models import FoodEntry, UserCreate
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
import boto3

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


@app.get("/entries") # Gets the DB entries
def read_food_entries(label: Optional[str] = None, offset: int = 0, limit: int = 10, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    dicFoodEntries = {}

    statement = select(FoodEntry)
    if label:
        statement = statement.where(FoodEntry.final_label.ilike(f"%{label}%")) 
    statement = statement.where(FoodEntry.user_id == current_user.id) # SQLModel chains them together so it does not replace the previous statement.
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
    if entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this entry")
    else:
        session.delete(entry)
        session.commit()

    
@app.post("/uploads")# Uploads the image to DB (adds Multipart Form data so it should not be merged with entries saving function)
def create_upload(file: UploadFile =File(...), final_label: Optional[str] = Form(None), current_user: User = Depends(get_current_user), session: Session =Depends(get_session)):
    extension = Path(file.filename).suffix.lower()
    acceptableFormat = set([".jpg", ".jpeg", ".png", ".webp", ".heic"])
    if extension not in acceptableFormat:
        raise HTTPException(status_code=400, detail = "Not acceptable image format.")
    uuidName = str(uuid.uuid4())
    newFileName = uuidName + extension
    
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    content = file.file.read()
    s3_client.put_object(
        Bucket=os.getenv("AWS_BUCKET_NAME"),
        Key=newFileName,
        Body=content,
        ContentType=file.content_type
    )
    bucket = os.getenv("AWS_BUCKET_NAME")
    url_path = f"https://{bucket}.s3.amazonaws.com/{newFileName}"

    if not final_label:
        final_label = identify_food(content, file.content_type)
    food = FoodEntry(image_path = str(url_path), final_label = final_label, user_id = current_user.id)
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

def identify_food(image_bytes: bytes, content_type: str) -> str:
    try:
        response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            genai.types.Part.from_bytes(data=image_bytes, mime_type=content_type),
            "What food is this? Reply with just the food name, nothing else."
        ]
        )
    except Exception:
        raise HTTPException(status_code=503, detail = "AI is busy, please add a label manually.")

    return response.text.strip()

