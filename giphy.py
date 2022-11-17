import os
import giphy_client
from giphy_client.rest import ApiException

API_KEY = os.getenv("GIPHY_KEY")


giphy_api = giphy_client.DefaultApi()
query = 'cheeseburgers'
options = {
    "limit": 5,
    "offset": 0,
    "rating": "g",
    "lang": "en",
    "fmt": "json"
}


def giphy(q=None):
    if not q:
        return

    try:
        gif = giphy_api.gifs_search_get(
            API_KEY,
            q,
            **options
        )
        return gif.data
    except (ApiException, ValueError):
        return []
