from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone

class FoodEntry(SQLModel, table=True): # Database table class
    id: Optional[int] = Field(default=None, primary_key=True) 
    image_path: Optional[str] = None
    final_label: Optional[str] = None
    logged_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    calories: Optional[int] = None

class User(SQLModel, table=True): # What goes INSIDE DB
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    hashed_password: str
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: Optional[str] = Field(default="en")

class UserCreate(SQLModel): # What the user SENDS to backend
    email: str
    password: str
