
from pydantic import BaseModel
import time

class LivingRoomContext(BaseModel):
    url: str = '' # 
    room_id: str = ''
    title: str = ''
    cookie_ttwid: str = ''
    flvs: dict = {}
    flv: str = ''
    wss_url: str = ''
    user_id: str = ''
    user_unique_id: str = ''
    user_count: str = ''
    total_user: str = ''
    has_commerce_goods: bool = True
    owner_id: str = ''
    admin_user: str = ''
    owner_sec_uid: str = ''
    owner_nickname: str = ''
    tm_create: str = time.strftime("%Y%m%d%H", time.localtime())