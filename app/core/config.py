import secrets

from dotenv import load_dotenv
import os

from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl, AnyUrl, validator
import openai
from loguru import logger


class Config(BaseSettings):
    PROJECT_NAME: str = "livescrapy"
    SERVER_NAME: str = ''
    SERVER_HOST: AnyHttpUrl = 'http://localhost'
    API_V1_STR: str = "/api/v1"

    CHAT_PROXY_QUERY: str = "http://43.206.30.168:10089/ask"
    EMBEDDING_PROXY_QUERY: str = "http://43.206.30.168:10089/embedding"
    TRANSCRIBE_PROXY_QUERY: str = "http://43.206.30.168:10089/transcribe"
    
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    TIME_SCRAPY: int = 60*60 # 真实抓取时间
    MAX_THREADS: int = 100 # 最大线程数
    MAX_VIDEO_SIZE: int = 1024*1024*400 # 最大视频大小,300MB 约等于 60分钟

    load_dotenv()
    SQLALCHEMY_DATABASE_URI: Optional[AnyUrl] = os.getenv('DATABASE')
    
    # URLS_FILE: str = 'urls.txt'
    URLS_FILE: str = '../urls.txt'

    format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} {line} | {elapsed} | {message}"
    logger.add('logs/livews-{time:YYYYMMDD}.log',
               rotation='00:00', catch=True, enqueue=True,
               encoding='utf-8',
               format=format)

settings = Config()
