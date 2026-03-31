from datetime import datetime
from pydantic import BaseModel, Field


# classes regarding users
class UserCreate(BaseModel):
    username: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    ratings_count: int = 0

    class Config:
        from_attributes = True


# classes regarding movies
class MovieResponse(BaseModel):
    id: int
    tmdb_id: int
    title: str
    overview: str | None
    genres: list | None
    poster_url: str | None
    vote_average: float | None
    director_name: str | None = None
    media_type: str = "movie"

    class Config:
        from_attributes = True


class MovieSearch(BaseModel):
    tmdb_id: int
    title: str
    overview: str | None
    poster_url: str | None
    vote_average: float | None


# classes regarding ratings
class RatingCreate(BaseModel):
    user_id: int
    movie_id: int
    score: int = Field(ge=1, le=10)


class RatingResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    score: int
    created_at: datetime
    movie: MovieResponse | None = None

    class Config:
        from_attributes = True


# class recommendation
class RecommendationResponse(BaseModel):
    movies: list[MovieResponse]
    strategy: str
