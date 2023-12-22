from navigo.db import get_db_internal_nodes_data_by_zone, get_poi_types, get_poi_themes
from navigo.external import get_external_data
from navigo.itinerary import compute_itinerary
from navigo.planner.models import UserData, InternalNodesData, ExternalData
from navigo.planner.scorer import compute_score
from navigo.planner.clustering import clustering_by_days
import logging

logger = logging.getLogger(__name__)

def _plan_trip(_user_input: UserData, internal_nodes_data: InternalNodesData, _external_data: ExternalData):

    logger.info("start planning trip")
    # Step 3: Scoring nodes based on user criteria
    for node in internal_nodes_data.get_all_nodes():
        try:
            if node is not None:
                node.score = compute_score(node, _user_input, _external_data)
        except Exception as e:
            logger.error(f"error while computing score for node ({node}): {e}")

    logger.info("scoring done")

    # Step 4: Divided nodes by travelling  days (clustering)
    clustering_by_days(_user_input.trip_duration, internal_nodes_data.poi_list)
    logger.info(f"clustering done")

    # Step 4: Compute the maximum points that can be visited
    max_points_by_day = 4
    max_restaurants = 2 * _user_input.trip_duration
    max_hostings = 1 * _user_input.trip_duration
    max_trails = 2 * _user_input.trip_duration

    # Step 5: Selection of top ones
    selected_poi = internal_nodes_data.select_top_points_by_day(
        _user_input.trip_duration,
        max_points_by_day)
    # logger.info(f"selected = {selected_poi}")

    first_poi = sorted(selected_poi, key=lambda x: x.score, reverse=True)[0]
    logger.info(f"first_POI = {first_poi}")

    _, selected_restaurant, selected_hosting, selected_trail, selected_toilets = internal_nodes_data.get_sorted_points()

    # Step 6: compute itinary for each days
    # itinerary, selected_toilets = compute_itinerary(
    #     first_poi, selected_poi,
    #     selected_restaurant[:max_restaurants],
    #     selected_hosting[:max_hostings],
    #     selected_trail[:max_trails],
    #     selected_toilets
    #     )
    itinerary, selected_toilets = compute_itinerary(
        first_poi, selected_poi,
        selected_restaurant,
        selected_hosting,
        selected_trail,
        selected_toilets
        )
    # after this step, itinerary is composed of POI, Restaurants, Hostings and Trails List where day and rank are used to map by day, as the order rank) 

    return itinerary, selected_toilets


def plan_trip(_user_input: UserData):

    # Step 1: Geographic Selection of POI, Restaurant, Hosting, and Trail
    # if _user_input.means_of_transport == 'by foot':
    #     rayon = 5
    # else:
    rayon = 10
    # internal_nodes_data = get_db_internal_nodes_data_by_zone(_user_input.trip_zone, rayon)
    internal_nodes_data = get_db_internal_nodes_data_by_zone(_user_input.trip_zone, rayon, _user_input.trip_duration)

    # Step 2: Fetch needed external Data
    _external_data = get_external_data(_user_input.trip_zone, _user_input.trip_start, _user_input.trip_duration, _user_input.sensitivity_to_weather)

    return _plan_trip(_user_input, internal_nodes_data, _external_data)


# Usage example with custom weights:

if __name__ == "__main__":
    # Provide the necessary input data 
    _user_input = UserData(
        favorite_poi_type_list=["museum", "park", "historical"],
        favorite_restaurant_categories=["italian", "asian"],
        favorite_hosting_categories=["hotel", "bnb"],
        sensitivity_to_weather=True,
    )
    internal_data = InternalNodesData(
        poi_list=[],
        restaurant_list=[],
        hosting_list=[],
        trail_list=[]
    )
    external_data = ExternalData(
        weather_forecast=True,
        top_poi_list=[...],  # Replace with actual data
        top_restaurant_list=[...],  # Replace with actual data
    )

    res_itinerary = plan_trip(_user_input)

    #user_input, internal_nodes_data, external_nodes_data = _plan_trip(user_input, internal_data, external_data)
