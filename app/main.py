from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select, desc
from app.database import create_db_and_tables
from app.models import FoodEntry, UserCreate, PasswordChange
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
from email_validator import validate_email, EmailNotValidError
import json

@asynccontextmanager # Creates the DB when it starts
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(lifespan = lifespan)

app.add_middleware( 
    CORSMiddleware,
    allow_origins=["https://food-recognition-app-7rtx.onrender.com"], 
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

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "language": current_user.language}

@app.patch("/me/language")
def set_language(language: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if language not in ("en", "ko"):
        raise HTTPException(status_code=400, detail="Language must be 'en' or 'ko'")
    current_user.language = language
    session.add(current_user)
    session.commit()
    return {"language": language}


@app.patch("/me/password")
def change_password(data: PasswordChange, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if not auth.verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    current_user.hashed_password = auth.hash_password(data.new_password)
    session.add(current_user)
    session.commit()
    return {"message": "Password changed successfully"}

@app.get("/entries/summary")
def get_summary(days: int = 7, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    statement = (
        select(
            func.date(FoodEntry.logged_at).label("date"),
            func.sum(FoodEntry.calories).label("total")
        )
        .where(FoodEntry.user_id == current_user.id)
        .where(FoodEntry.logged_at >= cutoff)
        .where(FoodEntry.calories.isnot(None))
        .group_by(func.date(FoodEntry.logged_at))
        .order_by(func.date(FoodEntry.logged_at))
    )
    results = session.execute(statement).all()
    return [{"date": str(row.date), "calories": int(row.total)} for row in results]

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
    calories = None
    if not final_label:
        result = identify_food(content, file.content_type, current_user.language)
        final_label = result["food"]
        calories = result["calories"]
    food = FoodEntry(image_path = str(url_path), final_label = final_label, user_id = current_user.id, calories=calories)
    session.add(food)
    session.commit()
    session.refresh(food)
    return food

@app.post("/register")
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    try:
        emailinfo = validate_email(user_data.email, check_deliverability=False)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Please write valid email.")

    emailExist = session.exec(select(User).where(User.email == emailinfo.normalized)).first()
    if emailExist:
        raise HTTPException(status_code=400, detail="Email is already registered")
    hashPWD = auth.hash_password(user_data.password)
    user = User(email = emailinfo.normalized, hashed_password = hashPWD)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "User registered successfully"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    try:
        normalized_email = validate_email(form_data.username, check_deliverability=False).normalized
    except EmailNotValidError:
        raise HTTPException(status_code=401, detail="Email or the password is wrong. Please check again.")
    emailExist = session.exec(select(User).where(User.email == normalized_email)).first()
    if not emailExist or not auth.verify_password(form_data.password, emailExist.hashed_password):
        raise HTTPException(status_code=401, detail="Email or the password is wrong. Please check again.")
    encodedJWT = auth.create_access_token({"sub": normalized_email})
    return {"access_token": encodedJWT, "token_type": "bearer"}


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

def identify_food(image_bytes: bytes, content_type: str, language: str = "en") -> dict:
    if language == "ko":
        prompt = '이 음식은 무엇인가요? 음식이라면 JSON 형식으로만 답하세요, 추가 텍스트 없이: {"food": "음식 이름", "calories": 예상_숫자}. 음식 이미지가 아니라면 {"food": "not_food", "calories": null} 을 반환하세요.'
    else:
        prompt = 'What food is this? If it is food, reply in JSON format only, no extra text: {"food": "food name", "calories": estimated_number}. If it is not a food image, return {"food": "not_food", "calories": null}'
    try:
        response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            genai.types.Part.from_bytes(data=image_bytes, mime_type=content_type),
            prompt
        ]
        )
        cleaned = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(cleaned)
    except Exception:
        raise HTTPException(status_code=503, detail="AI is busy, please add a label manually.")
    if result["food"] == "not_food":
        raise HTTPException(status_code=400, detail="The image does not appear to be food.")
    return result

