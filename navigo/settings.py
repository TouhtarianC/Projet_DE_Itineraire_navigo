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