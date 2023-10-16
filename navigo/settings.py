from decouple import config

# neo4j settings
# NEO4J_URI = config('NEO4J_URI', default="bolt://localhost:7687", cast=str)
NEO4J_URI = config('NEO4J_URI', default="bolt://localhost:7687", cast=str)
NEO4J_USER = config('NEO4J_USER', default="neo4j", cast=str)
NEO4J_PWD = config('NEO4J_PWD', default="neo4jneo4j", cast=str)


# neo4j settings
MARIADB_HOST = config('MARIADB_HOST', default="localhost:3306", cast=str)
MARIADB_USER = config('MARIADB_USER', default="root", cast=str)
MARIADB_PWD = config('MARIADB_PWD', default="", cast=str)
MARIADB_DB = config('MARIADB_DB', default="exploreit", cast=str)

MARIADB_HOSTING_TABLE = config('MARIADB_HOSTING_TABLE', default="hostings", cast=str)
MARIADB_WC_TABLE = config('MARIADB_WC_TABLE', default="wcs", cast=str)
MARIADB_RESTAURANT_TABLE = config('MARIADB_RESTAURANT_TABLE', default="restaurants", cast=str)
MARIADB_POI_TABLE = config('MARIADB_POI_TABLE', default="poi", cast=str)
MARIADB_TRAIL_TABLE = config('MARIADB_TRAIL_TABLE', default="trails", cast=str)


# mongodb settings
MONGODB_URI = config('MONGODB_URI', default="mongodb://localhost/", cast=str)
MONGODB_DB = config('MONGODB_DB', default="exploreit", cast=str)

MONGODB_HOSTING_COLLECTION = config('MONGODB_HOSTING_COLLECTION', default="hostings", cast=str)
MONGODB_WC_COLLECTION = config('MONGODB_WC_COLLECTION', default="wcs", cast=str)
MONGODB_RESTAURANT_COLLECTION = config('MONGODB_RESTAURANT_COLLECTION', default="restaurants", cast=str)

MIN_FETCHED_HOSTING_BY_ZONE_PER_DAY = config('MIN_FETCHED_HOSTING_BY_ZONE_PER_DAY', default=5, cast=int)
MIN_FETCHED_WC_BY_ZONE_PER_DAY = config('MIN_FETCHED_WC_BY_ZONE_PER_DAY', default=5, cast=int)
MIN_FETCHED_RESTAURANT_BY_ZONE_PER_DAY = config('MIN_FETCHED_RESTAURANT_BY_ZONE_PER_DAY', default=5, cast=int)
MIN_FETCHED_POI_BY_ZONE_PER_DAY = config('MIN_FETCHED_POI_BY_ZONE_PER_DAY', default=10, cast=int)
MIN_FETCHED_TRAIL_BY_ZONE_PER_DAY = config('MIN_FETCHED_TRAIL_BY_ZONE_PER_DAY', default=5, cast=int)
MAX_LOOKUP_ITERATIONS_FOR_POINTS = config('MAX_LOOKUP_ITERATIONS_FOR_POINTS', default=5, cast=int)
LOOKUP_ITERATIONS_RADIUS_INIT = config('LOOKUP_ITERATIONS_RADIUS_INIT', default=10, cast=int)
LOOKUP_ITERATIONS_RADIUS_STEP = config('LOOKUP_ITERATIONS_RADIUS_STEP', default=5, cast=int)


FOURESQUARE_API_CLIENT_ID = config('FOURESQUARE_API_CLIENT_ID', default="5NDRMZN5GUYKQHV0IBZDAFCQRPISIKXG1BNL2KF4UVSG421X", cast=str)
FOURESQUARE_API_CLIENT_SECRET = config('FOURESQUARE_API_CLIENT_SECRET', default="DOCN2RFXJG4LI4YEZ3CDXY3DQVKRJFTZWGRNZUZRDTMNUVWI", cast=str)
FOURESQUARE_API_TOKEN = config('FOURESQUARE_API_TOKEN', default="fsq3gbTuziGLH7+83FNfe7cHI17arBBaxxOW0K1aeXmE9us=", cast=str)
FOURESQUARE_API_URL = config('FOURESQUARE_API_URL', default="https://api.foursquare.com/v3/places/search", cast=str)
# Arts and Entertainment
FOURESQUARE_POI_CATEGORY_ID = config('FOURESQUARE_POI_CATEGORY_ID', default="10000", cast=str)
# Dining and Drinking
FOURESQUARE_RESTAURANT_CATEGORY_ID = config('FOURESQUARE_RESTAURANT_CATEGORY_ID', default="13000", cast=str)
