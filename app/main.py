from fastapi import FastAPI

from app.whatsapp import router

from app.db.database import Base
from app.db.database import engine

# IMPORTANT
from app.db import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(router)