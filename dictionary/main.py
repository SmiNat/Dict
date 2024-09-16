from fastapi import FastAPI

from dictionary.database import engine
from dictionary.logging_config import configure_logging
from dictionary.models import Base
from dictionary.routers.description import router as desc_router
from dictionary.routers.shuffle import router as shuffle_router
from dictionary.routers.word import router as word_router

configure_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Learning English", version="0.1.0")
app.include_router(desc_router)
app.include_router(shuffle_router)
app.include_router(word_router)
