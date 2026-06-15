from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.models import Beat, AccessRequest, Release 
from app.routers.beats import router as beats_router
from fastapi.templating import Jinja2Templates
from fastapi import Request


templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
#app.mount("/instrumentals", StaticFiles(directory="/Users/justinternois/Desktop/instrumentals"), name="instrumentals")
app.include_router(beats_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"message": "Evercurrent Beat Catalog API running"}

