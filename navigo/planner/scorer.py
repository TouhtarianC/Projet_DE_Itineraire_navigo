# Update the ScoringRules class to allow custom weights for scoring criteria
import difflib
import string

from navigo.planner.models import GeospatialPoint, UserData, ExternalData


# todo update defaults
class ScoringRules:
    def __init__(self, user_preference_weight=10, popularity_weight=10, notation_weight=10, weather_weight=10):

        self.user_preference_weight = user_preference_weight
        self.popularity_weight = popularity_weight
        self.notation_weight = notation_weight
        self.weather_weight = weather_weight


def is_internal_activity(activity_type_name: str):
    """
    return true if activity_type_name is considered as internal activity
    """
    # todo define internal activity types here
    internal_activities_types = []

    return activity_type_name in internal_activities_types


def is_jaccard_similar_name(name1, name2, limit=0.5):
    """
     Use Jaccard similarity to tell if two names are similar
    """
    name1 = name1.lower()
    name2 = name2.lower()

    # Remove punctuation from both restaurant names
    name1 = name1.translate(str.maketrans('', '', string.punctuation))
    name2 = name2.translate(str.maketrans('', '', string.punctuation))

    # Tokenize both restaurant names
    name1_tokens = name1.split()
    name2_tokens = name2.split()

    # Calculate the Jaccard similarity between the tokenized restaurant names
    jaccard_similarity = difflib.SequenceMatcher(None, name1_tokens, name2_tokens).ratio()

    return jaccard_similarity >= limit


def compute_score(point: GeospatialPoint, user_input: UserData, external_data: ExternalData, rules=ScoringRules()):
    score = 10

    if point.type == "POI":
        # boost user preferences
        if point.category.lower() in user_input.favorite_poi_type_list:
            index = user_input.favorite_poi_type_list.index(point.category)
            score += rules.user_preference_weight * (
                        len(user_input.favorite_poi_type_list) - index)

        # boost most popular POI
        for i, poi in external_data.top_poi_list:
            if is_jaccard_similar_name(point.name, poi.name):
                score += rules.popularity_weight * (len(external_data.top_poi_list) - i)
                break

        # boost external activities if weather is good else internal
        if user_input.sensitivity_to_weather:
            if external_data.weather_forecast:
                if not is_internal_activity(point.category.lower()):
                    score += rules.weather_weight

            else:
                if is_internal_activity(point.category.lower()):
                    score += rules.weather_weight

    if point.type == "Restaurant":
        # boost user preferences
        if point.category.lower() in user_input.favorite_restaurant_categories:
            index = user_input.favorite_restaurant_categories.index(point.category)
            score += rules.user_preference_weight * (
                        len(user_input.favorite_restaurant_categories) - index)

        # boost most popular POI
        for i, resto in external_data.top_restaurant_list:
            if is_jaccard_similar_name(point.name, resto.name):
                score += rules.popularity_weight * (len(external_data.top_restaurant_list) - i)
                break

    if point.type == "Hosting":
        # boost user preferences
        if point.category.lower() in user_input.favorite_hosting_categories:
            index = user_input.favorite_hosting_categories.index(point.category)
            score += rules.user_preference_weight * (
                        len(user_input.favorite_hosting_categories) - index)

    # # boost notation
    # if point.notation > 0:
    #     if point.notation > user_input.minimal_notation:
    #         score += rules.notation_weight * (point.notation - user_input.minimal_notation)

    return score
