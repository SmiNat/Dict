from fastapi import FastAPI

from .database import engine
from .logging_config import configure_logging
from .models import Base
from .routers.description import router as desc_router
from .routers.word import router as word_router

configure_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Learning English", version="0.1.0")
app.include_router(desc_router)
app.include_router(word_router)
