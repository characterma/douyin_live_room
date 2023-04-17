from app.schema.douyin_pb2 import PushFrame, Response, ChatMessage, LiveShoppingMessage
import requests
from websocket import WebSocketApp
import gzip
from loguru import logger
import time, traceback
from app.core.config import settings
import threading

class DyWss:
    def __init__(self, wss_url: str, ttwid: str, output_file: str) -> None:
        self.__wss_url = wss_url
        self.__ttwid = ttwid
        self.__ws = None
        self.__output_file = open(output_file, 'a', encoding='utf-8')
    
    def long_live_run(self):
        def on_open(ws):
            pass

        def on_message(ws, content):
            try:
                frame = PushFrame()
                frame.ParseFromString(content)

                # 消息默认是compressed
                origin_bytes = gzip.decompress(frame.payload)

                response = Response()
                response.ParseFromString(origin_bytes)

                if response.needAck:
                    s = PushFrame()
                    s.payloadType = "ack"
                    s.payload = response.internalExt.encode('utf-8')
                    s.logId = frame.logId

                    ws.send(s.SerializeToString())

                info = ''
                # 获取数据内容（需根据不同method，使用不同的结构对象对 数据 进行解析）
                #   注意：此处只处理 WebcastChatMessage ，其他处理方式都是类似的。
                for item in response.messagesList:
                    info = ""
                    now = round(time.time(),3)
                    if item.method == 'WebcastLiveShoppingMessage':
                        message = LiveShoppingMessage()
                        message.ParseFromString(item.payload)
                        for id in message.updatedProductIdsList:
                            info = f"##system: {id}"
                    
                    elif item.method == "WebcastChatMessage":
                        message = ChatMessage()
                        message.ParseFromString(item.payload)
                        
                        user_info = "|".join([str(x) for x in [
                            message.user.nickName,
                            #message.user.id,
                            message.user.shortId,
                            #message.user.Birthday,
                            #message.user.Telephone,
                            #message.user.city,
                            #message.user.createTime,
                            #message.user.modifyTime,
                            #message.user.displayId,
                            message.user.secUid,
                            #message.user.locationCity,
                            #message.user.webcastUid,
                            #message.user.idStr,
                            #message.user.isFollower,
                            #message.user.isFollowing,
                            #message.user.watchDurationMonth,
                        ]])
                        info = f"{now}\t{user_info}\t{message.content}"

                    if info:
                        self.__output_file.writelines(f"{info}\n")
                        self.__output_file.flush()
                        logger.debug(info)
                        
            except Exception as e:
                traceback.print_exc()
                logger.warning(f"On message, error: " + str(e))

                
        def on_error(ws, exception):
            logger.error(f"on_error, {ws}, {exception}")

        def on_close(ws, code, msg):
            pass
        
        def stop_ws(ws):
            ws.close()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Host": "webcast3-ws-web-lq.douyin.com",
            "Origin": "https://live.douyin.com",
        }

        #logger.debug(f"开始连接：ROOMID={room_id}, TITLE={room_title}, ONLINE={room_user_count}")

        ws = WebSocketApp(
            url=self.__wss_url,
            header=headers,
            cookie=f"ttwid={self.__ttwid}",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        timer = threading.Timer(settings.TIME_SCRAPY, stop_ws, args=[ws])
        timer.start()
        ws.run_forever(ping_timeout=settings.TIME_SCRAPY)
        timer.cancel()
        
"""
admin_user='106026337492,338294944308811,4495236267512808,97578969906,95732484712,78020098692,61357556537,2053505270426884,320702945167043,817638982558968,111476110222,95615655903,804431450617166,106795141704,85602294385,106802589239,2532922139621262,58807619987,64460695580,2278642155262111,69439711480,93582331218,4284164015660536,1574141479646223,64196394451,2752775952279799,50572102397,3606000512009291,104968687453,34779148590751,111105813643,97799257107,51817612639,980403136773965,3246200664893823,68036295187,470201054799819,2938333818010299,3412531880662112,94349580053,93507671473,202752560731454,61740258729'
"""