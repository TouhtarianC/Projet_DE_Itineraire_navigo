from fastapi.testclient import TestClient
from unittest.mock import patch
from navigo.planner.models import POI, Restaurant, Hosting, Trail, WC

from navigo.app.main import app, get_poi_by_zone
from faker import Faker

client = TestClient(app)


fake = Faker()

# ####################### POIS ###################################
mock_POIs = []
mock_POIs_result = []
# Generate fake POIs
for _ in range(100):
    poi = {
        'longitude': fake.longitude(),
        'latitude': fake.latitude(),
        'city': fake.city(),
        'city_code': fake.random_int(min=10000, max=99999),
        'type': 'POI',
        'name': fake.company(),
        'category': '',
        'notation': 0.0,
        'score': 0.0,
        'uuid': fake.uuid4(),
        'cluster': None,
        'day': None,
        'rank': None,
        "type_list": ["PlaceOfInterest","InterpretationCentre","CulturalSite","PointOfInterest","schema:LocalBusiness"],
        "theme_list": ["InTown"]
    }
    mock_POIs.append(POI(**poi))
    mock_POIs_result.append(poi)


def test_get_pois_with_non_int_params():
    # mock get_poi_by_zone to be independant to BDD
    with patch("navigo.app.main.get_poi_by_zone") as mock_get_poi_by_zone:
        mock_get_poi_by_zone.return_value = mock_POIs

        response = client.get("/data/pois?zip_code=balbla&rayon=10")
        # check results
        assert response.status_code == 500
        response = client.get("/data/pois?zip_code=1234&rayon=bou")
        # check results
        assert response.status_code == 500


def test_get_pois():
    # mock get_poi_by_zone to be independant to BDD
    with patch("navigo.app.main.get_poi_by_zone") as mock_get_poi_by_zone:
        mock_get_poi_by_zone.return_value = mock_POIs

        # call get_pois with mocked db
        # (zip_code and rayon values haven't importance here)
        response = client.get("/data/pois?zip_code=12345&rayon=10")

        # check results
        assert response.status_code == 200
        response = response.json()
        assert response.keys() == {"total", "page", "size", "results"}
        assert response['total'] == 100
        assert response['page'] == 1
        assert response['size'] == 10
        assert len(response['results']) == 10
        assert response['results'][0]['name'] == mock_POIs_result[0]['name']

        # check that get_poi_by_zone has been called once
        mock_get_poi_by_zone.assert_called_once_with(12345, 10)

        # closed mock of BDD
        mock_get_poi_by_zone.return_value = None  # Simule une base de données vide
        mock_get_poi_by_zone.reset_mock()  # Réinitialise l'appel précédent
        assert client.get(
            "/data/pois?zip_code=12345&rayon=10").status_code == 404


# ####### Pagination tests, will be done just once as it's generic function ##
#  test pagination with page and size setted
def test_get_pois_with_page_and_size():
    # mock get_poi_by_zone to be independant to BDD
    with patch("navigo.app.main.get_poi_by_zone") as mock_get_poi_by_zone:
        mock_get_poi_by_zone.return_value = mock_POIs

        response = client.get(
            "/data/pois?zip_code=33000&rayon=5&page=2&size=5")
        assert response.status_code == 200
        # check that response contains total, page, size and results
        response = response.json()
        assert response.keys() == {"total", "page", "size", "results"}
        # check that page and size are setted
        assert response['total'] == 100
        assert response["page"] == 2
        assert response["size"] == 5
        # check that results contains 5 elements
        assert len(response["results"]) == 5
        assert response["results"][0]["name"] == mock_POIs_result[5]["name"]


# test pagination with page out of range
def test_get_pois_with_page_out_of_range():
    # mock get_poi_by_zone to be independant to BDD
    with patch("navigo.app.main.get_poi_by_zone") as mock_get_poi_by_zone:
        mock_get_poi_by_zone.return_value = mock_POIs

        response = client.get(
            "/data/pois?zip_code=33000&rayon=5&page=1000&size=5")
        assert response.status_code == 404
        assert response.json()["detail"] == "Page out of range"


# ####################### Restaurants ###########################
# generate fake Restaurants
mock_restaurants = []
mock_restaurants_result = []
for _ in range(100):
    restaurant = {
        'longitude': fake.longitude(),
        'latitude': fake.latitude(),
        'city': fake.city(),
        'city_code': fake.random_int(min=10000, max=99999),
        'type': 'Restaurant',
        'name': fake.company(),
        'category': '',
        'notation': 0.0,
        'score': 0.0,
        'uuid': fake.uuid4(),
        'cluster': None,
        'day': None,
        'rank': None
    }
    mock_restaurants.append(Restaurant(**restaurant))
    mock_restaurants_result.append(restaurant)


def test_get_restaurants_with_non_int_params():
    # mock get_restaurants_by_zone to be independant to BDD
    with patch("navigo.app.main.get_restaurants_by_zone") as mock_get_restaurants_by_zone:
        mock_get_restaurants_by_zone.return_value = mock_restaurants
        
        response = client.get("/data/restaurants?zip_code=balbla&rayon=10")
        # check results
        assert response.status_code == 500
        
        response = client.get("/data/restaurants?zip_code=1234&rayon=bou")
        # check results
        assert response.status_code == 500


# check get_restaurants
def test_get_restaurants():
    # mock get_restaurants_by_zone to be independant to BDD
    with patch("navigo.app.main.get_restaurants_by_zone") as mock_get_restaurants_by_zone:
        mock_get_restaurants_by_zone.return_value = mock_restaurants

        # call get_restaurants with mocked db
        # (zip_code and rayon values haven't importance here)
        response = client.get("/data/restaurants?zip_code=12345&rayon=10")

        # check results
        assert response.status_code == 200
        response = response.json()
        assert response.keys() == {"total", "page", "size", "results"}
        assert response['total'] == 100
        assert response['page'] == 1
        assert response['size'] == 10
        assert len(response['results']) == 10
        assert response['results'][0]['name'] == mock_restaurants_result[0]['name']

        # check that get_restaurants_by_zone has been called once
        mock_get_restaurants_by_zone.assert_called_once_with(12345, 10)

        # closed mock of BDD
        # Simule une base de données vide
        mock_get_restaurants_by_zone.return_value = None
        mock_get_restaurants_by_zone.reset_mock()  # Réinitialise l'appel précédent
        assert client.get(
            "/data/restaurants?zip_code=12345&rayon=10").status_code == 404


# ####################### Hostings ###########################
# generate fake Hostings
mock_hostings = []
mock_hostings_result = []
for _ in range(100):
    hosting = {
        'longitude': fake.longitude(),
        'latitude': fake.latitude(),
        'city': fake.city(),
        'city_code': fake.random_int(min=10000, max=99999),
        'type': 'Hosting',
        'name': fake.company(),
        'category': '',
        'notation': 0.0,
        'score': 0.0,
        'uuid': fake.uuid4(),
        'cluster': None,
        'day': None,
        'rank': None
    }
    mock_hostings.append(Hosting(**hosting))
    mock_hostings_result.append(hosting)


def test_get_hostings_with_non_int_params():
    # mock get_hostings_by_zone to be independant to BDD
    with patch("navigo.app.main.get_hosting_by_zone") as mock_get_hosting_by_zone:
        mock_get_hosting_by_zone.return_value = mock_hostings

        response = client.get("/data/hostings?zip_code=balbla&rayon=10")
        # check results
        assert response.status_code == 500
        response = client.get("/data/hostings?zip_code=1234&rayon=bou")
        # check results
        assert response.status_code == 500


# check get_hostings
def test_get_hostings():
    # mock get_hostings_by_zone to be independant to BDD
    with patch("navigo.app.main.get_hosting_by_zone") as mock_get_hosting_by_zone:
        mock_get_hosting_by_zone.return_value = mock_hostings

        # call get_hostings with mocked db
        # (zip_code and rayon values haven't importance here)
        response = client.get("/data/hostings?zip_code=12345&rayon=10")

        # check results
        assert response.status_code == 200
        response = response.json()
        assert response.keys() == {"total", "page", "size", "results"}
        assert response['total'] == 100
        assert response['page'] == 1
        assert response['size'] == 10
        assert len(response['results']) == 10
        assert response['results'][0]['name'] == mock_hostings_result[0]['name']

        # check that get_hostings_by_zone has been called once
        mock_get_hosting_by_zone.assert_called_once_with(12345, 10)

        # closed mock of BDD
        mock_get_hosting_by_zone.return_value = None  # Simule une base de données vide
        mock_get_hosting_by_zone.reset_mock()  # Réinitialise l'appel précédent
        assert client.get(
            "/data/hostings?zip_code=12345&rayon=10").status_code == 404


# ####################### Trails ###########################
# Generate fake Trails
mock_trails = []
mock_trails_result = []
for _ in range(100):
    trail = {
        'longitude': fake.longitude(),
        'latitude': fake.latitude(),
        'city': fake.city(),
        'city_code': fake.random_int(min=10000, max=99999),
        'type': 'Trail',
        'name': fake.company(),
        'category': '',
        'notation': 0.0,
        'score': 0.0,
        'uuid': fake.uuid4(),
        'cluster': None,
        'day': None,
        'rank': None
    }
    mock_trails.append(Trail(**trail))
    mock_trails_result.append(trail)


def test_get_trails_with_non_int_params():
    # mock get_trails_by_zone to be independant to BDD
    with patch("navigo.app.main.get_trails_by_zone") as mock_get_trails_by_zone:
        mock_get_trails_by_zone.return_value = mock_trails

        response = client.get("/data/trails?zip_code=balbla&rayon=10")
        # check results
        assert response.status_code == 500
        response = client.get("/data/trails?zip_code=1234&rayon=bou")
        # check results
        assert response.status_code == 500


# check get_trails
def test_get_trails():
    # mock get_trails_by_zone to be independant to BDD
    with patch("navigo.app.main.get_trails_by_zone") as mock_get_trails_by_zone:
        mock_get_trails_by_zone.return_value = mock_trails

        # call get_trails with mocked db
        # (zip_code and rayon values haven't importance here)
        response = client.get("/data/trails?zip_code=12345&rayon=10")

        # check results
        assert response.status_code == 200
        response = response.json()
        assert response.keys() == {"total", "page", "size", "results"}
        assert response['total'] == 100
        assert response['page'] == 1
        assert response['size'] == 10
        assert len(response['results']) == 10
        assert response['results'][0]['name'] == mock_trails_result[0]['name']

        # check that get_trails_by_zone has been called once
        mock_get_trails_by_zone.assert_called_once_with(12345, 10)

        # closed mock of BDD
        mock_get_trails_by_zone.return_value = None  # Simule une base de données vide
        mock_get_trails_by_zone.reset_mock()  # Réinitialise l'appel précédent
        assert client.get(
            "/data/trails?zip_code=12345&rayon=10").status_code == 404


# ####################### WC ###########################
# Generate fake WC
mock_WCs = []
mock_WCs_result = []
for _ in range(100):
    wc = {
        'longitude': fake.longitude(),
        'latitude': fake.latitude(),
        'city': fake.city(),
        'city_code': fake.random_int(min=10000, max=99999),
        'type': "POI",
        'name': "WC",
        'category': '',
        'notation': 0.0,
        'score': 0.0,
        'uuid': fake.uuid4(),
        'cluster': None,
        'day': None,
        'rank': None
    }
    mock_WCs.append(WC(**wc))
    mock_WCs_result.append(wc)


def test_get_wcs_with_non_int_params():
    # mock get_WCs_by_zone to be independant to BDD
    with patch("navigo.app.main.get_wc_by_zone") as mock_get_wc_by_zone:
        mock_get_wc_by_zone.return_value = mock_WCs

        response = client.get("/data/wcs?zip_code=balbla&rayon=10")
        # check results
        assert response.status_code == 500
        response = client.get("/data/wcs?zip_code=1234&rayon=bou")
        # check results
        assert response.status_code == 500

# check get_wcs


def test_get_wcs():
    # mock get_WCs_by_zone to be independant to BDD
    with patch("navigo.app.main.get_wc_by_zone") as mock_get_wc_by_zone:
        mock_get_wc_by_zone.return_value = mock_WCs

        # call get_WCs with mocked db
        # (zip_code and rayon values haven't importance here)
        response = client.get("/data/wcs?zip_code=12345&rayon=10")

        # check results
        assert response.status_code == 200
        response = response.json()
        assert response.keys() == {"total", "page", "size", "results"}
        assert response['total'] == 100
        assert response['page'] == 1
        assert response['size'] == 10
        assert len(response['results']) == 10
        assert response['results'][0]['uuid'] == mock_WCs_result[0]['uuid']

        # check that get_WCs_by_zone has been called once
        mock_get_wc_by_zone.assert_called_once_with(12345, 10)

        # closed mock of BDD
        mock_get_wc_by_zone.return_value = None  # Simule une base de données vide
        mock_get_wc_by_zone.reset_mock()  # Réinitialise l'appel précédent
        assert client.get(
            "/data/WCs?zip_code=12345&rayon=10").status_code == 404
