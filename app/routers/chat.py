from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Movie, Rating
from app.services import movie_service
from app.services.recommendation import get_recommendations

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    username: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    movies: list[dict] = []
    clear_chat: bool = False


def _get_or_create_user(db: Session, username: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _format_movie(movie) -> dict:
    return {
        "id": movie.id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "overview": movie.overview,
        "poster_url": movie.poster_url,
        "vote_average": movie.vote_average,
        "genres": movie.genres,
    }


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    user = _get_or_create_user(db, req.username)
    msg = req.message.strip().lower()

    # Help
    if msg in ("help", "/help", "start", "/start"):
        return ChatResponse(
            reply=(
                f"Hey {user.username}! I'm your movie & TV assistant. Here's what I can do:\n\n"
                "**Movies:**\n"
                "- **search <title>** — Search for movies\n"
                "- **random** — Get 15 random movies\n"
                "- **popular** — See trending movies\n\n"
                "**TV Series:**\n"
                "- **search tv <title>** — Search for TV series\n"
                "- **random tv** — Get 15 random TV series\n"
                "- **popular tv** — See trending TV series\n\n"
                "**General:**\n"
                "- **rate <id> <score>** — Rate a movie or TV series (1-10)\n"
                "- **recommend** — Get personalized recommendations\n"
                "- **my ratings** — View your ratings\n"
                "- **reset** — Clear all ratings & reset recommendations\n"
                "- **clear** — Clear chat history\n"
                "- **help** — Show this message"
            )
        )

    # Search TV
    if msg.startswith("search tv "):
        query = msg[10:].strip()
        movies = await movie_service.search_tv_and_cache(db, query)
        if not movies:
            return ChatResponse(
                reply=f'No TV series found for "{query}". Try a different title.'
            )
        movie_list = [_format_movie(m) for m in movies[:15]]
        lines = [f'Found {len(movie_list)} TV results for "{query}":\n']
        for m in movie_list:
            stars = f"⭐ {m['vote_average']:.1f}" if m["vote_average"] else ""
            lines.append(f"**{m['title']}** (ID: {m['id']}) {stars}")
        return ChatResponse(reply="\n".join(lines), movies=movie_list)

    # Search
    if msg.startswith("search "):
        query = msg[7:].strip()
        movies = await movie_service.search_and_cache(db, query)
        if not movies:
            return ChatResponse(
                reply=f'No movies found for "{query}". Try a different title.'
            )
        movie_list = [_format_movie(m) for m in movies[:15]]
        lines = [f'Found {len(movie_list)} results for "{query}":\n']
        for m in movie_list:
            stars = f"⭐ {m['vote_average']:.1f}" if m["vote_average"] else ""
            lines.append(f"**{m['title']}** (ID: {m['id']}) {stars}")
        return ChatResponse(reply="\n".join(lines), movies=movie_list)

    # Rate
    if msg.startswith("rate "):
        parts = msg.split()
        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            movie_id = int(parts[1])
            score = int(parts[2])
            if score < 1 or score > 10:
                return ChatResponse(reply="Score must be between 1 and 10.")
            movie = db.query(Movie).filter(Movie.id == movie_id).first()
            if not movie:
                return ChatResponse(
                    reply=f"Movie with ID {movie_id} not found. Search for it first!"
                )
            existing = (
                db.query(Rating)
                .filter(Rating.user_id == user.id, Rating.movie_id == movie_id)
                .first()
            )
            if existing:
                existing.score = score
            else:
                db.add(Rating(user_id=user.id, movie_id=movie_id, score=score))
            db.commit()
            return ChatResponse(
                reply=f"Rated **{movie.title}** with score **{score}/10**!"
            )

    # Recommend
    if msg == "recommend":
        movies, strategy = get_recommendations(db, user.id)
        if not movies:
            return ChatResponse(reply="No recommendations yet. Rate some movies first!")
        movie_list = [_format_movie(m) for m in movies[:15]]
        strategy_text = (
            "Based on your taste" if strategy == "content-based" else "Popular picks"
        )
        lines = [f"{strategy_text}:\n"]
        for m in movie_list:
            stars = f"⭐ {m['vote_average']:.1f}" if m["vote_average"] else ""
            lines.append(f"**{m['title']}** (ID: {m['id']}) {stars}")
        return ChatResponse(reply="\n".join(lines), movies=movie_list)

    # Random TV
    if msg == "random tv":
        movies = await movie_service.get_random_tv_and_cache(db)
        if not movies:
            return ChatResponse(reply="Couldn't fetch random TV series. Try again!")
        movie_list = [_format_movie(m) for m in movies]
        lines = ["Here are 15 random TV series:\n"]
        for m in movie_list:
            stars = f"⭐ {m['vote_average']:.1f}" if m["vote_average"] else ""
            lines.append(f"**{m['title']}** (ID: {m['id']}) {stars}")
        return ChatResponse(reply="\n".join(lines), movies=movie_list)

    # Random
    if msg == "random":
        movies = await movie_service.get_random_and_cache(db)
        if not movies:
            return ChatResponse(reply="Couldn't fetch random movies. Try again!")
        movie_list = [_format_movie(m) for m in movies]
        lines = ["Here are 15 random movies:\n"]
        for m in movie_list:
            stars = f"⭐ {m['vote_average']:.1f}" if m["vote_average"] else ""
            lines.append(f"**{m['title']}** (ID: {m['id']}) {stars}")
        return ChatResponse(reply="\n".join(lines), movies=movie_list)

    # Popular TV
    if msg == "popular tv":
        movies = await movie_service.get_popular_tv_and_cache(db)
        movie_list = [_format_movie(m) for m in movies[:15]]
        lines = ["Trending TV series right now:\n"]
        for m in movie_list:
            stars = f"⭐ {m['vote_average']:.1f}" if m["vote_average"] else ""
            lines.append(f"**{m['title']}** (ID: {m['id']}) {stars}")
        return ChatResponse(reply="\n".join(lines), movies=movie_list)

    # Popular
    if msg == "popular":
        movies = await movie_service.get_popular_and_cache(db)
        movie_list = [_format_movie(m) for m in movies[:15]]
        lines = ["Trending movies right now:\n"]
        for m in movie_list:
            stars = f"⭐ {m['vote_average']:.1f}" if m["vote_average"] else ""
            lines.append(f"**{m['title']}** (ID: {m['id']}) {stars}")
        return ChatResponse(reply="\n".join(lines), movies=movie_list)

    # Reset recommendations (clear all ratings)
    if msg == "reset":

        ratings = db.query(Rating).filter(Rating.user_id == user.id).all()
        if not ratings:
            return ChatResponse(reply="You have no ratings to reset.")
        count = len(ratings)
        db.query(Rating).filter(Rating.user_id == user.id).delete()
        db.commit()
        return ChatResponse(
            reply=f"All {count} rating(s) cleared! Your recommendations have been reset. Rate some movies to get new personalized suggestions."
        )

    # Clear chat
    if msg == ("clear"):
        return ChatResponse(reply="Chat cleared!", clear_chat=True)

    # My ratings
    if msg == "my ratings":
        ratings = db.query(Rating).filter(Rating.user_id == user.id).all()
        if not ratings:
            return ChatResponse(
                reply="You haven't rated any movies yet. Search for a movie and rate it!"
            )
        lines = ["Your ratings:\n"]
        for r in ratings:
            lines.append(f"**{r.movie.title}** — {r.score}/10")
        return ChatResponse(reply="\n".join(lines))

    # error response
    return ChatResponse(
        reply=(
            "I didn't understand that. Try:\n"
            "- **search <title>** to find movies\n"
            "- **search tv <title>** to find TV series\n"
            "- **rate <id> <score>** to rate a movie or TV series\n"
            "- **recommend** for suggestions\n"
            "- **random** / **random tv** for random picks\n"
            "- **popular** / **popular tv** for trending\n"
            "- **help** for all commands"
        )
    )
