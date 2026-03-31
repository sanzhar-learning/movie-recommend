import random

import httpx

from app.config import TMDB_API_KEY

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


async def search_movies(query: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={"api_key": TMDB_API_KEY, "query": query, "language": "en-US"},
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    return [_parse_movie(m) for m in results[:20]]


async def get_movie_details(tmdb_id: int) -> dict | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}",
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return _parse_movie_details(resp.json())


async def get_popular_movies() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/movie/popular",
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    return [_parse_movie(m) for m in results[:20]]


async def get_random_movies() -> list[dict]:
    page = random.randint(1, 500)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/discover/movie",
            params={
                "api_key": TMDB_API_KEY,
                "language": "en-US",
                "sort_by": "popularity.desc",
                "page": page,
            },
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    return [_parse_movie(m) for m in results[:20]]


def _parse_movie(data: dict) -> dict:
    poster = None
    if data.get("poster_path"):
        poster = f"{TMDB_IMAGE_BASE}{data['poster_path']}"
    return {
        "tmdb_id": data["id"],
        "title": data.get("title", ""),
        "overview": data.get("overview", ""),
        "genres": data.get("genre_ids", []),
        "poster_url": poster,
        "vote_average": data.get("vote_average", 0),
        "release_date": data.get("release_date", ""),
    }


async def get_movie_credits(tmdb_id: int) -> dict | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits",
            params={"api_key": TMDB_API_KEY},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        for member in data.get("crew", []):
            if member.get("job") == "Director":
                return {"name": member["name"], "id": member["id"]}
    return None


async def get_director_filmography(person_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/person/{person_id}/movie_credits",
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
        )
        resp.raise_for_status()
        data = resp.json()
        movies = []
        for item in data.get("crew", []):
            if item.get("job") == "Director":
                movies.append(_parse_movie(item))
        return movies


def _parse_movie_details(data: dict) -> dict:
    poster = None
    if data.get("poster_path"):
        poster = f"{TMDB_IMAGE_BASE}{data['poster_path']}"
    genres = [g["name"] for g in data.get("genres", [])]
    return {
        "tmdb_id": data["id"],
        "title": data.get("title", ""),
        "overview": data.get("overview", ""),
        "genres": genres,
        "poster_url": poster,
        "vote_average": data.get("vote_average", 0),
        "release_date": data.get("release_date", ""),
    }


# TV show parsing is separate because the fields are different, for example "name" instead of "title",
# "first_air_date" instead of "release_date", and no director info in search results (TMDB doesn't return it for TV shows at all, so we have to get it from credits endpoint)


def _parse_tv(data: dict) -> dict:
    poster = None
    if data.get("poster_path"):
        poster = f"{TMDB_IMAGE_BASE}{data['poster_path']}"
    return {
        "tmdb_id": data["id"],
        "title": data.get("name", ""),
        "overview": data.get("overview", ""),
        "genres": data.get("genre_ids", []),
        "poster_url": poster,
        "vote_average": data.get("vote_average", 0),
        "release_date": data.get("first_air_date", ""),
        "media_type": "tv",
    }


def _parse_tv_details(data: dict) -> dict:
    poster = None
    if data.get("poster_path"):
        poster = f"{TMDB_IMAGE_BASE}{data['poster_path']}"
    genres = [g["name"] for g in data.get("genres", [])]
    creator = data.get("created_by", [])
    director_name = creator[0]["name"] if creator else None
    director_id = creator[0]["id"] if creator else None
    return {
        "tmdb_id": data["id"],
        "title": data.get("name", ""),
        "overview": data.get("overview", ""),
        "genres": genres,
        "poster_url": poster,
        "vote_average": data.get("vote_average", 0),
        "release_date": data.get("first_air_date", ""),
        "media_type": "tv",
        "director_name": director_name,
        "director_id": director_id,
    }


async def search_tv(query: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/search/tv",
            params={"api_key": TMDB_API_KEY, "query": query, "language": "en-US"},
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    return [_parse_tv(m) for m in results[:20]]


async def get_tv_details(tmdb_id: int) -> dict | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/tv/{tmdb_id}",
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return _parse_tv_details(resp.json())


async def get_popular_tv() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/tv/popular",
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    return [_parse_tv(m) for m in results[:20]]


async def get_random_tv() -> list[dict]:
    page = random.randint(1, 500)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/discover/tv",
            params={
                "api_key": TMDB_API_KEY,
                "language": "en-US",
                "sort_by": "popularity.desc",
                "page": page,
            },
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    return [_parse_tv(m) for m in results[:20]]


async def get_tv_credits(tmdb_id: int) -> dict | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TMDB_BASE_URL}/tv/{tmdb_id}",
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        creators = data.get("created_by", [])
        if creators:
            return {"name": creators[0]["name"], "id": creators[0]["id"]}
    return None
