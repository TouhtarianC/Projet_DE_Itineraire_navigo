import logging

from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists
from sqlalchemy.orm import Session
from navigo.external import get_nearby_communes
from navigo.planner.models_DB_ORM import Poi
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
    res = "(" + ",".join(str(n) for n in communes) + ")"

    logger.info(f"restricting search in following communes: {res}")
    return res

# this function is used to find a list of postal codes, and will be used the same for
# finding POIs, Restaurants, Hostings and Trails
def get_nearby_communes_by_zone(zone: int, rayon: int, days: int = 1) -> str:
    iteration = 0
    poi_list = []
    min_nb_POI = MIN_FETCHED_POI_BY_ZONE_PER_DAY * days

    session = Session(engine)

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and \
            len(poi_list) < min_nb_POI:

        radius = rayon + iteration * LOOKUP_ITERATIONS_RADIUS_STEP
        logger.info(
            f"running iteration {iteration} to fetch POI with radius: {radius}")

        query = text(
            f"""
            SELECT * FROM {MARIADB_POI_TABLE} WHERE POSTAL_CODE in
            {get_nearby_communes_as_where_clause(zone, radius)} 
            LIMIT {min_nb_POI * 3}
            """
        )
        try:
            poi_list=session.query(Poi).from_statement(query).all()
        except Exception as e:
            logger.error(f"error while fetching POI: {e}")

        iteration += 1

    if poi_list != []:
        return get_nearby_communes_as_where_clause(zone, radius)
    else:
        return None

# Connect to MariaDB
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MARIADB_USER}:{MARIADB_PWD}@{MARIADB_HOST}/{MARIADB_DB}'
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
if not database_exists(engine.url):
    msg = f'Database not found: {MARIADB_DB}'
    raise DBManagerException(msg)


def get_poi_by_zone(zone: int, rayon: int, days: int = 1) -> list:
    poi_list = []
    res_list = []
    min_nb_POI = MIN_FETCHED_POI_BY_ZONE_PER_DAY * days
    session = Session(engine)

    query = text(
        f"""
        SELECT * FROM {MARIADB_POI_TABLE} WHERE POSTAL_CODE in
        {get_nearby_communes_by_zone(zone, rayon, days)} 
        LIMIT {min_nb_POI * 3}
        """
    )
    try:
        poi_list=session.query(Poi).from_statement(query).all()
    except Exception as e:
        logger.error(f"error while fetching POI: {e}")

    logger.info(f"number of POIs find = {len(poi_list)}")
    if poi_list != []:
        res_list = [db_raw_to_poi(x) for x in poi_list]
        # logger.info(f"identified POI: {res_list}")
        return res_list
    else:
        return None
    

def get_restaurants_by_zone(zone: int, rayon: int, days: int = 1) -> list:
    restaurant_list = []
    
    with engine.begin() as con:
        query = text(
            f"""
            SELECT * FROM {MARIADB_RESTAURANT_TABLE} WHERE POSTAL_CODE in
            {get_nearby_communes_by_zone(zone, rayon, days)}
            """
        )
        try:
            restaurant_list = con.execute(query)
            restaurant_list = restaurant_list.mappings().all()
        except Exception as e:
            logger.error(f"error while fetching Restaurant: {e}")

    logger.info(f"number of Restaurants find = {len(restaurant_list)}")

    restaurant_list = [db_raw_to_restaurant(x) for x in restaurant_list]
    # logger.info(f"identified restaurants: {json.dumps(restaurant_list, indent=4)}")
    # logger.info(f"identified restaurants: {restaurant_list}")
    return restaurant_list


def get_hosting_by_zone(zone: int, rayon: int, days: int = 1) -> list:
    hosting_list = []

    with engine.begin() as con:
        query = text(
            f"""
                SELECT * FROM {MARIADB_HOSTING_TABLE} WHERE POSTAL_CODE in
                {get_nearby_communes_by_zone(zone, rayon, days)}
                """
        )
        try:
            hosting_list = con.execute(query)
            hosting_list = hosting_list.mappings().all()
        except Exception as e:
            logger.error(f"error while fetching Hosting: {e}")

    hosting_list = [db_raw_to_hosting(x) for x in hosting_list]
    # logger.info(f"identified hostings: {json.dumps(hosting_list, indent=4)}")
    # logger.info(f"identified hostings: {hosting_list}")
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
                    LIMIT {min_nb_trail * 3 }
                """
            )
            trail_list = con.execute(query)
            trail_list = trail_list.mappings().all()

        iteration += 1

    trail_list = [db_raw_to_trail(x) for x in trail_list]
    # logger.info(f"identified trails: {json.dumps(trail_list, indent=4)}")
    # logger.info(f"identified trails: {trail_list}")
    return trail_list


def get_wc_by_zone(zone: int, rayon: int, days: int = 1) -> list:
    wc_list = []
    
    with engine.begin() as con:
        query = text(
            f"""
                SELECT * FROM {MARIADB_WC_TABLE} WHERE POSTAL_CODE in
                {get_nearby_communes_by_zone(zone, rayon, days)}
            """
        )
        wc_list = con.execute(query)
        wc_list = wc_list.mappings().all()

    wc_list = [db_raw_to_wc(x) for x in wc_list]
    # logger.info(f"identified WCs: {json.dumps(wc_list, indent=4)}")
    # logger.info(f"identified WCs: {wc_list}")
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


def get_poi_categories_of_type() -> list:
    poi_type_categories = []
    with engine.begin() as con:
        query = text(
            f"""SELECT DISTINCT CATEGORY FROM {MARIADB_POI_TYPE_TABLE} WHERE CATEGORY <> 'Other' ORDER BY CATEGORY """
        )
        try:
            res = con.execute(query)
            res = res.mappings().all()
            for t in res:
                poi_type_categories.append({'NAME':t['CATEGORY']})
        except Exception as e:
            logger.error(f"error while fetching categories of POI types: {e}")
        # logger.info(f"res = {res_dict}")
    
    return poi_type_categories


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


def get_poi_categories_of_theme() -> list:
    poi_theme_categories = []
    with engine.begin() as con:
        query = text(
            f"""SELECT DISTINCT CATEGORY FROM {MARIADB_POI_THEME_TABLE} WHERE CATEGORY <> 'Other' ORDER BY CATEGORY """
        )
        try:
            res = con.execute(query)
            res = res.mappings().all()
            for t in res:
                poi_theme_categories.append({'NAME':t['CATEGORY']})
        except Exception as e:
            logger.error(f"error while fetching categories of POI themes: {e}")
        # logger.info(f"res = {res_dict}")

    return poi_theme_categories


def get_restaurants_types() -> list:
    rest_type = []
    with engine.begin() as con:
        query = text(
            f"""SELECT DISTINCT(TYPE) FROM {MARIADB_RESTAURANT_TABLE}"""
        )
        try:
            res = con.execute(query)
            rest_type = res.mappings().all()
        except Exception as e:
            logger.error(f"error while fetching restaurants types: {e}")
    return rest_type


def get_hostings_types() -> list:
    host_types = []
    with engine.begin() as con:
        query = text(
            f"""SELECT DISTINCT(TYPE) FROM {MARIADB_HOSTING_TABLE}"""
        )
        try:
            res = con.execute(query)
            host_types = res.mappings().all()
        except Exception as e:
            logger.error(f"error while fetching hostings types: {e}")
    return host_types
