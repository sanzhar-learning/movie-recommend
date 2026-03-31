from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    ratings = relationship("Rating", back_populates="user")


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (UniqueConstraint("tmdb_id", "media_type"),)

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    overview = Column(Text, nullable=True)
    genres = Column(JSON, nullable=True)
    poster_url = Column(String, nullable=True)
    vote_average = Column(Float, nullable=True)
    release_date = Column(String, nullable=True)
    director_name = Column(String, nullable=True)
    director_id = Column(Integer, nullable=True)
    media_type = Column(String, default="movie")

    ratings = relationship("Rating", back_populates="movie")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    score = Column(Integer, nullable=False)

    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")
