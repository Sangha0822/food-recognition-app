from typing import Optional
from sqlmodel import SQLModel, Field
from pathlib import Path
from pydantic import computed_field

class FoodEntry(SQLModel, table=True): # Database table class
    id: Optional[int] = Field(default=None, primary_key=True) 
    image_path: Optional[str] = None
    final_label: Optional[str] = None

    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        if not self.image_path:
            return None
        filename = Path(self.image_path).name
        return f"http://127.0.0.1:8000/static/{filename}"
    
    

class FoodEntryCreate(SQLModel): # Request body class for creating a food entry
    final_label: Optional[str] = None



