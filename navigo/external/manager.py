from navigo.planner.models import ExternalData


def get_weather_forecast_by_zone(zone: int) -> dict:
    # todo Implement the logic
    return {}


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
