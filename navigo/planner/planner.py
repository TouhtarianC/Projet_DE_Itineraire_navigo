from navigo.db.manager import get_db_internal_nodes_data_by_zone
from navigo.external.manager import get_external_data
from navigo.itinerary.manager import compute_itinerary
from navigo.planner.models import UserData, InternalNodesData, ExternalData
from navigo.planner.scorer import compute_score
from navigo.planner.clustering import clustering_by_days


def _plan_trip(_user_input: UserData, internal_nodes_data: InternalNodesData, _external_data: ExternalData):

    # Step 3: Scoring nodes based on user criteria
    for node in internal_nodes_data.get_all_nodes():
        try:
            node.score = compute_score(node, _user_input, _external_data)
        except Exception as e:
            print(f"error while computing score for node ({node}): {e}")

    # Step 4: Divided nodes by travelling  days (clustering)
    clustering_by_days(_user_input.trip_duration, internal_nodes_data.poi_list)
    #  print(f"poi after clustering = {internal_nodes_data}")

    # Step 4: Compute the maximum points that can be visited
    max_points_by_day = 4

    # Step 5: Selection of top ones
    selected_poi = internal_nodes_data.select_top_points_by_day(
        _user_input.trip_duration,
        max_points_by_day)
    # print(f"selected = {selected_poi}")

    first_poi = sorted(selected_poi, key=lambda x: x.score, reverse=True)[0]
    print(f"first_POI = {first_poi}")

    # Step 6: compute itinary for each days
    itinerary = compute_itinerary( \
        first_poi, selected_poi, internal_nodes_data.restaurant_list, \
        internal_nodes_data.hosting_list, internal_nodes_data.trail_list)
    # after this step, itinerary is composed of 4 lists (POI, Restaurants, Hostings, [], where day and rank are used to map by day, as the order rank) 
    
    return itinerary


def plan_trip(_user_input: UserData):

    # Step 1: Geographic Selection of POI, Restaurant, Hosting, and Trail
    if _user_input.means_of_transport == 'by foot':
        rayon = 5
    else:
        rayon = 100
    # internal_nodes_data = get_db_internal_nodes_data_by_zone(_user_input.trip_zone, rayon)
    internal_nodes_data = get_db_internal_nodes_data_by_zone(_user_input.trip_zone, rayon, _user_input.trip_duration)

    # Step 2: Fetch needed external Data
    _external_data = get_external_data(_user_input.trip_zone, _user_input.trip_start, _user_input.trip_duration)

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
