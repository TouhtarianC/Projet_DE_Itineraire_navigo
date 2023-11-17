import logging

from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists

from navigo.external import get_nearby_communes
from navigo.planner.models import InternalNodesData, db_raw_to_poi, db_raw_to_restaurant, db_raw_to_hosting, \
    db_raw_to_trail, db_raw_to_wc
from navigo.settings import MARIADB_USER, MARIADB_PWD, MARIADB_HOST, MARIADB_DB, MARIADB_POI_TABLE, \
    MARIADB_RESTAURANT_TABLE, MARIADB_HOSTING_TABLE, MARIADB_TRAIL_TABLE, MARIADB_WC_TABLE, \
    MIN_FETCHED_POI_BY_ZONE_PER_DAY, MAX_LOOKUP_ITERATIONS_FOR_POINTS, \
    LOOKUP_ITERATIONS_RADIUS_STEP, MIN_FETCHED_RESTAURANT_BY_ZONE_PER_DAY, MIN_FETCHED_HOSTING_BY_ZONE_PER_DAY, \
    MIN_FETCHED_TRAIL_BY_ZONE_PER_DAY, MIN_FETCHED_WC_BY_ZONE_PER_DAY, MARIADB_POI_TYPE_TABLE, MARIADB_POI_THEME_TABLE

logger = logging.getLogger(__name__)


class DBManagerException(Exception):
    pass


def get_nearby_communes_as_where_clause(postal_code, rayon=10) -> str:
    """
    Returns a list formatted for SQL query of results from get_nearby_communes.

    Args:
        postal_code: The postal code of the commune to search for.
        rayon: The search radius in kilometers.

    Returns:
        A list (on SQL format) of postal codes.
    """
    communes = get_nearby_communes(postal_code, rayon)
    res = "(" + ",".join(str(n) for n in communes) + ", 33063" + ")" #TODO : ajout spécifique de ce code postal 33063 pour faire marcher sur Bordeaux...

    logger.info(f"restricting search in following communes: {res}")
    return res


# Connect to MariaDB
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MARIADB_USER}:{MARIADB_PWD}@{MARIADB_HOST}/{MARIADB_DB}'
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
if not database_exists(engine.url):
    msg = f'Database not found: {MARIADB_DB}'
    raise DBManagerException(msg)


def get_poi_by_zone(zone: int, rayon: int, days: int = 1) -> list:
    iteration = 0
    poi_list = []
    res_list = []
    min_nb_POI = MIN_FETCHED_POI_BY_ZONE_PER_DAY * days

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and \
            len(poi_list) < min_nb_POI:

        radius = rayon + iteration * LOOKUP_ITERATIONS_RADIUS_STEP
        logger.info(
            f"running iteration {iteration} to fetch POI with radius: {radius}")

        with engine.begin() as con:
            query = text(
                f"""
                SELECT * FROM {MARIADB_POI_TABLE} WHERE POSTAL_CODE in
                {get_nearby_communes_as_where_clause(zone, radius)}
                """
            )
            try:
                poi_list = con.execute(query)
                poi_list = poi_list.mappings().all()
            except Exception as e:
                logger.error(f"error while fetching POI: {e}")

        iteration += 1

    logger.info(f"number of POIs find = {len(poi_list)}")
    if poi_list != []:
        res_list = [db_raw_to_poi(x) for x in poi_list]
        logger.info(f"identified POI: {res_list}")
        return res_list
    else:
        return None


def get_restaurants_by_zone(zone: int, rayon: int, days: int = 1) -> list:
    iteration = 0
    restaurant_list = []
    min_nb_restau = MIN_FETCHED_RESTAURANT_BY_ZONE_PER_DAY * days

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and \
            len(restaurant_list) < min_nb_restau:

        radius = rayon + iteration * LOOKUP_ITERATIONS_RADIUS_STEP
        logger.info(
            f"running iteration {iteration} to fetch Restaurant with radius: {radius}")

        with engine.begin() as con:
            query = text(
                f"""
                SELECT * FROM {MARIADB_RESTAURANT_TABLE} WHERE POSTAL_CODE in
                {get_nearby_communes_as_where_clause(zone, radius)}
                """
            )
            try:
                restaurant_list = con.execute(query)
                restaurant_list = restaurant_list.mappings().all()
            except Exception as e:
                logger.error(f"error while fetching Restaurant: {e}")

        iteration += 1
    logger.info(f"number of Restaurants find = {len(restaurant_list)}")

    restaurant_list = [db_raw_to_restaurant(x) for x in restaurant_list]
    # logger.info(f"identified restaurants: {json.dumps(restaurant_list, indent=4)}")
    logger.info(f"identified restaurants: {restaurant_list}")
    return restaurant_list


def get_hosting_by_zone(zone: int, rayon: int, days: int = 1) -> list:
    iteration = 0
    hosting_list = []
    min_nb_hosting = MIN_FETCHED_HOSTING_BY_ZONE_PER_DAY * days

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and \
            len(hosting_list) < min_nb_hosting:

        radius = rayon + iteration * LOOKUP_ITERATIONS_RADIUS_STEP

        logger.info(
            f"running iteration {iteration} to fetch hosting with radius: {radius}")

        with engine.begin() as con:
            query = text(
                f"""
                    SELECT * FROM {MARIADB_HOSTING_TABLE} WHERE POSTAL_CODE in
                    {get_nearby_communes_as_where_clause(zone, radius)}
                    """
            )
            hosting_list = con.execute(query)
            hosting_list = hosting_list.mappings().all()

        iteration += 1

    hosting_list = [db_raw_to_hosting(x) for x in hosting_list]
    # logger.info(f"identified hostings: {json.dumps(hosting_list, indent=4)}")
    logger.info(f"identified hostings: {hosting_list}")
    return hosting_list


def get_trails_by_zone(zone: int, rayon: int, days: int = 1) -> list:
    iteration = 0
    trail_list = []
    min_nb_trail = MIN_FETCHED_TRAIL_BY_ZONE_PER_DAY * days

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and \
            len(trail_list) < min_nb_trail:

        radius = rayon + iteration * LOOKUP_ITERATIONS_RADIUS_STEP

        logger.info(
            f"running iteration {iteration} to fetch trails with radius: {radius}")

        with engine.begin() as con:
            query = text(
                f"""
                    SELECT * FROM {MARIADB_TRAIL_TABLE} WHERE POSTAL_CODE in
                    {get_nearby_communes_as_where_clause(zone, radius)}
                """
            )
            trail_list = con.execute(query)
            trail_list = trail_list.mappings().all()

        iteration += 1

    trail_list = [db_raw_to_trail(x) for x in trail_list]
    # logger.info(f"identified trails: {json.dumps(trail_list, indent=4)}")
    logger.info(f"identified trails: {trail_list}")
    return trail_list


def get_wc_by_zone(zone: int, rayon: int, days: int = 1) -> list:
    iteration = 0
    wc_list = []
    min_nb_wc = MIN_FETCHED_WC_BY_ZONE_PER_DAY * days

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and \
            len(wc_list) < min_nb_wc:

        radius = rayon + iteration * LOOKUP_ITERATIONS_RADIUS_STEP

        logger.info(
            f"running iteration {iteration} to fetch wc with radius: {radius}")

        with engine.begin() as con:
            query = text(
                f"""
                    SELECT * FROM {MARIADB_WC_TABLE} WHERE POSTAL_CODE in
                    {get_nearby_communes_as_where_clause(zone, radius)}
                """
            )
            wc_list = con.execute(query)
            wc_list = wc_list.mappings().all()

        iteration += 1

    wc_list = [db_raw_to_wc(x) for x in wc_list]
    # logger.info(f"identified WCs: {json.dumps(wc_list, indent=4)}")
    logger.info(f"identified WCs: {wc_list}")
    return wc_list


def get_db_internal_nodes_data_by_zone(zone: int, rayon: int, days: int = 1) -> InternalNodesData:
    return InternalNodesData(
        poi_list=get_poi_by_zone(zone, rayon, days),
        restaurant_list=get_restaurants_by_zone(zone, rayon, days),
        hosting_list=get_hosting_by_zone(zone, rayon, days),
        trail_list=get_trails_by_zone(zone, rayon, days)
    )


def get_poi_types() -> list:
    poi_types = []
    with engine.begin() as con:
        query = text(
            f"""SELECT * FROM {MARIADB_POI_TYPE_TABLE}"""
        )
        try:
            res = con.execute(query)
            poi_types = res.mappings().all()
        except Exception as e:
            logger.error(f"error while fetching POI types: {e}")
        # logger.info(f"res = {res_dict}")

    return poi_types


def get_poi_themes() -> list:
    poi_themes = []
    with engine.begin() as con:
        query = text(
            f"""SELECT * FROM {MARIADB_POI_THEME_TABLE}"""
        )
        try:
            res = con.execute(query)
            poi_themes = res.mappings().all()
        except Exception as e:
            logger.error(f"error while fetching POI themes: {e}")

    return poi_themes
