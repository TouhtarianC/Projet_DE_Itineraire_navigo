from datetime import datetime
import json
import logging

import pandas as pd
import requests

from navigo.planner.models import ExternalData, POI, Restaurant
from navigo.settings import FOURESQUARE_API_CLIENT_ID, FOURESQUARE_API_CLIENT_SECRET, FOURESQUARE_API_URL, \
    FOURESQUARE_POI_CATEGORY_ID, FOURESQUARE_RESTAURANT_CATEGORY_ID, FOURESQUARE_API_TOKEN

logger = logging.getLogger(__name__)


@dataclass
class WeatherRequest:
    ville: str
    start_date: datetime
    end_date: datetime
    
def fetch_weather_data(ville):
    '''
    Fetch weather data from OpenWeatherMap API for a given city.
    Returns a DataFrame containing the raw weather data.
    '''
    KEY = "bd5e378503939ddaee76f12ad7a97608"
    url = f"https://api.openweathermap.org/data/2.5/forecast/daily?q={ville}&cnt=16&appid={KEY}&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data_dict = response.json()
        normalized_data = pd.json_normalize(data_dict).list[0]
        return pd.DataFrame(normalized_data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

def preprocess_weather_data(df):
    '''
    Preprocess the raw weather data DataFrame.
    Returns a DataFrame with relevant columns.
    '''
    df["date"] = pd.to_datetime(df["dt"], unit='s')
    df["tempRessentie"] = df["feels_like"].apply(lambda x: round(x["day"]))
    df[["idTemps", "tempsPrevu"]] = df["weather"].apply(lambda x: pd.Series((x[0]["id"], x[0]["description"])))
    df["condition"] = df.apply(lambda row: (row['idTemps'] >= 800 and 10 <= row['tempRessentie'] <= 30) or row['idTemps'] == 500, axis=1)
    return df[['date', 'tempRessentie', 'idTemps', 'tempsPrevu', 'condition']]

    
def get_weather_forecast(request: WeatherRequest):
    '''
    Function that takes a WeatherRequest object with a city name, travel start and end dates.
    Returns True if the weather is favorable during the specified period, and False otherwise.
    
    Weather is considered favorable if there is little to no rain and temperature between 10 and 30°.
    If weather data is unavailable, returns True.
    '''
    weather_data = fetch_weather_data(request.ville)
    if weather_data is None:
        return True

    print(request)
    
    preprocessed_data = preprocess_weather_data(weather_data)
    #print(preprocessed_data)
    
    end_date_recalculated = request.end_date + pd.Timedelta(days=1)
    filtered_conditions = preprocessed_data[(preprocessed_data['date'] >= request.start_date) & (preprocessed_data['date'] <= end_date_recalculated)].copy()
    filtered_conditions['filtered_date'] = filtered_conditions['date'].dt.strftime('%Y-%m-%d')
    filtered_conditions = filtered_conditions[['filtered_date', 'tempRessentie', 'idTemps', 'condition']]
    print(f"filtered_conditions :\n{filtered_conditions}")
    if filtered_conditions.empty:
        final_result = True
    else:
        final_result = all(filtered_conditions['condition'])
    
    # print(final_result)
    #print(request.start_date)
    #print(request.end_date)
    
    print(f"Résultat final : {final_result}")
    return final_result


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


################################################
# helper APIs to work with cities and zip codes
################################################

def get_nearby_communes(postal_code, rayon=10) -> list:
    """
    Returns a list of the first "top" elements from the list returned by the API villes-voisines.fr

    Args:
        postal_code: The postal code of the commune to search for.
        rayon: The search radius in kilometers.
        _top: The number of elements to return.

    Returns:
        A list of postal codes.
    """

    url = f"https://www.villes-voisines.fr/getcp.php?cp={postal_code}&rayon={rayon}"
    response = requests.get(url)
    data = json.loads(response.content)
    logger.info(f"Villes voisines: {json.dumps(data, indent=4)}")

    if isinstance(data, dict):
        communes = list(data.values())
    else:
        communes = data

    res = list(
        set(
            [int(commune["code_postal"]) for commune in communes]
        )
    )

    return res


def get_zipcode(city_name: str) -> int:
    """
    Queries the Vicopo API to get the zip code of a given city.

    Args:
        city_name: The name of the city to look for.

    Returns:
        The zip code of the city
    """

    url = f"https://vicopo.selfbuild.fr/cherche/{city_name}"
    response = requests.get(url)

    if response.status_code != 200:
        msg = f"unable to get zip code of {city_name}: {response}"
        logger.error(msg)
        raise Exception(msg)

    data = response.json()

    # return first match
    for city in data["cities"]:
        if city["city"].upper() == city_name.upper():
            return city["code"]


if __name__ == "__main__":
    print(get_zipcode('bordeaux'))
    from pprint import pprint
    pprint(get_external_data(33000).top_poi_list)
