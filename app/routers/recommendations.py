from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import RecommendationResponse
from app.services.recommendation import get_recommendations

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/{user_id}", response_model=RecommendationResponse)
def recommend(user_id: int, db: Session = Depends(get_db)):
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    movies, strategy = get_recommendations(db, user_id)
    return RecommendationResponse(movies=movies, strategy=strategy)
