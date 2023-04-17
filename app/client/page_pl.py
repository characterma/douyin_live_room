from playwright.sync_api import Playwright, sync_playwright
from playwright.sync_api import Page, expect
from playwright.async_api import async_playwright
from urllib.parse import urlencode, unquote_plus, urlparse, quote
from loguru import logger
from websocket import WebSocketApp
from func_timeout import func_set_timeout
from app.schema.douyin_pb2 import PushFrame, Response, ChatMessage
from app.schema.livingroom import LivingRoomContext

import hashlib
import time
import asyncio
import re
import json
import gzip
import traceback
import secrets


########### CONFIGS ##############
# fixed params
live_id = 1
aid = 6383
version_code = '180800'
webcast_sdk_version = '1.3.0'
sub_room_id = ''
sub_channel_id = ''
did_rule = 3
device_platform = 'web'
device_type = ''
ac = ''
identity = 'audience'
wss_push_did = '7200658128986916404'
#dim_log_id = '2023032013405717AD627D022E4210ED1F'

class DyPagePl:
    """
    Playwright Client for making HTTP requests
    """
    def __init__(
            self
    ):
        self.browser = None
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        
    async def start_browser(self) -> Playwright:
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(headless=True)
        return p
    
    async def close_browser(self):
        await self.browser.close()
    
    async def get_secid_by_name(self, name: str) -> str:
        """
        Returns the author
        """
        
        url = f'https://www.douyin.com/search/{quote(name)}?source=switch_tab&type=user'
        context = await self.browser.new_context(user_agent=self.user_agent)
        page = await context.new_page()
        #await page.goto('https://www.douyin.com/search/%E4%BA%A4%E4%B8%AA%E6%9C%8B%E5%8F%8B?source=switch_tab&type=user')
        await page.goto(url)
        await page.evaluate('window.scrollBy(0, 100)')
        
        sec_id = False

        try:
            await page.wait_for_selector('button:has-text("关注")')
            html = await page.locator('li.aCTzxbOJ.OPn2NCBX').first.inner_html()
            href_match = re.search(r'href=.*www\.douyin\.com/user/(.*?)\?', html)
            sec_id = href_match.group(1)
            logger.debug(f"Find user={name} , id={sec_id}")

        except Exception as e:
            traceback.print_exc()
            logger.warning(f"Could not find user {name}, error: " + str(e))
            raise e

        return sec_id
    
    # @TOOD: # 可能会弹出验证码导致失败
    async def get_living_room(self, sec_id: str) -> str:
        """
        通过作者id获取直播间url，如果没有开播返回false
        """
        url = f'https://www.douyin.com/user/{sec_id}'
        context = await self.browser.new_context(user_agent=self.user_agent)
        page = await context.new_page()
        await page.goto(url)
        room = False

        try:
            html = await page.locator('div.x2yFtBWw.Ll07vpAQ').inner_html()

            if not re.findall('直播中', html):
                raise Exception(f"User {id} Not online")

            matches = re.findall(r'https://live.douyin.com/(.*?)\?', html)
            room = matches[0]
            
            logger.debug(f"Find user={id} , roomid={room}")
        except Exception as e:
            logger.warning(
                f"Could not find livingroom for user:{sec_id}")
            raise e

        return f"https://live.douyin.com/{room}"
        
    async def get_websocket_url(self, url: str) -> LivingRoomContext:
        # Note the change below: the user agent is set while creating the page
        context = await self.browser.new_context(user_agent=self.user_agent)
        page = await context.new_page()

        await page.goto(url)
            
        # 解析页面静态内容：room_id/user_unique_id/flv等
        content = await page.content()
        data_string = re.findall(
                r'<script id="RENDER_DATA" type="application/json">(.*?)</script>', content)[0]
        data_dict = json.loads(unquote_plus(data_string))
            
        room = data_dict['app']['initialState']['roomStore']['roomInfo']['room']
        room_id = room['id_str']
        status = room['status'] # 4直播已结束，2直播中
        if status == 4:
            logger.debug(f"直播已结束: status={status}, roominfo={room}")
            return None
            
        elif not status == 2:
            logger.warning(f"未知直播状态：status={status}, roominfo={room}")
            return None
        
        user_id = data_dict['app']['odin']['user_id']
        user_unique_id = data_dict['app']['odin']['user_unique_id']
        title = room['title']
        user_count = room['stats']['user_count_str'] if 'stats' in room else ''
        total_user = room['stats']['total_user_str'] if 'stats' in room else ''
        has_commerce_goods = room['has_commerce_goods']
        owner_id = room['owner']['id_str']
        admin_user = ",".join(room['admin_user_ids_str'])
        owner_sec_uid = room['owner']['sec_uid']
        owner_nickname = room['owner']['nickname']
        
        
        # 计算 xmstub 值，实际是md5
        params = {
                'live_id': live_id,
                'aid': aid,
                'version_code': version_code,
                'webcast_sdk_version': webcast_sdk_version,
                'room_id': room_id,
                'sub_room_id': '',
                'sub_channel_id': '',
                'did_rule': did_rule,
                'user_unique_id': user_unique_id,
                'device_platform': 'web',
                'device_type': '',
                'ac': '',
                'identity': 'audience',
        }
            
        xmstub = hashlib.md5(','.join([f"{k}={v}" for k, v in params.items()]).encode('utf-8')).hexdigest()
        #logger.debug(xmstub)
            
        # 获取websocket URL的签名，传入xmstub，调用js中的函数
        signature = await page.evaluate('''() => {
                const s = {'X-MS-STUB': '%s'}
                console.log(window.byted_acrawler.frontierSign(s));
                return window.byted_acrawler.frontierSign(s);
        }''' % (xmstub))

        # 获取cookie ttwid，建立websocket需要
        signature=signature['X-Bogus']
        cookies = await context.cookies()
        cookie = ''
        for c in cookies:
            if c['name'] == 'ttwid':
                cookie = c['value']
            
        # 拼接完整的wss链接
        now = int(1000*time.time())
        ntime = time.time_ns()
        
        # 类似：2023032013405717AD627D022E4210ED1F
        dim_log_id = time.strftime("%Y%m%d%H%M%S") + secrets.token_hex(8).upper()
        
        params = {
                'app_name':                 'douyin_web',
                'version_code':             version_code,
                'webcast_sdk_version':      webcast_sdk_version,
                'update_version_code':      webcast_sdk_version,
                'compress':                 'gzip',
                'internal_ext':             f'internal_src:dim|wss_push_room_id:{room_id}|wss_push_did:{wss_push_did}|dim_log_id:{dim_log_id}|fetch_time:{now}|seq:1|wss_info:0-{now}-0-0|wrds_kvs:AudienceGiftSyncData-{ntime}_InputPanelComponentSyncData-{ntime}_WebcastRoomRankMessage-{ntime}_HighlightContainerSyncData-16_WebcastRoomStatsMessage-{ntime}',
                'host':                     'https://live.douyin.com',
                'aid':                      aid,
                'live_id':                  live_id,
                'did_rule':                 did_rule,
                'debug':                    'false',
                'maxCacheMessageNumber':    20,
                'endpoint':                 'live_pc',
                'support_wrds':             1,
                'im_path':                  '/webcast/im/fetch/',
                'user_unique_id':           user_unique_id,
                'device_platform':          'web',
                'cookie_enabled':           'true',
                'screen_width':             '2048',
                'screen_height':            '1152',
                'browser_language':         'zh-CN',
                'browser_platform':         'Win32',
                'browser_name':             'Mozilla',
                'browser_version':          '5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/111.0.0.0%20Safari/537.36',
                'browser_online':           'true',
                'tz_name':                  'Asia/Shanghai',
                'identity':                 'audience',
                'room_id':                  room_id,
                'heartbeatDuration':        0,
                'signature':                signature,
        }
            
        wss_url = '&'.join([f"{k}={v}" for k, v in params.items()])

        wss_url = f"wss://webcast3-ws-web-hl.douyin.com/webcast/im/push/v2/?{wss_url}"
        
        flv = ''
        for key in ['SD1', 'SD2', 'FULL_HD1']:
            if key in room['stream_url']['flv_pull_url']:
                flv = room['stream_url']['flv_pull_url'][key]
                break
            
        # 保存直播间上下文，后面可以入库
        ctx = LivingRoomContext(
                url=url,
                room_id=room_id,
                title=title,
                cookie_ttwid=cookie,
                flvs=room['stream_url']['flv_pull_url'],
                flv=flv,
                wss_url=wss_url,
                user_id=user_id,
                user_unique_id=user_unique_id,
                user_count=user_count,
                total_user=total_user,
                has_commerce_goods=has_commerce_goods,
                owner_id=owner_id,
                admin_user=admin_user,
                owner_sec_uid=owner_sec_uid,
                owner_nickname=owner_nickname,
            )
            
        return ctx

