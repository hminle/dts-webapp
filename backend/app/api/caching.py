"""Cache policy for data responses, set in one place."""

from fastapi import Response

# Browsers revalidate after 5 min; Vercel's CDN keeps a day. A deploy (the daily
# data refresh) changes the cache key, so s-maxage can safely be long.
DATA_CACHE_CONTROL = "public, max-age=300, s-maxage=86400, stale-while-revalidate=86400"


def cache_public(response: Response) -> None:
    response.headers["Cache-Control"] = DATA_CACHE_CONTROL
