# Backend Architecture

## Project Structure

```
movie-recommendation/
├── .env                    # Environment variables (TMDB_API_KEY, DATABASE_URL)
├── .gitignore              # Ignores .env, __pycache__, *.db, venv/
├── requirements.txt        # Python dependencies
├── Procfile                # Heroku/Railway start command
├── railway.toml            # Railway deployment config
├── frontend/               # Static frontend files (HTML/CSS/JS)
│   ├── index.html
│   ├── app.js
│   └── style.css
└── app/                    # The FastAPI application
    ├── __init__.py          # Empty — makes `app` a Python package
    ├── config.py            # Loads env vars (TMDB_API_KEY, DATABASE_URL)
    ├── database.py          # SQLAlchemy engine, session, Base
    ├── main.py              # App entrypoint — routers, static mount
    ├── models.py            # SQLAlchemy ORM models (User, Movie, Rating)
    ├── schemas.py           # Pydantic request/response schemas
    ├── routers/             # API route handlers
    │   ├── __init__.py
    │   ├── chat.py          # POST /api/chat — the chat-based interface
    │   ├── movies.py        # GET /api/movies/* — search, popular, TV endpoints
    │   ├── ratings.py       # POST/GET /api/ratings — rate movies
    │   ├── recommendations.py  # GET /api/recommendations/{user_id}
    │   └── users.py         # POST /api/users/register, GET /api/users/{id}
    └── services/            # Business logic layer
        ├── __init__.py
        ├── tmdb.py          # TMDb API client (movies + TV)
        ├── movie_service.py # DB caching layer on top of TMDb
        └── recommendation.py# Recommendation engine
```

---

## Root Files

### `.env`
Stores secrets. Contains `TMDB_API_KEY` and optionally `DATABASE_URL`. Never committed to git.

### `requirements.txt`
Five dependencies:
- `fastapi` — the web framework
- `uvicorn` — ASGI server to run FastAPI
- `sqlalchemy` — ORM for SQLite database
- `httpx` — async HTTP client for TMDb API calls
- `python-dotenv` — loads `.env` into environment

### `Procfile` / `railway.toml`
Deployment configs. Both tell the hosting platform to run `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

---

## `app/config.py`
Loads environment variables:
- `TMDB_API_KEY` — auth key for TMDb
- `DATABASE_URL` — defaults to `sqlite:///./movies.db`

---

## `app/database.py`
Sets up SQLAlchemy:
- Creates the `engine` from `DATABASE_URL` with `check_same_thread=False` (required for SQLite + FastAPI)
- `SessionLocal` — session factory for DB connections
- `Base` — declarative base class all models inherit from
- `get_db()` — dependency injection generator; yields a session and ensures it closes
- `create_tables()` — calls `Base.metadata.create_all()` to create tables on startup

---

## `app/main.py`
The app entrypoint:
- Creates the `FastAPI` app instance (title: "Movies Recommendation API")
- Registers all 5 routers (movies, users, ratings, recommendations, chat)
- Mounts `frontend/` directory at `/static` for serving JS/CSS/HTML
- Calls `create_tables()` at module level on import
- `GET /` returns `index.html`

---

## `app/models.py`
Three SQLAlchemy ORM models:

### `User` — `users` table
- `id`, `username` (unique)
- Has many `ratings`

### `Movie` — `movies` table
- `id`, `tmdb_id`, `title`, `overview`, `genres` (JSON), `poster_url`, `vote_average`, `release_date`, `director_name`, `director_id`, `media_type`
- `UniqueConstraint("tmdb_id", "media_type")` — a movie and a TV show can share the same TMDb ID (they're different namespaces in TMDb)
- Has many `ratings`

### `Rating` — `ratings` table
- `id`, `user_id` (FK -> users), `movie_id` (FK -> movies), `score` (1-10)
- Belongs to a `User` and a `Movie`

---

## `app/schemas.py`
Pydantic models for API serialization:

- `UserCreate` — input: `username`
- `UserResponse` — output: `id`, `username`, `ratings_count`
- `MovieResponse` — output: all movie fields including `media_type`
- `MovieSearch` — lighter output for search results (no `id`, no `director_name`)
- `RatingCreate` — input: `user_id`, `movie_id`, `score` (validated 1-10)
- `RatingResponse` — output: rating with optional nested `MovieResponse`
- `RecommendationResponse` — output: list of movies + strategy string

---

## `app/routers/` — API Routes

### `chat.py` — `POST /api/chat`
The main interface. Takes `{username, message}`, returns `{reply, movies, clear_chat}`. Parses the message with exact string matching (`startswith()` / `==`) and dispatches to:
- `help` / `start` — lists all commands
- `search tv <query>` — searches TV via TMDb
- `search <query>` — searches movies via TMDb
- `rate <id> <score>` — saves a rating
- `recommend` — runs the recommendation engine
- `random tv` / `random` — discover random TV/movies
- `popular tv` / `popular` — trending TV/movies
- `reset` — deletes all user ratings
- `clear` — signals frontend to clear chat
- `my ratings` — lists user's ratings
- Fallback — "I didn't understand that" with command hints

### `movies.py` — REST endpoints for movies
- `GET /api/movies/search?query=` — search movies
- `GET /api/movies/popular` — popular movies
- `GET /api/movies/search/tv?query=` — search TV series
- `GET /api/movies/popular/tv` — popular TV series
- `GET /api/movies/{movie_id}` — get single movie by DB id

### `ratings.py` — REST endpoints for ratings
- `POST /api/ratings/` — create or update a rating (validates user and movie exist)
- `GET /api/ratings/user/{user_id}` — get all ratings for a user

### `recommendations.py` — REST endpoint for recommendations
- `GET /api/recommendations/{user_id}` — runs the scoring algorithm and returns results

### `users.py` — REST endpoints for users
- `POST /api/users/register` — creates user or returns existing (idempotent)
- `GET /api/users/{user_id}` — get user by id

---

## `app/services/` — Business Logic

### `tmdb.py` — TMDb API Client
Defines TMDb constants (`TMDB_BASE_URL`, `TMDB_IMAGE_BASE`) and provides async functions using `httpx`:

**Movie functions:**
- `search_movies(query)` — `GET /search/movie`, returns parsed list
- `get_movie_details(tmdb_id)` — `GET /movie/{id}`, returns full details with genre names
- `get_popular_movies()` — `GET /movie/popular`
- `get_random_movies()` — `GET /discover/movie` with random page (1-500)
- `get_movie_credits(tmdb_id)` — `GET /movie/{id}/credits`, extracts director from crew
- `get_director_filmography(person_id)` — `GET /person/{id}/movie_credits`, returns all movies where person directed

**TV functions:**
- `search_tv(query)` — `GET /search/tv`
- `get_tv_details(tmdb_id)` — `GET /tv/{id}`, extracts creator as director
- `get_popular_tv()` — `GET /tv/popular`
- `get_random_tv()` — `GET /discover/tv` with random page
- `get_tv_credits(tmdb_id)` — `GET /tv/{id}`, extracts `created_by[0]` as creator

**Parsers:**
- `_parse_movie(data)` — normalizes TMDb movie search result to our dict format
- `_parse_movie_details(data)` — same but for detailed endpoint (genre names instead of IDs)
- `_parse_tv(data)` — maps TV fields (`name` -> `title`, `first_air_date` -> `release_date`), sets `media_type="tv"`
- `_parse_tv_details(data)` — same for detailed TV endpoint, also extracts creator

### `movie_service.py` — Caching Layer
Sits between TMDb and the database:

- `get_or_create_movie(db, tmdb_id, data)` — looks up by `(tmdb_id, media_type)`; creates if missing; updates director if newly available. The central dedup function.
- `search_and_cache(db, query)` — searches TMDb movies, caches all results in DB, returns Movie objects
- `search_tv_and_cache(db, query)` — same for TV
- `get_details_and_cache(db, tmdb_id, media_type)` — fetches single movie/TV detail if not cached
- `get_popular_and_cache(db)` / `get_popular_tv_and_cache(db)` — caches popular movies/TV
- `get_random_and_cache(db)` / `get_random_tv_and_cache(db)` — caches random movies/TV, filters out unreleased
- `backfill_director(db, movie)` — lazily fetches director credits if missing
- `backfill_tv_creator(db, movie)` — lazily fetches TV creator if missing
- `fetch_director_movies(db, director_id, name)` — fetches a director's full filmography and caches it

### `recommendation.py` — Recommendation Engine

- `get_recommendations(db, user_id, limit=15)` — the scoring algorithm:
  1. Gets all movies rated >= 7 to build genre weights
  2. If no good ratings, falls back to top-rated movies in DB (strategy: `"popular"`)
  3. Otherwise, scores every unrated movie in DB:
     - Genre match: sum of `genre_weight` for each matching genre
     - TMDb rating boost: adds `vote_average`
  4. Sorts by score descending, returns top 15 (strategy: `"content-based"`)# movie-app
# movie-recommend
