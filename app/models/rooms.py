from sqlmodel import SQLModel, Field
from datetime import datetime


class Rooms(SQLModel, table=True):
    __tablename__ = 'rooms'
    id: int = Field(default=None, primary_key=True)
    room_id: int
    user_count: str
    url: str = ''
    flv: str = ''
    title: str = ''
    owner_sec_uid: str = ''
    owner_nickname: str = ''
    context: str = ''

    tm_create: datetime = datetime.now()
    tm_modify: datetime = datetime.now()
