from datetime import date

from sqlalchemy.orm import Session

from app.models import Movie
from app.services import tmdb


def get_or_create_movie(db: Session, tmdb_id: int, movie_data: dict) -> Movie:
    media_type = movie_data.get("media_type", "movie")
    movie = (
        db.query(Movie)
        .filter(Movie.tmdb_id == tmdb_id, Movie.media_type == media_type)
        .first()
    )
    if movie:
        if not movie.director_name and movie_data.get("director_name"):
            movie.director_name = movie_data["director_name"]
            movie.director_id = movie_data.get("director_id")
            db.commit()
            db.refresh(movie)
        return movie
    movie = Movie(
        tmdb_id=movie_data["tmdb_id"],
        title=movie_data["title"],
        overview=movie_data.get("overview"),
        genres=movie_data.get("genres"),
        poster_url=movie_data.get("poster_url"),
        vote_average=movie_data.get("vote_average"),
        release_date=movie_data.get("release_date"),
        director_name=movie_data.get("director_name"),
        director_id=movie_data.get("director_id"),
        media_type=media_type,
    )
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


async def search_and_cache(db: Session, query: str) -> list[Movie]:
    results = await tmdb.search_movies(query)
    movies = []
    for data in results:
        movie = get_or_create_movie(db, data["tmdb_id"], data)
        movies.append(movie)
    return movies


async def get_details_and_cache(
    db: Session, tmdb_id: int, media_type: str = "movie"
) -> Movie | None:
    movie = (
        db.query(Movie)
        .filter(Movie.tmdb_id == tmdb_id, Movie.media_type == media_type)
        .first()
    )
    if movie:
        return movie
    if media_type == "tv":
        data = await tmdb.get_tv_details(tmdb_id)
    else:
        data = await tmdb.get_movie_details(tmdb_id)
    if not data:
        return None
    return get_or_create_movie(db, tmdb_id, data)


async def get_popular_and_cache(db: Session) -> list[Movie]:
    results = await tmdb.get_popular_movies()
    movies = []
    for data in results:
        movie = get_or_create_movie(db, data["tmdb_id"], data)
        movies.append(movie)
    return movies


async def get_random_and_cache(db: Session) -> list[Movie]:
    results = await tmdb.get_random_movies()
    today = date.today().isoformat()
    movies = []
    for data in results:
        if data.get("release_date") and data["release_date"] > today:
            continue
        movie = get_or_create_movie(db, data["tmdb_id"], data)
        movies.append(movie)
    return movies[:15]


async def backfill_director(db: Session, movie: Movie) -> None:
    if movie.director_name:
        return
    credits = await tmdb.get_movie_credits(movie.tmdb_id)
    if credits:
        movie.director_name = credits["name"]
        movie.director_id = credits["id"]
        db.commit()


async def fetch_director_movies(
    db: Session, director_id: int, director_name: str
) -> None:
    filmography = await tmdb.get_director_filmography(director_id)
    for data in filmography:
        data["director_name"] = director_name
        data["director_id"] = director_id
        get_or_create_movie(db, data["tmdb_id"], data)


# tv series functions below, similar to movies but with some differences due to TMDB API structure and fields


async def search_tv_and_cache(db: Session, query: str) -> list[Movie]:
    results = await tmdb.search_tv(query)
    movies = []
    for data in results:
        movie = get_or_create_movie(db, data["tmdb_id"], data)
        movies.append(movie)
    return movies


async def get_popular_tv_and_cache(db: Session) -> list[Movie]:
    results = await tmdb.get_popular_tv()
    movies = []
    for data in results:
        movie = get_or_create_movie(db, data["tmdb_id"], data)
        movies.append(movie)
    return movies


async def get_random_tv_and_cache(db: Session) -> list[Movie]:
    results = await tmdb.get_random_tv()
    today = date.today().isoformat()
    movies = []
    for data in results:
        if data.get("release_date") and data["release_date"] > today:
            continue
        movie = get_or_create_movie(db, data["tmdb_id"], data)
        movies.append(movie)
    return movies[:15]


async def backfill_tv_creator(db: Session, movie: Movie) -> None:
    if movie.director_name:
        return
    credits = await tmdb.get_tv_credits(movie.tmdb_id)
    if credits:
        movie.director_name = credits["name"]
        movie.director_id = credits["id"]
        db.commit()
