import json
import logging

import requests
from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists

from navigo.planner.models import InternalNodesData, POI, db_raw_to_poi, db_raw_to_restaurant, db_raw_to_hosting, \
    db_raw_to_trail, db_raw_to_wc
from navigo.settings import MARIADB_USER, MARIADB_PWD, MARIADB_HOST, MARIADB_DB, MARIADB_POI_TABLE, \
    MARIADB_RESTAURANT_TABLE, MARIADB_HOSTING_TABLE, MARIADB_TRAIL_TABLE, MARIADB_WC_TABLE, \
    MIN_FETCHED_POI_BY_ZONE_PER_DAY, LOOKUP_ITERATIONS_RADIUS_INIT, MAX_LOOKUP_ITERATIONS_FOR_POINTS, \
    LOOKUP_ITERATIONS_RADIUS_STEP, MIN_FETCHED_RESTAURANT_BY_ZONE_PER_DAY, MIN_FETCHED_HOSTING_BY_ZONE_PER_DAY, \
    MIN_FETCHED_TRAIL_BY_ZONE_PER_DAY, MIN_FETCHED_WC_BY_ZONE_PER_DAY

logger = logging.getLogger(__name__)


class DBManagerException(Exception):
    pass


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


def get_nearby_communes_as_where_clause(postal_code, rayon=10) -> str:
    communes = get_nearby_communes(postal_code, rayon)
    res = "(" + ",".join(str(n) for n in communes) + ")"

    logger.info(f"restricting search in following communes: {res}")
    return res


# Connect to MariaDB
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MARIADB_USER}:{MARIADB_PWD}@{MARIADB_HOST}/{MARIADB_DB}'
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
if not database_exists(engine.url):
    msg = f'Database not found: {MARIADB_DB}'
    raise DBManagerException(msg)


def get_poi_by_zone(zone: int, days: int = 1) -> list:
    iteration = 0
    poi_list = []

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and len(poi_list) < MIN_FETCHED_POI_BY_ZONE_PER_DAY * days:
        radius = LOOKUP_ITERATIONS_RADIUS_INIT + iteration * LOOKUP_ITERATIONS_RADIUS_STEP
        logger.info(f"running iteration {iteration} to fetch POI with radius: {radius}")

        with engine.begin() as con:
            query = text(
                f"""
                SELECT * FROM {MARIADB_POI_TABLE} WHERE POSTAL_CODE in 
                {get_nearby_communes_as_where_clause(zone, radius)}
                """
            )
            res = con.execute(query)
            poi_list = [{r.meta_key: r.meta_value for r in res}]

        iteration += 1

    poi_list = [db_raw_to_poi(x) for x in poi_list]
    # logger.info(f"identified POI: {json.dumps(poi_list, indent=4)}")
    logger.info(f"identified POI: {poi_list}")
    return poi_list


def get_restaurants_by_zone(zone: int, days: int = 1) -> list:
    iteration = 0
    restaurant_list = []

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and len(restaurant_list) < MIN_FETCHED_RESTAURANT_BY_ZONE_PER_DAY * days:
        radius = LOOKUP_ITERATIONS_RADIUS_INIT + iteration * LOOKUP_ITERATIONS_RADIUS_STEP
        logger.info(f"running iteration {iteration} to fetch Restaurant with radius: {radius}")

        with engine.begin() as con:
            query = text(
                f"""
                    SELECT * FROM {MARIADB_RESTAURANT_TABLE} WHERE POSTAL_CODE in 
                    {get_nearby_communes_as_where_clause(zone, radius)}
                    """
            )
            res = con.execute(query)
            restaurant_list = [{r.meta_key: r.meta_value for r in res}]

        iteration += 1

    restaurant_list = [db_raw_to_restaurant(x) for x in restaurant_list]
    # logger.info(f"identified restaurants: {json.dumps(restaurant_list, indent=4)}")
    logger.info(f"identified POI: {restaurant_list}")
    return restaurant_list


# todo return dataclass
def get_hosting_by_zone(zone: int, days: int = 1) -> list:
    iteration = 0
    hosting_list = []

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and len(hosting_list) < MIN_FETCHED_HOSTING_BY_ZONE_PER_DAY * days:
        radius = LOOKUP_ITERATIONS_RADIUS_INIT + iteration * LOOKUP_ITERATIONS_RADIUS_STEP
        logger.info(f"running iteration {iteration} to fetch hosting with radius: {radius}")

        with engine.begin() as con:
            query = text(
                f"""
                    SELECT * FROM {MARIADB_HOSTING_TABLE} WHERE POSTAL_CODE in 
                    {get_nearby_communes_as_where_clause(zone, radius)}
                    """
            )
            res = con.execute(query)
            hosting_list = [{r.meta_key: r.meta_value for r in res}]

        iteration += 1

    hosting_list = [db_raw_to_hosting(x) for x in hosting_list]
    # logger.info(f"identified hostings: {json.dumps(hosting_list, indent=4)}")
    logger.info(f"identified hostings: {hosting_list}")
    return hosting_list


def get_trails_by_zone(zone: int, days: int = 1) -> list:
    iteration = 0
    trail_list = []

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and len(trail_list) < MIN_FETCHED_TRAIL_BY_ZONE_PER_DAY * days:
        radius = LOOKUP_ITERATIONS_RADIUS_INIT + iteration * LOOKUP_ITERATIONS_RADIUS_STEP
        logger.info(f"running iteration {iteration} to fetch trails with radius: {radius}")

        with engine.begin() as con:
            query = text(
                f"""
                    SELECT * FROM {MARIADB_TRAIL_TABLE} WHERE POSTAL_CODE in 
                    {get_nearby_communes_as_where_clause(zone, radius)}
                    """
            )
            res = con.execute(query)
            trail_list = [{r.meta_key: r.meta_value for r in res}]

        iteration += 1

    trail_list = [db_raw_to_trail(x) for x in trail_list]
    # logger.info(f"identified trails: {json.dumps(trail_list, indent=4)}")
    logger.info(f"identified trails: {trail_list}")
    return trail_list


def get_wc_by_zone(zone: int, days: int = 1) -> list:
    iteration = 0
    wc_list = []

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and len(wc_list) < MIN_FETCHED_WC_BY_ZONE_PER_DAY * days:
        radius = LOOKUP_ITERATIONS_RADIUS_INIT + iteration * LOOKUP_ITERATIONS_RADIUS_STEP
        logger.info(f"running iteration {iteration} to fetch wc with radius: {radius}")

        with engine.begin() as con:
            query = text(
                f"""
                    SELECT * FROM {MARIADB_WC_TABLE} WHERE POSTAL_CODE in 
                    {get_nearby_communes_as_where_clause(zone, radius)}
                    """
            )
            res = con.execute(query)
            wc_list = [{r.meta_key: r.meta_value for r in res}]

        iteration += 1

    wc_list = [db_raw_to_wc(x) for x in wc_list]
    # logger.info(f"identified WCs: {json.dumps(wc_list, indent=4)}")
    logger.info(f"identified WCs: {wc_list}")
    return wc_list


def get_db_internal_nodes_data_by_zone(zone: int, days: int = 1) -> InternalNodesData:
    return InternalNodesData(
        poi_list=get_poi_by_zone(zone, days),
        restaurant_list=get_restaurants_by_zone(zone, days),
        hosting_list=get_hosting_by_zone(zone, days),
        trail_list=get_trails_by_zone(zone, days)
    )

# todo delete after demo
# def get_db_internal_nodes_data_by_zone(zone: int, days: int = 1) -> InternalNodesData:
#     return InternalNodesData(
#         poi_list=[
#             POI(name="Paris", city="Paris", latitude=48.8567, longitude=2.3522, city_code=1),
#             POI(name="Marseille", city="Marseille", latitude=43.2964, longitude=5.3700, city_code=1),
#             POI(name="Lyon", city="Lyon", latitude=45.7600, longitude=4.8400, city_code=1),
#             POI(name="Toulouse", city="Toulouse", latitude=43.6045, longitude=1.4440, city_code=1),
#             POI(name="Nice", city="Nice", latitude=43.7034, longitude=7.2663, city_code=1),
#             POI(name="Nantes", city="Nantes", latitude=47.2181, longitude=-1.5528, city_code=1),
#             POI(name="Montpellier", city="Montpellier", latitude=43.6119, longitude=3.8772, city_code=1),
#             POI(name="Strasbourg", city="Strasbourg", latitude=48.5833, longitude=7.7458, city_code=1),
#             POI(name="Bordeaux", city="Bordeaux", latitude=44.8400, longitude=-0.5800, city_code=1),
#             POI(name="Lille", city="Lille", latitude=50.6278, longitude=3.0583, city_code=1),
#             POI(name="Rennes", city="Rennes", latitude=48.1147, longitude=-1.6794, city_code=1),
#             POI(name="Reims", city="Reims", latitude=49.2628, longitude=4.0347, city_code=1),
#             POI(name="Toulon", city="Toulon", latitude=43.1258, longitude=5.9306, city_code=1),
#         ],
#         restaurant_list=[],
#         hosting_list=[],
#         trail_list=[]
#     )
