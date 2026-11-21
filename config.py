import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR=Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY=os.getenv('SECRET_KEY','dev-secret-change-this')
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL',f"sqlite:///{BASE_DIR/'instance'/'stockflow_pro.db'}").replace('postgres://','postgresql://',1)
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SESSION_COOKIE_HTTPONLY=True
    SESSION_COOKIE_SAMESITE='Lax'
    SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','0')=='1'
