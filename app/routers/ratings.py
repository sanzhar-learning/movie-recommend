from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Rating, User, Movie
from app.schemas import RatingCreate, RatingResponse

router = APIRouter(prefix="/api/ratings", tags=["ratings"])


@router.post("/", response_model=RatingResponse)
def rate_movie(data: RatingCreate, db: Session = Depends(get_db)):
    if not db.query(User).filter(User.id == data.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    if not db.query(Movie).filter(Movie.id == data.movie_id).first():
        raise HTTPException(status_code=404, detail="Movie not found")

    # Update existing rating or create new
    existing = (
        db.query(Rating)
        .filter(Rating.user_id == data.user_id, Rating.movie_id == data.movie_id)
        .first()
    )
    if existing:
        existing.score = data.score
        db.commit()
        db.refresh(existing)
        return existing

    rating = Rating(user_id=data.user_id, movie_id=data.movie_id, score=data.score)
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


@router.get("/user/{user_id}", response_model=list[RatingResponse])
def get_user_ratings(user_id: int, db: Session = Depends(get_db)):
    ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
    return ratings
