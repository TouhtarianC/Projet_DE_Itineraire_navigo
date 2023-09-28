from navigo.db.manager import get_db_internal_nodes_data_by_zone
from navigo.external.manager import get_external_data
from navigo.itinerary.manager import compute_itinerary
from navigo.planner.models import UserData, InternalNodesData, ExternalData
from navigo.planner.scorer import compute_score


def _plan_trip(_user_input: UserData, internal_nodes_data: InternalNodesData, _external_data: ExternalData):

    # Step 3: Scoring nodes based on user criteria
    for node in internal_nodes_data.get_all_nodes():
        node.score = compute_score(node, _user_input, _external_data)

    # Step 4: Compute the maximum points that can be visited
    max_points_to_visit = int(_user_input.trip_duration / _user_input.meantime_on_poi)

    # Step 5: Selection of top ones
    selected_poi, selected_restaurants, selected_hosting, selected_trails \
        = internal_nodes_data.select_top_points(max_points_to_visit)

    # Step 6: compute itinerary
    itinerary = compute_itinerary(selected_poi, selected_restaurants, selected_hosting, selected_trails)

    return itinerary


def plan_trip(_user_input: UserData):

    # Step 1: Geographic Selection of POI, Restaurant, Hosting, and Trail
    internal_nodes_data = get_db_internal_nodes_data_by_zone(_user_input.trip_zone)

    # Step 2: Fetch needed external Data
    _external_data = get_external_data(_user_input.trip_zone)

    return _plan_trip(_user_input, internal_nodes_data, _external_data)


# Usage example with custom weights:

if __name__ == "__main__":
    # Provide the necessary input data
    user_input = UserData(
        favorite_poi_categories=["museum", "park", "historical"],
        favorite_restaurant_categories=["italian", "asian"],
        favorite_hosting_categories=["hotel", "bnb"],
        sensitivity_to_weather=0.5,
    )
    internal_data = InternalNodesData(
        poi_list=[],
        restaurant_list=[],
        hosting_list=[],
        trail_list=[]
    )
    external_data = ExternalData(
        weather_forecast={"Paris": {"rain": False, "temperature": 25}},
        top_poi_list=[...],  # Replace with actual data
        top_restaurant_list=[...],  # Replace with actual data
    )

    _plan_trip(user_input, internal_data, external_data)

