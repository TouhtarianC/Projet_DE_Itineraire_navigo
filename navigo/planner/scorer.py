# Update the ScoringRules class to allow custom weights for scoring criteria

# todo update defaults
class ScoringRules:
    def __init__(self, user_preference_weight=10, notation_weight=10, weather_weight=10):

        self.user_preference_weight = user_preference_weight
        self.notation_weight = notation_weight
        self.weather_weight = weather_weight


def compute_score(point, user_input, external_data, rules=ScoringRules()):
    score = 0

    # todo update compute_score method so it will increment the score if the point is listed in

    if point.type == "POI":
        if point.category in user_input.favorite_poi_categories:
            index = user_input.favorite_poi_categories.index(point.category)
            score += rules.user_preference_weight * (
                        len(user_input.favorite_poi_categories) - index)

    if point.type == "Restaurant":
        if point.category in user_input.favorite_restaurant_categories:
            index = user_input.favorite_restaurant_categories.index(point.category)
            score += rules.user_preference_weight * (
                        len(user_input.favorite_restaurant_categories) - index)

    if point.type == "Hosting":
        if point.category in user_input.favorite_hosting_categories:
            index = user_input.favorite_hosting_categories.index(point.category)
            score += rules.user_preference_weight * (
                        len(user_input.favorite_hosting_categories) - index)

    if point.notation > 0:
        if point.notation > user_input.minimal_notation:
            score += rules.notation_weight * (point.notation - user_input.minimal_notation)

    # todo implement me
    # if user_input.sensitivity_to_weather:
    #     weather_notation = user_input.sensitivity_to_weather[point.city]
    #     score += rules.weather_weight * weather_notation

    return score
