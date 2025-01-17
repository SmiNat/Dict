from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from dictionary.config import config

# Setting the database
# Note: if using postgresql (like here), the database must be created in postgresql first
database_url = config.DATABASE_URL

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
