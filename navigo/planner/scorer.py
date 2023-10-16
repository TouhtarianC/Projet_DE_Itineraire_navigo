# Update the ScoringRules class to allow custom weights for scoring criteria
from navigo.planner.models import GeospatialPoint, UserData, ExternalData


# todo update defaults
class ScoringRules:
    def __init__(self, user_preference_weight=10, popularity_weight=10, notation_weight=10, weather_weight=10):

        self.user_preference_weight = user_preference_weight
        self.popularity_weight = popularity_weight
        self.notation_weight = notation_weight
        self.weather_weight = weather_weight


def compute_score(point: GeospatialPoint, user_input: UserData, external_data: ExternalData, rules=ScoringRules()):
    score = 0

    if point.type == "POI":
        # boost user preferences
        if point.category.lower() in user_input.favorite_poi_categories:
            index = user_input.favorite_poi_categories.index(point.category)
            score += rules.user_preference_weight * (
                        len(user_input.favorite_poi_categories) - index)

        # boost most popular POI
        if point.name.lower() in [p.name for p in external_data.top_poi_list]:
            index = next((i for i, p in enumerate(external_data.top_poi_list) if p.name == point.name.lower()))
            score += rules.popularity_weight * (
                    len(external_data.top_poi_list) - index)

    if point.type == "Restaurant":
        # boost user preferences
        if point.category.lower() in user_input.favorite_restaurant_categories:
            index = user_input.favorite_restaurant_categories.index(point.category)
            score += rules.user_preference_weight * (
                        len(user_input.favorite_restaurant_categories) - index)

        # boost most popular POI
        if point.name.lower() in [p.name for p in external_data.top_restaurant_list]:
            index = next((i for i, p in enumerate(external_data.top_restaurant_list) if p.name == point.name.lower()))
            score += rules.popularity_weight * (
                    len(external_data.top_restaurant_list) - index)

    if point.type == "Hosting":
        # boost user preferences
        if point.category.lower() in user_input.favorite_hosting_categories:
            index = user_input.favorite_hosting_categories.index(point.category)
            score += rules.user_preference_weight * (
                        len(user_input.favorite_hosting_categories) - index)

    # boost notation
    if point.notation > 0:
        if point.notation > user_input.minimal_notation:
            score += rules.notation_weight * (point.notation - user_input.minimal_notation)

    # boost weather
    if user_input.sensitivity_to_weather:
        weather_notation = external_data.weather_forecast.get(point.city.lower(), {}).get('score', 0)
        score += rules.weather_weight * weather_notation

    return score
