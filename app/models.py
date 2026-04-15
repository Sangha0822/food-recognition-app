from typing import Optional
from sqlmodel import SQLModel, Field
from pathlib import Path
from pydantic import computed_field
from datetime import datetime, timezone

class FoodEntry(SQLModel, table=True): # Database table class
    id: Optional[int] = Field(default=None, primary_key=True) 
    image_path: Optional[str] = None
    final_label: Optional[str] = None
    logged_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")

    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        if not self.image_path:
            return None
        filename = Path(self.image_path).name
        return f"http://127.0.0.1:8000/static/{filename}"
    
    

class User(SQLModel, table=True): # What goes INSIDE DB
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    hashed_password: str
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(SQLModel): # What the user SENDS to backend
    email: str
    password: str
