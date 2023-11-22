from fastapi.testclient import TestClient
from unittest.mock import patch
from navigo.planner.models import POI

from navigo.app.main import app, get_poi_by_zone

client = TestClient(app)

mock_POIs = [POI(longitude='-0.584716', latitude='44.84247', city='Bordeaux', city_code=33000, type='POI', name='Site archéologique de Saint Seurin', category='', notation=0, score=0.0, uuid='02cba7e7-c046-488c-97c2-95364c5f6911', cluster=None, day=None, rank=None),
             POI(longitude='-0.5644055', latitude='44.8472004', city='Bordeaux', city_code=33000, type='POI', name='Parc aux Angéliques',
                 category='', notation=0, score=0.0, uuid='053e84d9-2a39-4664-9858-45ac70e255b6', cluster=None, day=None, rank=None),
             POI(longitude='-0.612311', latitude='44.864726', city='Le Bouscat', city_code=33110, type='POI', name="Parc de la Chêneraie et le Castel d'Andorte",
                 category='', notation=0, score=0.0, uuid='0617580d-cd29-4aa7-b95a-0ce9d6fc9d23', cluster=None, day=None, rank=None),
             POI(longitude='-0.5593435', latitude='44.8710732', city='Bordeaux', city_code=33300, type='POI', name='Bassins des Lumières',
                 category='', notation=0, score=0.0, uuid='080e3c15-fc6b-4aba-9ac8-78ba457bb88f', cluster=None, day=None, rank=None),
             POI(longitude='-0.571477', latitude='44.8354741', city='Bordeaux', city_code=33000, type='POI', name='Grosse Cloche',
                 category='', notation=0, score=0.0, uuid='0b8ecefc-bb80-4a84-9f3d-4c4b05ef9492', cluster=None, day=None, rank=None),
             POI(longitude='-0.5518423', latitude='44.8584526', city='Bordeaux', city_code=33000, type='POI', name='Pont Jacques Chaban Delmas',
                 category='', notation=0, score=0.0, uuid='122b949d-0bbb-442e-b1d7-00f6eb122500', cluster=None, day=None, rank=None)
             ]

mock_POIs_result = [
    {'longitude': -0.584716, 'latitude': 44.84247, 'city': 'Bordeaux', 'city_code': 33000, 'type': 'POI', 'name': 'Site archéologique de Saint Seurin', 'category': '', 'notation': 0.0, 'score': 0.0, 'uuid': '02cba7e7-c046-488c-97c2-95364c5f6911', 'cluster': None, 'day': None, 'rank': None},
    {'longitude': -0.5644055, 'latitude': 44.8472004, 'city': 'Bordeaux', 'city_code': 33000, 'type': 'POI', 'name': 'Parc aux Angéliques', 'category': '', 'notation': 0.0, 'score': 0.0, 'uuid': '053e84d9-2a39-4664-9858-45ac70e255b6', 'cluster': None, 'day': None, 'rank': None},
    {'longitude': -0.612311, 'latitude': 44.864726, 'city': 'Le Bouscat', 'city_code': 33110, 'type': 'POI', 'name': "Parc de la Chêneraie et le Castel d'Andorte", 'category': '', 'notation': 0.0, 'score': 0.0, 'uuid': '0617580d-cd29-4aa7-b95a-0ce9d6fc9d23', 'cluster': None, 'day': None, 'rank': None},
    {'longitude': -0.5593435, 'latitude': 44.8710732, 'city': 'Bordeaux', 'city_code': 33300, 'type': 'POI', 'name': 'Bassins des Lumières', 'category': '', 'notation': 0.0, 'score': 0.0, 'uuid': '080e3c15-fc6b-4aba-9ac8-78ba457bb88f', 'cluster': None, 'day': None, 'rank': None},
    {'longitude': -0.571477, 'latitude': 44.8354741, 'city': 'Bordeaux', 'city_code': 33000, 'type': 'POI', 'name': 'Grosse Cloche', 'category': '', 'notation': 0.0, 'score': 0.0, 'uuid': '0b8ecefc-bb80-4a84-9f3d-4c4b05ef9492', 'cluster': None, 'day': None, 'rank': None},
    {'longitude': -0.5518423, 'latitude': 44.8584526, 'city': 'Bordeaux', 'city_code': 33000, 'type': 'POI', 'name': 'Pont Jacques Chaban Delmas', 'category': '', 'notation': 0.0, 'score': 0.0, 'uuid': '122b949d-0bbb-442e-b1d7-00f6eb122500', 'cluster': None, 'day': None, 'rank': None}
]


def test_get_pois_with_mocked_db():
    # mock get_poi_by_zone to be independant to BDD
    with patch("navigo.app.main.get_poi_by_zone") as mock_get_poi_by_zone:
        mock_get_poi_by_zone.return_value = mock_POIs

        # call get_pois with mocked db 
        # (zip_code and rayon values haven't importance here)
        response = client.get("/data/pois?zip_code=12345&rayon=10")

        # check results
        assert response.status_code == 200
        assert response.json()['results'] == mock_POIs_result

        # check that get_poi_by_zone has been called once
        mock_get_poi_by_zone.assert_called_once_with(12345, 10)

        # closed mock of BDD
        mock_get_poi_by_zone.return_value = None  # Simule une base de données vide
        mock_get_poi_by_zone.reset_mock()  # Réinitialise l'appel précédent
        assert client.get("/data/pois?zip_code=12345&rayon=10").status_code == 404

        # check that get_poi_by_zone has been called once
        mock_get_poi_by_zone.assert_called_once_with(12345, 10)


# test pagination with default values
def test_get_pois():
    response = client.get("/data/pois?zip_code=33000&rayon=5")
    assert response.status_code == 200
    # check that response contains total, page, size and results
    assert response.json().keys() == {"total", "page", "size", "results"}


#  test pagination with page and size setted
def test_get_pois_with_page_and_size():
    response = client.get("/data/pois?zip_code=33000&rayon=5&page=2&size=5")
    assert response.status_code == 200
    # check that response contains total, page, size and results
    assert response.json().keys() == {"total", "page", "size", "results"}
    # check that page and size are setted
    assert response.json()["page"] == 2
    assert response.json()["size"] == 5
    # check that results contains 5 elements
    assert len(response.json()["results"]) == 5


# test pagination with page out of range
def test_get_pois_with_page_out_of_range():
    response = client.get("/data/pois?zip_code=33000&rayon=5&page=1000&size=5")
    assert response.status_code == 404
    assert response.json()["detail"] == "Page out of range"


# check get_restaurants
def test_get_restaurants():
    response = client.get("/data/restaurants?zip_code=33000&rayon=5")
    assert response.status_code == 200
    # assert response.json() == {"name": "item1"}


# check get_hostings
def test_get_hostings():
    response = client.get("/data/hostings?zip_code=33000&rayon=5")
    assert response.status_code == 200
    # assert response.json() == {"name": "item1"}
