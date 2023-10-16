import logging

import requests

from navigo.planner.models import ExternalData, POI, Restaurant
from navigo.settings import FOURESQUARE_API_CLIENT_ID, FOURESQUARE_API_CLIENT_SECRET, FOURESQUARE_API_URL, \
    FOURESQUARE_POI_CATEGORY_ID, FOURESQUARE_RESTAURANT_CATEGORY_ID, FOURESQUARE_API_TOKEN

logger = logging.getLogger(__name__)


def get_weather_forecast_by_zone(zone: int) -> dict:
    # todo Implement the logic
    return {}


# todo fix category IDs
# Foursquare APIs
def explore_venues(zip_code, category_id, limit, radius) -> list:
    client = requests.Session()
    client.headers['Authorization'] = FOURESQUARE_API_TOKEN

    response = client.get(
        FOURESQUARE_API_URL,
        params={
            'client_id': FOURESQUARE_API_CLIENT_ID,
            'client_secret': FOURESQUARE_API_CLIENT_SECRET,
            'v': '20220101',
            'near': zip_code,
            'categoryId': category_id,
            'limit': limit,
            # 'radius': radius,
            'sort_field': 'popularity',
            'sort_order': 'DESC',
        }
    )
    if response.status_code == 200:
        data = response.json()
        return data['results']
    else:
        logger.error(f"Error: {response.status_code}")
        logger.error(response.json())
        return []


def get_most_popular_poi_by_zone(zip_code, limit=25, radius=50000) -> list:
    raw_pois = explore_venues(zip_code, FOURESQUARE_POI_CATEGORY_ID, limit, radius)
    pois = [
        POI(
            longitude=float(result["geocodes"]["main"]["longitude"]),
            latitude=float(result["geocodes"]["main"]["latitude"]),
            city=result["location"]["locality"],
            city_code=int(result["location"]["postcode"]),
            type=result["categories"][0]["name"],
            name=result["name"].lower(),
        )
        for result in raw_pois
    ]

    return pois


def get_most_popular_restaurant_by_zone(zip_code, limit=25, radius=50000) -> list:
    raw_restaurants = explore_venues(zip_code, FOURESQUARE_RESTAURANT_CATEGORY_ID, limit, radius)
    restaurants = [
        Restaurant(
            longitude=result["geocodes"]["main"]["longitude"],
            latitude=result["geocodes"]["main"]["latitude"],
            city=result["location"]["locality"],
            city_code=int(result["location"]["postcode"]),
            type=result["categories"][0]["name"],
            name=result["name"],
        )
        for result in raw_restaurants
    ]

    return restaurants


def get_external_data(zone: int) -> ExternalData:
    return ExternalData(
        weather_forecast=get_weather_forecast_by_zone(zone),
        top_poi_list=get_most_popular_poi_by_zone(zone),
        top_restaurant_list=get_most_popular_restaurant_by_zone(zone)
    )


if __name__ == "__main__":
    from pprint import pprint
    pprint(get_external_data(33000).top_poi_list)
