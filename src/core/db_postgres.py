from decouple import config
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# Load variables from .env using decouple
url = URL.create(
    drivername="postgresql",
    username=config("PG_USER"),
    password=config("PG_PASSWORD"),
    host=config("PG_HOST"),
    database=config("PG_DB"),
    port=config("PG_PORT", cast=int, default=5432)
)

# Create SQLAlchemy engine
engine = create_engine(url, echo=True)  # echo=True shows queries in the console (useful for debugging)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to get the session (useful in FastAPI, Flask, etc.)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
