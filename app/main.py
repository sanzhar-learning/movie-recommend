from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import create_tables
from app.routers import movies, users, ratings, recommendations, chat

app = FastAPI(title="Movies Recommendation API", version="1.0.0")

app.include_router(movies.router)
app.include_router(users.router)
app.include_router(ratings.router)
app.include_router(recommendations.router)
app.include_router(chat.router)

frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

create_tables()


@app.get("/")
def root():
    return FileResponse(str(frontend_dir / "index.html"))
