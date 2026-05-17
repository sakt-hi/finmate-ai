from fastapi import FastAPI

from app.whatsapp import router

from app.db.database import engine
from app.db.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(router)


@app.get("/")
def home():

    return {
        "status": "FinMate AI Running"
    }