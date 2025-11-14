import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Načteme URL z prostředí, defaultně SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# --- ÚPRAVA KVŮLI PSYCOPG3 ---
# Pokud je v URL starý driver "psycopg2", přepíšeme ho na "psycopg"
if "psycopg2" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("psycopg2", "psycopg")

# Railway/PG často používá jen "postgres://" nebo "postgresql://"
# takže to přepíšeme na explicitní driver psycopg3
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
# --- KONEC ÚPRAVY ---

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

