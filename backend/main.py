from fastapi import FastAPI

from . import models
from .database import Base, engine
from .routes.chat import router as chat_router
from .routes.dsa import router as dsa_router
from .routes.aptitude import router as aptitude_router
from .routes.interview import router as interview_router
from .routes.progress import router as progress_router
from .routes.student import router as student_router
from .routes.study_plan import router as study_plan_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(student_router)
app.include_router(chat_router)
app.include_router(dsa_router)
app.include_router(aptitude_router)
app.include_router(interview_router)
app.include_router(progress_router)
app.include_router(study_plan_router)


@app.get("/")
def home():
    return {
        "message": "Placement Copilot backend is running!"
    }
