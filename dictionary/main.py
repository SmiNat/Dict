from fastapi import FastAPI

from .crud import router
from .database import engine
from .logging_config import configure_logging
from .models import Base

configure_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Learning English", version="0.1.0")
app.include_router(router)
