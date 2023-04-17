from sqlmodel import SQLModel, Field
from datetime import datetime

class Rooms(SQLModel):
    id: int = Field(default=None, primary_key=True)
    room_id: int
    
    start: int
    end: int
    
    asr_tsv: str
    asr_txt: str
    asr_json: str
    
    tm_create: datetime = datetime.now()
    tm_modify: datetime = datetime.now()
    