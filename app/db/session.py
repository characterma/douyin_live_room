#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI,
                       pool_recycle=3600, pool_pre_ping=True, echo=True)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
