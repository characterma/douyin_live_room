import openai
from loguru import logger
import random, os
from dotenv import load_dotenv
import requests
from app.core.config import settings

load_dotenv()

prompt = "这份记录是一个直播间的对话，直播间的人正在销售讲解产品的卖点，同时也会回应弹幕上用户的提问。请将标点、停顿词都加上，例如：价格多少钱呢？六十九块九，就是你买短袖的价格，把外套带回去。而且有IP的。是的。"
format = 'verbose_json' # text, srt, verbose_json, vtt

def transcribe_audio(filename, format):
    key = random.choice(os.getenv('OPENAI_KEYS').split(','))
    openai.api_key = key
    logger.debug(f"use key: {key}")
    with open(filename, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", 
                                   audio_file,
                                   api_key=key,
                                   prompt=prompt,
                                   response_format=format,
                                   language='Chinese')
    
        return transcript
    
    return False

def transcribe_remote(filename, format):
    url = settings.TRANSCRIBE_PROXY_QUERY + f"?format={format}"
    with open(filename, "rb") as audio_file:
        response = requests.post(url, files={'file': audio_file})
        return response.content
    

if __name__ == '__main__':
    transcript = transcribe_remote("data/7215831026495523639/output.mp3",
                                   'srt')
    print(transcript)