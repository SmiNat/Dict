from fastapi import FastAPI

from .database import engine
from .models import Base

app = FastAPI(title="Learning English", version="0.1.0")

Base.metadata.create_all(bind=engine)
