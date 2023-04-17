from app.client.page_pl import DyPagePl
from app.client.websocket import DyWss
from loguru import logger
import asyncio
import argparse

async def main(url: str):
    page = DyPagePl()
    await page.start_browser()
    
    #sec_id = await page.get_secid_by_name("交个朋友")
    #room = await page.get_living_room(sec_id) # 可能会弹出验证码导致失败
    #logger.debug(room)
    
    ctx = await page.get_websocket_url(url)
    await page.close_browser()
    return ctx

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='监控直播间弹幕、下载视频流')
    parser.add_argument('--room', '-r', help='直播间')
    parser.add_argument('--output', '-o', help='文件名')
    args = parser.parse_args()
    if not args.room:
        print("请传入room参数")
        exit(1)
    
    room_url = args.room if args.room.startswith("https://") else f"https://live.douyin.com/{args.room}"
    room_str = room_url.replace("https://live.douyin.com/", "")
    output_file = args.output if args.output else f"data/{room_str}.txt"
    
    ctx = asyncio.run(main(room_url))
    
    if ctx:
        logger.debug(ctx)
        wss = DyWss(ctx.wss_url, ctx.cookie_ttwid, output_file)
        wss.long_live_run()
    else:
        logger.debug("没有开播")