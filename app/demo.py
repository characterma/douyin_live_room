from app.client.page import DyPage
from app.client.page_pl import DyPagePl
from app.schema.livingroom import LivingRoomContext

from app.client.websocket import DyWss
from loguru import logger
import asyncio

async def main():
    page = DyPagePl()
    await page.start_browser()
    
    #sec_id = await page.get_secid_by_name("交个朋友")
    #room = await page.get_living_room(sec_id) # 可能会弹出验证码导致失败
    #logger.debug(room)
    
    ctx = await page.get_websocket_url('https://live.douyin.com/100688345342')
    await page.close_browser()
    return ctx

if __name__ == '__main__':
    
    loop = asyncio.get_event_loop()
    try:
        ctx = loop.run_until_complete(main())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    
    logger.debug(ctx)
    wss = DyWss(ctx.wss_url, ctx.cookie_ttwid, 'output.log')
    wss.long_live_run()
    