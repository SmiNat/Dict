import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Setting the database
# note: the database must be created in postgresql first
database_url = os.environ.get(
    "database"
)  # schema: "postgresql://user:password@postgresserver/db"

engine = create_engine(database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Creating a database connection
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()