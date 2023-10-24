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

    uuid: str = ""
    cluster: int | None = None
    rank: int | None = None


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
        return self.poi_list + self.restaurant_list + self.hosting_list + self.trail_list

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
            for res in sorted(my_list, key=lambda x: x.score, reverse=True)[:max_pois_by_day]:
                result_list.append(res)
        return result_list

    def select_best(self):
        """return the object with best score level"""
        return (
            sorted(self.poi_list, key=lambda x: x.score, reverse=True)[0],
            sorted(self.restaurant_list, key=lambda x: x.score, reverse=True)[0],
            sorted(self.hosting_list, key=lambda x: x.score, reverse=True)[0],
            sorted(self.trail_list, key=lambda x: x.score, reverse=True)[0]
        )
