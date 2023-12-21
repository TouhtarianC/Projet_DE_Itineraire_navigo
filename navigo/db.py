import logging

from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists
from sqlalchemy.orm import Session
from navigo.external import get_nearby_communes
from navigo.planner.models_DB_ORM import Poi, Trail, PoiType, PoiTheme
from navigo.planner.models import InternalNodesData, db_raw_to_poi, db_raw_to_restaurant, db_raw_to_hosting, \
    db_raw_to_trail, db_raw_to_wc
from navigo.settings import MARIADB_USER, MARIADB_PWD, MARIADB_HOST, MARIADB_DB, MARIADB_POI_TABLE, \
    MARIADB_RESTAURANT_TABLE, MARIADB_HOSTING_TABLE, MARIADB_TRAIL_TABLE, MARIADB_WC_TABLE, \
    MIN_FETCHED_POI_BY_ZONE_PER_DAY, MAX_LOOKUP_ITERATIONS_FOR_POINTS, \
    LOOKUP_ITERATIONS_RADIUS_STEP, MIN_FETCHED_RESTAURANT_BY_ZONE_PER_DAY, MIN_FETCHED_HOSTING_BY_ZONE_PER_DAY, \
    MIN_FETCHED_TRAIL_BY_ZONE_PER_DAY, MIN_FETCHED_WC_BY_ZONE_PER_DAY, MARIADB_POI_TYPE_TABLE, MARIADB_POI_THEME_TABLE

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MARIADB_USER}:{MARIADB_PWD}@{MARIADB_HOST}/{MARIADB_DB}'

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
    # format list in SQL format
    res = "(" + ",".join(str(n) for n in communes) + ")"

    logger.info(f"restricting search in following communes: {res}")
    return res

# def get_nearby_communes_by_zone(zone: int, rayon: int, days: int = 1) -> str:
#     """
#     this function is used to find a list of postal codes, and will be used the same for
#     finding POIs, Restaurants, Hostings and Trails
#     """
#     iteration = 0
#     poi_list = []
#     min_nb_POI = MIN_FETCHED_POI_BY_ZONE_PER_DAY * days

#     session = maria_connect()

#     while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and \
#             len(poi_list) < min_nb_POI:

#         radius = rayon + iteration * LOOKUP_ITERATIONS_RADIUS_STEP
#         logger.info(
#             f"running iteration {iteration} to fetch POI with radius: {radius}")

#         l_postal_code = get_nearby_communes_as_where_clause(zone, radius)
#         try:
#             poi_list = session.query(Poi).filter(
#                 Poi.POSTAL_CODE.in_(l_postal_code[1:-1].split(','))).limit(min_nb_POI * 3).all()
#         except Exception as e:
#             logger.error(f"error while fetching POI in nearby_communes: {e}")

#         iteration += 1

#     if poi_list != []:
#         return l_postal_code
#     else:
#         return None

# Connect to MariaDB
def maria_connect(URL=SQLALCHEMY_DATABASE_URI) -> Session:
    engine = create_engine(URL, echo=False)
    if not database_exists(engine.url):
        msg = f'Database not found: {MARIADB_DB}'
        raise DBManagerException(msg)

    return Session(engine)


def get_poi_by_zone(zone: int, rayon: int, days: int = 1) -> (list, list):
    """function that return a list of POI and a list of postal codes where POI are located"""
    iteration = 0
    poi_list = []
    res_list = []
    min_nb_POI = MIN_FETCHED_POI_BY_ZONE_PER_DAY * days

    session = maria_connect()

    while iteration < MAX_LOOKUP_ITERATIONS_FOR_POINTS and \
            len(poi_list) < min_nb_POI:

        radius = rayon + iteration * LOOKUP_ITERATIONS_RADIUS_STEP
        logger.info(
            f"running iteration {iteration} to fetch POI with radius: {radius}")

        l_postal_code = get_nearby_communes_as_where_clause(zone, rayon)
        # logger.info(f"l_postal_code = {l_postal_code}")
        try:
            poi_list = session.query(Poi).filter(
                Poi.POSTAL_CODE.in_(l_postal_code[1:-1].split(','))).limit(min_nb_POI * 3).all()
        except Exception as e:
            logger.error(f"error while fetching POI: {e}")
            session.close()

        iteration += 1
    logger.info(f"number of POIs find = {len(poi_list)}")
    if poi_list != []:
        res_list = [db_raw_to_poi(x) for x in poi_list]
        # logger.info(f"identified POI: {res_list}")
        session.close()
        return res_list, l_postal_code
    else:
        session.close()
        return [], []
    

def get_restaurants_by_zone(l_postal_code: list, days: int = 1) -> list:
    restaurant_list = []
    min_nb_restau = MIN_FETCHED_RESTAURANT_BY_ZONE_PER_DAY * days
    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)

    with engine.begin() as con:
        query = text(
            f"""
            SELECT * FROM {MARIADB_RESTAURANT_TABLE} WHERE POSTAL_CODE in
            {l_postal_code} 
            LIMIT {min_nb_restau * 3 }
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


def get_hosting_by_zone(l_postal_code: list, days: int = 1) -> list:
    hosting_list = []
    min_nb_hosting = MIN_FETCHED_HOSTING_BY_ZONE_PER_DAY * days
    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)

    with engine.begin() as con:
        query = text(
            f"""
                SELECT * FROM {MARIADB_HOSTING_TABLE} WHERE POSTAL_CODE in
            {l_postal_code} 
            LIMIT {min_nb_hosting * 3 }
            """
        )
        try:
            hosting_list = con.execute(query)
            hosting_list = hosting_list.mappings().all()
        except Exception as e:
            logger.error(f"error while fetching Hosting: {e}")

    logger.info(f"number of Hostings find = {len(hosting_list)}")

    hosting_list = [db_raw_to_hosting(x) for x in hosting_list]
    # logger.info(f"identified hostings: {json.dumps(hosting_list, indent=4)}")
    # logger.info(f"identified hostings: {hosting_list}")
    return hosting_list


def get_trails_by_zone(l_postal_code: list, days: int = 1) -> list:
    trail_list = []
    min_nb_trail = MIN_FETCHED_TRAIL_BY_ZONE_PER_DAY * days
    session = maria_connect()

    try:
        trail_list = session.query(Trail).filter(
            Trail.POSTAL_CODE.in_(l_postal_code[1:-1].split(','))).limit(min_nb_trail * 3).all()
    except Exception as e:
        logger.error(f"error while fetching Trail: {e}")
        session.close()
    

    if trail_list != []:
        trail_list = [db_raw_to_trail(x) for x in trail_list]
        session.close()
        return trail_list
    else:
        session.close()
        return []


def get_wc_by_zone(l_postal_code: list, days: int = 1) -> list:
    wc_list = []
    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)

    with engine.begin() as con:
        query = text(
            f"""
                SELECT * FROM {MARIADB_WC_TABLE} WHERE POSTAL_CODE in
                {l_postal_code} 
            """
        )
        wc_list = con.execute(query)
        wc_list = wc_list.mappings().all()

    wc_list = [db_raw_to_wc(x) for x in wc_list]
    # logger.info(f"identified WCs: {json.dumps(wc_list, indent=4)}")
    # logger.info(f"identified WCs: {wc_list}")
    return wc_list


def get_db_internal_nodes_data_by_zone(zone: int, rayon: int, days: int = 1) -> InternalNodesData:
    poi_list, l_postal_code = get_poi_by_zone(zone, rayon, days)

    return InternalNodesData(
        poi_list=poi_list,
        restaurant_list=get_restaurants_by_zone(l_postal_code, days),
        hosting_list=get_hosting_by_zone(l_postal_code, days),
        trail_list=get_trails_by_zone(l_postal_code, days),
        toilets_list=get_wc_by_zone(l_postal_code, days)
    )


def get_poi_types() -> list:
    poi_types = []
    session = maria_connect()
    try:
        poi_types = session.query(PoiType).all()
        # poi_types = res.mappings().all()
    except Exception as e:
        logger.error(f"error while fetching POI types: {e}")
    finally:
        session.close()
    # logger.info(f"res = {res_dict}")

    return poi_types


def get_poi_categories_of_type() -> list:
    session = maria_connect()
    poi_type_categories = set()
    try:
        res = session.query(PoiType).filter(PoiType.CATEGORY != 'Other').all()
        # logger.info(f"res = {res}")
        for t in res:
            poi_type_categories.add(t.CATEGORY)
    except Exception as e:
        logger.error(f"error while fetching categories of POI types: {e}")
    # logger.info(f"poi_type_categories = {poi_type_categories}")
    finally:
        session.close()

    return list(poi_type_categories)


def get_poi_themes() -> list:
    session = maria_connect()
    try:
        res = session.query(PoiTheme).all()
    except Exception as e:
        logger.error(f"error while fetching POI themes: {e}")
    finally:
        session.close()

    return res


def get_poi_categories_of_theme() -> list:
    session = maria_connect()
    poi_theme_categories = set()
    try:
        res = session.query(PoiTheme).filter(PoiTheme.CATEGORY != 'Other').all()
        for t in res:
            poi_theme_categories.add(t.CATEGORY)
    except Exception as e:
            logger.error(f"error while fetching categories of POI themes: {e}")
    # logger.info(f"poi_theme_categories = {poi_theme_categories}")
    finally:    
        session.close()

    return list(poi_theme_categories)


def get_restaurants_types() -> list:
    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
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
    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
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
