import requests
import pandas as pd
from dataclasses import dataclass
from datetime import datetime

from navigo.planner.models import ExternalData



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


def get_most_popular_poi_by_zone(zone: int) -> list:
    # todo Implement the logic
    return []


def get_most_popular_restaurant_by_zone(zone: int) -> list:
    # todo Implement the logic
    return []


def get_external_data(zone: int) -> ExternalData:
    return ExternalData(
        weather_forecast=get_weather_forecast_by_zone(zone),
        top_poi_list=get_most_popular_poi_by_zone(zone),
        top_restaurant_list=get_most_popular_restaurant_by_zone(zone)
    )
