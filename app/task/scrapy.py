from loguru import logger
import os, requests, sys
import time
import io
import requests
from pydub import AudioSegment, silence
import subprocess
from func_timeout import func_timeout, func_set_timeout, FunctionTimedOut
from app.core.asr import transcribe_audio
from app.core.config import settings
import threading

TIME_SCRAPY = settings.TIME_SCRAPY # 真实抓取时间
#MAX_VIDEO_SIZE = settings.MAX_VIDEO_SIZE

def download_and_convert_stream(url: str, path: str):
    try:
        os.makedirs(path, exist_ok=True)
        
        # 记录下起始时间
        tm_ms = int(time.time()*1000) # ms
        with open(f"{path}/fromtime","w") as file:
            file.write(str(tm_ms))
        
        # ffmpeg -i 'http://pull-flv-l26.douyincdn.com/third/stream-112759400715256294_ld.flv?expire=642fcc87&sign=0af807f38cafe314942398f39d3ff219' -vn -ac 1 -acodec libmp3lame -f mp3 pipe: > a.mp3
        with open(f"{path}/output.mp3", 'wb') as file:
            process = subprocess.Popen(['ffmpeg', '-i', url, '-vn', '-ac', '1', '-acodec', 'libmp3lame', '-f', 'mp3', 'pipe:'], stdout=file, stdin=subprocess.PIPE)
            # 等待ffmpeg进程完成或超时
            timer = threading.Timer(TIME_SCRAPY, process.terminate)
            timer.start()
            process.communicate()
            timer.cancel()
            
    except Exception as e:
        logger.warning(f"下载异常：{e}")


# sudo apt-get install libavcodec-extra

def convert_flv_to_asr(path: str):
    """ 
    convert flv to mp3, then split mp3 into multiple segments, each segment is less than 1 minute, and split at the middle of the last silence
    # ffmpeg -i videos.flv -vn -acodec copy videos.mp3
    """
    subprocess.run(['ffmpeg', '-i', f"{path}/videos.flv", '-vn', '-ac', '1', '-acodec', 'libmp3lame', f'{path}/output.mp3'])
    # 转为mp3，后续再进行ASR
    return
    with open(f"{path}/fromtime","r") as file:
        tm_ms = int(file.read())

        # Load the MP3 file
        audio = AudioSegment.from_file(f'{path}/output.mp3')
        interval = 60 * 1000 * 10 # 10 minute
        
        segments = [audio[i:i+interval] for i in range(0, len(audio), interval)]
        records = []
        for i, segment in enumerate(segments):
            tm = tm_ms + i * interval
            segment.export(f"{path}/audio_{i}.mp3", format="mp3")
            transcribe = transcribe_audio(f"{path}/audio_{i}.mp3", 'verbose_json')
            for seg in transcribe['segments']:
                record = (tm + seg['start']*1000, 
                          tm + seg['end']*1000, 
                          seg['text'])
                records.append(record)

        with open(f"{path}/asr.txt", "w") as file:
            for record in records:
                file.write(f"{record[0]}\t{record[1]}\t{record[2]}")
                   

def process_audio(url: str, path: str):
    download_and_convert_stream(url, path)
    # convert_flv_to_asr(path)
                 
if __name__ == "__main__":
    from glob import glob
    #for d in glob("data/*"):
    download_and_convert_stream('http://pull-flv-l13.douyincdn.com/stage/stream-112846519020290488_or4.flv?expire=1682151992&sign=057ac22fbd71be53b6b9b24eb750806f',
                     'tmp')
        #convert_flv_to_asr(d)
    