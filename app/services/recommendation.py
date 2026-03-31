from collections import Counter
from sqlalchemy.orm import Session
from app.models import Movie, Rating


# this one gets users highly rated movies (if score >= 7)
def get_recommendations(
    db: Session, user_id: int, limit: int = 15
) -> tuple[list[Movie], str]:
    good_ratings = (
        db.query(Rating).filter(Rating.user_id == user_id, Rating.score >= 7).all()
    )

    # if user has no good ratings (yet), recommend popular movies
    if not good_ratings:
        popular = db.query(Movie).order_by(Movie.vote_average.desc()).limit(limit).all()
        return popular, "popular"

    # this one ranks genres by how much the user liked movies in them (movies with genres the user rated highly will get higher ratings),
    # then recommends movies with highest ranked genre scores, boosted by their average rating on TMDB
    genre_rank = Counter()
    rated_movie_ids = set()
    for rating in good_ratings:

        rated_movie_ids.add(rating.movie_id)
        movie = rating.movie
        if movie and movie.genres:
            for genre in movie.genres:
                genre_rank[genre] += rating.score

    # get all rated movie IDs (not just good ones) to exclude them from candidates
    all_rated = {
        r.movie_id for r in db.query(Rating).filter(Rating.user_id == user_id).all()
    }

    # score candidate movies
    candidates = db.query(Movie).filter(Movie.id.notin_(all_rated)).all()
    scored = []
    for movie in candidates:
        score = 0.0
        if movie.genres:
            for genre in movie.genres:
                score += genre_rank.get(genre, 0)
        # boost movies with higher average ratings
        if movie.vote_average:
            score += movie.vote_average
        scored.append((movie, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [m for m, _ in scored[:limit]], "content-based"
