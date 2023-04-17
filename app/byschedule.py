import time
import schedule
import threading
import asyncio
import os, json
from sqlmodel import Session, select

from app.core.config import settings
from app.models.rooms import Rooms
from app.db.session import engine
from app.client.page_pl import DyPagePl
from app.client.websocket import DyWss
from app.task.scrapy import process_audio

from loguru import logger
from func_timeout import func_set_timeout, FunctionTimedOut

TIME_SCRAPY = settings.TIME_SCRAPY
MAX_THREADS = settings.MAX_THREADS

# 获取页面上下文信息，包括 WebSocket URL 等
async def get_context(url: str):
    page = DyPagePl()
    await page.start_browser()
    
    ctx = await page.get_websocket_url(url)
    await page.close_browser()
    return ctx

# 运行 WebSocket 连接并设置超时时间
def wss_run(ctx):
        path = f"data/{ctx.room_id}_{ctx.tm_create}"
        os.makedirs(f"{path}", exist_ok=True)
        output_file = f"{path}/chats.txt"
        wss = DyWss(ctx.wss_url, ctx.cookie_ttwid, output_file)
        wss.long_live_run()
    
# 长连接，获取聊天信息
def trace_chats(ctx):
    try:
        wss_run(ctx)
    except FunctionTimedOut:
        logger.warning("下载超时，结束")
    finally:
        logger.debug("完成弹幕追踪")
        
# 持续下载内容，保存成音频文件
def trace_streams(ctx):
    try:
        path = f"data/{ctx.room_id}_{ctx.tm_create}"
        os.makedirs(f"{path}", exist_ok=True)
        process_audio(ctx.flv, f"{path}")
    except Exception as e:
        logger.error(e)

# 跟踪直播间，创建线程
def trace_living_room(ctx):
    if threading.active_count() <= MAX_THREADS:
        chats_thread = threading.Thread(target=trace_chats, args=(ctx, ))
        flv_thread = threading.Thread(target=trace_streams, args=(ctx,))
        
        chats_thread.start()
        flv_thread.start()
        
        logger.debug(f"start threads, ctx={ctx.url}, threading.active_count={threading.active_count()}")
    else:
        logger.debug(f"threads is full, ctx={ctx.url}, threading.active_count={threading.active_count()}")

# 检查直播间是否在线，设置每一轮任务超时时间
def check_live(session: Session):
    if not os.path.exists(settings.URLS_FILE):
        logger.error(f"urls file: {settings.URLS_FILE} not exists")
        exit(0)
    
    urls = []
    with open(settings.URLS_FILE, 'r') as f:
        urls = list(set([x.strip() for x in f.read().split("\n") if x.strip().startswith('https://live.douyin.com/')]))
    
        for url in urls:
            ctx = None
            try:
                ctx = asyncio.run(get_context(url))
            except Exception as e:
                logger.warning(f"异常: url={url} e={e}")
                continue
                
            if ctx:
                room = Rooms(room_id=ctx.room_id,
                            url=ctx.url,
                            flv=ctx.flv,
                            title=ctx.title,
                            user_count=ctx.user_count,
                            owner_sec_uid=ctx.owner_sec_uid,
                            owner_nickname=ctx.owner_nickname,
                            context=json.dumps(ctx.dict(), ensure_ascii=False))
                session.add(room)
                try:
                    session.commit()
                except Exception as e:
                    logger.warning(f"异常: url={url} e={e}")
                    session.rollback()

                logger.debug(ctx)
                trace_living_room(ctx)

def job():
    session = Session(engine)
    try:
        check_live(session)
    except FunctionTimedOut:
        logger.warning(f"本次轮询任务超时: {int(TIME_SCRAPY+TIME_SCRAPY/2)}")
    finally:
        session.close()

if __name__ == '__main__':
    job()
    
    exit(0)

# 用crontab控制
# 0 0-2,8-23/2 * * * conda activate douyin && cd xxx/livescrapy and python -m app.byschedule



"""
if __name__ == '__main__':
    job()
    # 每两小时执行一次，并且从现在开始立刻启动一次
    schedule.every().day.at("08:00").do(job)  # 从 8am 开始第一次运行任务

    while True:
        nowHour = int(time.strftime('%H'))
        if nowHour >= 2 and nowHour < 8:
            schedule.clear()  # 不在时间范围内，清除任务计划
        else:
            schedule.every(2).hours.do(job)  # 从 8am 到 2am 之间每隔两小时运行一次

        schedule.run_pending()
        time.sleep(10)
    
"""