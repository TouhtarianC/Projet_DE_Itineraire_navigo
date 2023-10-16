from dataclasses import dataclass, field


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
    score: float = 0.0


@dataclass
class POI(GeospatialPoint):
    type: str = "POI"


def db_raw_to_poi(db_raw: dict) -> POI:
    return POI(
        longitude=db_raw['LONGITUDE'],
        latitude=db_raw['LATITUDE'],
        name=db_raw['NAME'],  # todo verify
        city=db_raw['CITY'],
        city_code=db_raw['POSTAL_CODE'],
    )


@dataclass
class Restaurant(GeospatialPoint):
    type: str = "Restaurant"


def db_raw_to_restaurant(db_raw: dict) -> Restaurant:
    return Restaurant(
        longitude=db_raw['LONGITUDE'],
        latitude=db_raw['LATITUDE'],
        name=db_raw['NAME'],
        city=db_raw['CITY'],
        city_code=db_raw['POSTAL_CODE'],
    )


@dataclass
class Hosting(GeospatialPoint):
    type: str = "Hosting"


def db_raw_to_hosting(db_raw: dict) -> Hosting:
    return Hosting(
        longitude=db_raw['LONGITUDE'],
        latitude=db_raw['LATITUDE'],
        name=db_raw['NAME'],
        city=db_raw['CITY'],
        city_code=db_raw['POSTAL_CODE'],
    )


@dataclass
class Trail(GeospatialPoint):
    type: str = "Trail"


def db_raw_to_trail(db_raw: dict) -> Trail:
    return Trail(
        longitude=db_raw['LONGITUDE'],
        latitude=db_raw['LATITUDE'],
        name=db_raw['NAME'],  # verify
        city=db_raw['CITY'],
        city_code=db_raw['POSTAL_CODE'],
    )


@dataclass
class WC(GeospatialPoint):
    type: str = "POI"
    name: str = "WC"


def db_raw_to_wc(db_raw: dict) -> WC:
    return WC(
        longitude=db_raw['LONGITUDE'],
        latitude=db_raw['LATITUDE'],
        city=db_raw['CITY'],
        city_code=db_raw['POSTAL_CODE'],
    )


@dataclass
class UserData:
    trip_zone: int = 33
    trip_start: str = None
    trip_duration: int = 7
    favorite_poi_categories: list[str] = field(default_factory=list)
    favorite_restaurant_categories: list[str] = field(default_factory=list)
    favorite_hosting_categories: list[str] = field(default_factory=list)
    meantime_on_poi: float = 0.5
    minimal_notation: int = 3
    means_of_transport: str = "BY_FOOT"
    sensitivity_to_weather: float = 0.5
    days_on_hiking: float = 0


@dataclass
class ExternalData:
    weather_forecast: dict[str, dict[str, int]]
    top_poi_list: list[POI]
    top_restaurant_list: list[Restaurant]


@dataclass
class InternalNodesData:
    poi_list: list[POI]
    restaurant_list: list[Restaurant]
    hosting_list: list[Hosting]
    trail_list: list[Trail]

    def get_all_nodes(self):
        return self.poi_list + self.restaurant_list + self.hosting_list + self.trail_list

    def get_sorted_points(self):
        return (
            sorted(self.poi_list, key=lambda x: x.score, reverse=True),
            sorted(self.restaurant_list, key=lambda x: x.score, reverse=True),
            sorted(self.hosting_list, key=lambda x: x.score, reverse=True),
            sorted(self.trail_list, key=lambda x: x.score, reverse=True)
        )
