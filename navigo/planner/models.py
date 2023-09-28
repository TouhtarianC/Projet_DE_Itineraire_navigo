from dataclasses import dataclass, field


@dataclass
class GeospatialPoint:
    longitude: float
    latitude: float

    name: str

    city: str
    city_code: int

    type: str

    category: str = ""
    notation: float = 3
    score: float = 0.0


@dataclass
class POI(GeospatialPoint):
    type: str = "POI"


@dataclass
class Restaurant(GeospatialPoint):
    type: str = "Restaurant"


@dataclass
class Hosting(GeospatialPoint):
    type: str = "Hosting"


@dataclass
class Trail(GeospatialPoint):
    type: str = "Trail"


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
    top_poi_list: list[POI]  # Replace with actual POI class definition
    top_restaurant_list: list[Restaurant]  # Replace with actual Restaurant class definition


@dataclass
class InternalNodesData:
    poi_list: list[POI]
    restaurant_list: list[Restaurant]
    hosting_list: list[Hosting]
    trail_list: list[Trail]

    def get_all_nodes(self):
        return self.poi_list + self.restaurant_list + self.hosting_list + self.trail_list

    def select_top_points(self, max_points_to_visit):
        # select the top points based on the score
        return (
            sorted(self.poi_list, key=lambda x: x.score, reverse=True)[:max_points_to_visit],
            sorted(self.restaurant_list, key=lambda x: x.score, reverse=True)[:max_points_to_visit],
            sorted(self.hosting_list, key=lambda x: x.score, reverse=True)[:max_points_to_visit],
            sorted(self.trail_list, key=lambda x: x.score, reverse=True)[:max_points_to_visit]
        )
