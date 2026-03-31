from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Movie
from app.schemas import MovieResponse
from app.services import movie_service

router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.get("/search", response_model=list[MovieResponse])
async def search_movies(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    movies = await movie_service.search_and_cache(db, query)
    return movies


@router.get("/popular", response_model=list[MovieResponse])
async def popular_movies(db: Session = Depends(get_db)):
    movies = await movie_service.get_popular_and_cache(db)
    return movies


@router.get("/search/tv", response_model=list[MovieResponse])
async def search_tv(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    movies = await movie_service.search_tv_and_cache(db, query)
    return movies


@router.get("/popular/tv", response_model=list[MovieResponse])
async def popular_tv(db: Session = Depends(get_db)):
    movies = await movie_service.get_popular_tv_and_cache(db)
    return movies


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie
