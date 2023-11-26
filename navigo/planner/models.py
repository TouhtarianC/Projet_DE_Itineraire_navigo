from dataclasses import dataclass, field
from pymongo import MongoClient
from neo4j import GraphDatabase
from navigo.settings import MONGODB_URI, MONGODB_DB, MONGODB_POI_COLLECTION, NEO4J_URI, NEO4J_USER, NEO4J_PWD


@dataclass
class GeospatialPoint:
    longitude: float
    latitude: float

    city: str
    city_code: int

    type: str
    name: str = ""

    category: str = ""
    notation: float = 0
    score: float = 10

    uuid: str = ""
    cluster: int | None = None
    day: int | None = None
    rank: int | None = None

    def __init__(self, longitude, latitude, city, city_code, type, name, 
                 category, notation, score, uuid, cluster):
        self.longitude = longitude
        self.latitude = latitude
        self.city = city
        self.city_code = city_code
        self.type = type 
        self.name = name
        self.category = category
        self.notation = notation
        self.score = score
        self.uuid = uuid
        self.cluster = cluster
    
    def __copy__(self):
        return GeospatialPoint(self.longitude, self.latitude, self.city, 
                               self.city_code, self.type, self.name, self.category, self.notation, 
                               self.score, self.uuid, self.cluster)


@dataclass
class POI(GeospatialPoint):
    type: str = "POI"


def db_raw_to_poi(db_raw: dict) -> POI:
    collection = MongoClient(MONGODB_URI)[
            MONGODB_DB][MONGODB_POI_COLLECTION]
    # print("connection mongoDB ok")

    document = collection.find_one({'UUID': db_raw.UUID})
    if document:
        # connect to neo4j
        with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD)) as driver:
            with driver.session() as session:
                query = (
                    f"MATCH (n) WHERE n.UUID = '{db_raw.UUID}' RETURN n"
                )
                result = session.run(query).data()
                # print(f"neo4j result for poi.id ({db_raw.id}) = {result}")
        if result:
            # todo: how to inject POI category here ??
            return POI(
                    name=document['LABEL']['fr'],
                    city=db_raw.CITY,
                    city_code=db_raw.POSTAL_CODE,
                    uuid=db_raw.UUID,
                    latitude=result[0]['n']['LATITUDE'],
                    longitude=result[0]['n']['LONGITUDE'],
                    )


@dataclass
class Restaurant(GeospatialPoint):
    type: str = "Restaurant"


def db_raw_to_restaurant(db_raw: dict) -> Restaurant:
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD)) as driver:
        with driver.session() as session:
            query = (
                f"MATCH (n:restaurant) WHERE n.UUID = '{db_raw.UUID}' RETURN n"
            )
            result = session.run(query).data()
    if result:
        # print(f"neo4j result for rest ({db_raw.UUID}) = {result}")
        return Restaurant(
            latitude=result[0]['n']['LATITUDE'],
            longitude=result[0]['n']['LONGITUDE'],
            uuid=db_raw['UUID'],
            name=db_raw['NAME'],
            city=db_raw['CITY'],
            city_code=db_raw['POSTAL_CODE'],
            category=db_raw['TYPE'],
            )


@dataclass
class Hosting(GeospatialPoint):
    type: str = "Hosting"


def db_raw_to_hosting(db_raw: dict) -> Hosting:
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD)) as driver:
        with driver.session() as session:
            query = (
                f"MATCH (n:hosting) WHERE n.UUID = '{db_raw.UUID}' RETURN n"
            )
            result = session.run(query).data()
    if result:
        # print(f"neo4j result for hosting ({db_raw.UUID}) = {result}")
        return Hosting(
            latitude=result[0]['n']['LATITUDE'],
            longitude=result[0]['n']['LONGITUDE'],
            uuid=db_raw['UUID'],
            name=db_raw['NAME'],
            city=db_raw['CITY'],
            city_code=db_raw['POSTAL_CODE'],
            category=db_raw['TYPE'],
        )


@dataclass
class Trail(GeospatialPoint):
    type: str = "Trail"


def db_raw_to_trail(db_raw: dict) -> Trail:
    collection = MongoClient(MONGODB_URI)[
            MONGODB_DB][MONGODB_POI_COLLECTION]
    # print("connection mongoDB ok")

    document = collection.find_one({'UUID': db_raw.UUID})
    if document:
        # connect to neo4j
        with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD)) as driver:
            with driver.session() as session:
                query = (
                    f"MATCH (n) WHERE n.UUID = '{db_raw.UUID}' RETURN n"
                )
                result = session.run(query).data()
                # print(f"neo4j result for poi.id ({db_raw.id}) = {result}")
        if result:
            return Trail(
                    name=document['LABEL']['fr'],
                    city=db_raw.CITY,
                    city_code=db_raw.POSTAL_CODE,
                    uuid=db_raw.UUID,
                    latitude=result[0]['n']['LATITUDE'],
                    longitude=result[0]['n']['LONGITUDE'],
                    )


@dataclass
class WC(GeospatialPoint):
    type: str = "POI"
    name: str = "WC"


def db_raw_to_wc(db_raw: dict) -> WC:
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD)) as driver:
        with driver.session() as session:
            query = (
                f"MATCH (n:wc) WHERE n.UUID = '{db_raw.UUID}' RETURN n"
            )
            result = session.run(query).data()
    if result:
        #print(f"neo4j result for wc ({db_raw.UUID}) = {result}")
        return WC(
            latitude=result[0]['n']['LATITUDE'],
            longitude=result[0]['n']['LONGITUDE'],
            name=db_raw['NAME'],
            city=db_raw['CITY'],
            city_code=db_raw['POSTAL_CODE'],
        )


@dataclass
class UserData:
    trip_zone: int = 33000
    trip_start: str = "2024-01-08"
    trip_duration: int = 7
    # favorite_poi_categories: list[str] = field(default_factory=list)
    favorite_poi_type_list: list[str] = field(default_factory=list)
    favorite_poi_theme_list: list[str] = field(default_factory=list)
    favorite_restaurant_categories: list[str] = field(default_factory=list)
    favorite_hosting_categories: list[str] = field(default_factory=list)
    # meantime_on_poi: float = 0.5
    # minimal_notation: int = 3
    means_of_transport: str = "by foot"
    sensitivity_to_weather: bool = True
    days_on_hiking: float = 0


@dataclass
class ExternalData:
    weather_forecast: bool  # True if weather is good => boost external activities
    top_poi_list: list[POI]
    top_restaurant_list: list[Restaurant]


@dataclass
class InternalNodesData:
    poi_list: list[POI]
    restaurant_list: list[Restaurant]
    hosting_list: list[Hosting]
    trail_list: list[Trail]

    def get_all_nodes(self):
        return self.poi_list + \
            self.restaurant_list + self.hosting_list + self.trail_list

    def get_sorted_points(self):
        return (
            sorted(self.poi_list, key=lambda x: x.score, reverse=True),
            sorted(self.restaurant_list, key=lambda x: x.score, reverse=True),
            sorted(self.hosting_list, key=lambda x: x.score, reverse=True),
            sorted(self.trail_list, key=lambda x: x.score, reverse=True)
        )

    def select_top_points_by_day(self, nb_days: int, max_pois_by_day: int):
        # select the top points for each cluster based on the score
        result_list = []
        for d in range(nb_days):
            my_list = [poi for poi in self.poi_list if poi.cluster == d]
            for res in sorted(my_list,
                              key=lambda x: x.score,
                              reverse=True)[:max_pois_by_day]:
                result_list.append(res)
        return result_list

    def select_best(self):
        """return the object with best score level"""
        return (
            sorted(self.poi_list, key=lambda x: x.score, reverse=True)[0],
            sorted(self.restaurant_list,
                   key=lambda x: x.score, reverse=True)[0],
            sorted(self.hosting_list, key=lambda x: x.score, reverse=True)[0],
            sorted(self.trail_list, key=lambda x: x.score, reverse=True)[0]
        )
