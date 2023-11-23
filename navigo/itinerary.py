from dataclasses import asdict
from neo4j import GraphDatabase, basic_auth
from navigo.planner.models import POI, Hosting, Restaurant, Trail
from navigo.settings import NEO4J_URI, NEO4J_USER, NEO4J_PWD
import logging
import copy


logger = logging.getLogger(__name__)


def clear_nodes(node_type):
    query = (f"MATCH (n:{node_type}) DETACH DELETE n;")
    with GraphDatabase.driver(NEO4J_URI,
                              auth=basic_auth(NEO4J_USER, NEO4J_PWD)
                              ) as driver:
        with driver.session() as session:
            session.run(query)


def clear_relationships(relationship_type):
    query = (f"MATCH ()-[r:{relationship_type}]->() DETACH DELETE r;")
    with GraphDatabase.driver(NEO4J_URI,
                              auth=basic_auth(NEO4J_USER, NEO4J_PWD)
                              ) as driver:
        with driver.session() as session:
            session.run(query)


# for testing purpose (eg using __main__)
def duplicate_nodes():
    for type in ['restaurant', 'hosting']:
        queryDuplicate = (
            f"MATCH (p:{type}) \
            CREATE (c:{str.capitalize(type)+'2'}) \
            SET c += properties(p) \
            SET c.LATITUDE = toFloat(p.LATITUDE) \
            SET c.LONGITUDE = toFloat(p.LONGITUDE) \
            SET c.SCORE = 0 \
            SET c.TYPE = '{type.upper()}'; \
            ")
        with GraphDatabase.driver(NEO4J_URI,
                                  auth=basic_auth(NEO4J_USER, NEO4J_PWD)
                                  ) as driver:
            with driver.session() as session:
                session.run(queryDuplicate)


# Create nodes for POIs, Restaurants, Hostings, and Trails
def create_nodes(poi_list, restaurant_list, hosting_list, trail_list):
    with GraphDatabase.driver(NEO4J_URI,
                              auth=basic_auth(NEO4J_USER, NEO4J_PWD)
                              ) as driver:
        with driver.session() as session:
            for node in poi_list + restaurant_list + hosting_list + trail_list:
                # copy of new nodes and labels in upper to be consistent with neo4j db
                node_type = node.type+'2'
                params_node = {key.upper(): asdict(
                    node)[key] for key in asdict(node).keys()}
                query = (
                    f"CREATE (p:{node_type} $params)\
                    SET p.LATITUDE = toFloat(p.LATITUDE) \
                    SET p.LONGITUDE = toFloat(p.LONGITUDE) \
                    ;"
                )
                session.run(query, params=params_node)

# Identify a POI among a list with its uuid, return a POI


def find_node_by_uuid(poi_list, uuid):
    res = next((poi for poi in poi_list if poi.uuid == uuid), None)

    if res is not None:
        return copy.copy(res)
    else:
        return None


# Find next POI to visit after a previous POI
def find_next_poi_from_poi(start_uuid):

    queryCreateToNextPOI = (
        f"MATCH (start:POI2 {{UUID:'{start_uuid}'}}) \
        MATCH (m:POI2) WHERE m.UUID <> start.UUID \
            AND m.CLUSTER = start.CLUSTER \
            AND NOT EXISTS(()-[]->(m)) AND NOT EXISTS((m)-[]->()) \
        WITH \
            min(round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: m.LONGITUDE, latitude: m.LATITUDE}}) \
            ))) as dist_min, start \
        MATCH (end:POI2) WHERE end.UUID <> start.UUID \
            AND end.CLUSTER = start.CLUSTER \
            AND NOT EXISTS(()-[]->(end)) AND NOT EXISTS((end)-[]->()) \
            AND round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                )) = dist_min \
        WITH start, end \
        ORDER BY dist_min ASC \
        LIMIT 1 \
        MERGE (start)-[r:TO_NEXT_POI]->(end) \
        SET r.DISTANCE=round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                )) \
        RETURN end; \
    ")
    with GraphDatabase.driver(NEO4J_URI,
                              auth=basic_auth(NEO4J_USER, NEO4J_PWD)
                              ) as driver:
        with driver.session() as session:
            res = session.run(queryCreateToNextPOI).data()
    res = res[0]['end']
    return res['UUID']


# Find next POI to visit after a restaurant or a hosting
def find_next_poi_from_other(start_uuid, start_type, cluster=None):

    # when we have to find a POI after a restaurant, 
    # we have to memorize in which cluster the last POI was
    if cluster is not None:
        queryCreateToNextPOI = (
            f"MATCH (start:{start_type} {{UUID:'{start_uuid}'}}) \
            MATCH (m:POI2) WHERE m.UUID <> start.UUID \
                AND NOT EXISTS(()-[]->(m)) AND NOT EXISTS((m)-[]->()) \
                AND m.CLUSTER = {cluster} \
            WITH \
                min(round(point.distance( \
                    point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                    point({{longitude: m.LONGITUDE, latitude: m.LATITUDE}}) \
                ))) as dist_min, start \
            MATCH (end:POI2) WHERE end.UUID <> start.UUID \
                AND NOT EXISTS(()-[]->(end)) AND NOT EXISTS((end)-[]->()) \
                AND round(point.distance( \
                    point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                    point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                    )) = dist_min \
            WITH start, end \
            ORDER BY dist_min ASC \
            LIMIT 1 \
            MERGE (start)-[r:TO_NEXT_POI]->(end) \
            SET r.DISTANCE=round(point.distance( \
                    point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                    point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                    )) \
            RETURN end; \
        ")
    # when we have to find a POI after a hosting,
    # there's no need to know the cluster as it will be a new one (eg a day after)
    else:
        queryCreateToNextPOI = (
            f"MATCH (start:{start_type} {{UUID:'{start_uuid}'}}) \
            MATCH (m:POI2) WHERE m.UUID <> start.UUID \
                AND NOT EXISTS(()-[]->(m)) AND NOT EXISTS((m)-[]->()) \
            WITH \
                min(round(point.distance( \
                    point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                    point({{longitude: m.LONGITUDE, latitude: m.LATITUDE}}) \
                ))) as dist_min, start \
            MATCH (end:POI2) WHERE end.UUID <> start.UUID \
                AND NOT EXISTS(()-[]->(end)) AND NOT EXISTS((end)-[]->()) \
                AND round(point.distance( \
                    point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                    point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                    )) = dist_min \
            WITH start, end \
            ORDER BY dist_min ASC \
            LIMIT 1 \
            MERGE (start)-[r:TO_NEXT_POI]->(end) \
            SET r.DISTANCE=round(point.distance( \
                    point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                    point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                    )) \
            RETURN end; \
        ")
    with GraphDatabase.driver(NEO4J_URI,
                              auth=basic_auth(NEO4J_USER, NEO4J_PWD)
                              ) as driver:
        with driver.session() as session:
            res = session.run(queryCreateToNextPOI).data()
    res = res[0]['end']
    return res['UUID'], res['CLUSTER']


# Find next restaurant to have lunch or dinner after POI
def find_next_restaurant_from_poi(start_uuid, start_type):

    ray_f = 200
    n = find_stop_around_number(start_uuid, start_type, "Restaurant2", ray_f)

    while (ray_f < 20000 and n < 3):
        ray_f += 100
        n = find_stop_around_number(
            start_uuid, start_type, "Restaurant2", ray_f)
    queryCreateToNextRestaurant = (
        f"MATCH (start:{start_type} {{UUID:'{start_uuid}'}}) \
        MATCH (m:Restaurant2) \
        WHERE round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: m.LONGITUDE, latitude: m.LATITUDE}}) \
                )) <= {ray_f} \
        WITH \
            max(m.SCORE) as score_max, start \
        MATCH (end:Restaurant2) \
        WHERE round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                )) <= {ray_f} \
            AND end.SCORE = score_max \
        WITH start, end \
        ORDER BY score_max DESC \
        LIMIT 1 \
        MERGE (start)-[r:TO_NEXT_RESTAURANT]->(end) \
        SET r.DISTANCE=round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                )) \
        RETURN end; \
    ")
    with GraphDatabase.driver(NEO4J_URI,
                              auth=basic_auth(NEO4J_USER, NEO4J_PWD)
                              ) as driver:
        with driver.session() as session:
            res = session.run(queryCreateToNextRestaurant).data()
    res = res[0]['end']
    return res['UUID']


# Find next hosting to stay after a restaurant
def find_next_hosting_from_restaurant(start_uuid, start_type):

    ray_f = 200
    n = find_stop_around_number(start_uuid, start_type, "Hosting2", ray_f)

    while (ray_f < 20000 and n < 3):
        ray_f += 100
        n = find_stop_around_number(start_uuid, start_type, "Hosting2", ray_f)
    queryCreateToNextHosting = (
        f"MATCH (start:{start_type} {{UUID:'{start_uuid}'}}) \
        MATCH (m:Hosting2) \
        WHERE round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: m.LONGITUDE, latitude: m.LATITUDE}}) \
                )) <= {ray_f} \
        WITH \
            max(m.SCORE) as score_max, start \
        MATCH (end:Hosting2) \
        WHERE round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                )) <= {ray_f} \
            AND end.SCORE = score_max \
        WITH start, end \
        ORDER BY score_max DESC \
        LIMIT 1 \
        MERGE (start)-[r:TO_NEXT_HOSTING]->(end) \
        SET r.DISTANCE=round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                )) \
        RETURN end; \
    ")
    with GraphDatabase.driver(NEO4J_URI,
                              auth=basic_auth(NEO4J_USER, NEO4J_PWD)
                              ) as driver:
        with driver.session() as session:
            res = session.run(queryCreateToNextHosting).data()
    res = res[0]['end']
    return res['UUID']


# Find the number of potential restaurants or hosting in a defined ray
# They will be later filtered by the best score within this ray
def find_stop_around_number(start_uuid, start_type, stop_type, ray):

    queryfindNextStopNumber = (
        f"MATCH (start:{start_type} {{UUID: '{start_uuid}'}}) \
        MATCH (stop:{stop_type}) \
        WITH \
            point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}) AS startPoint, \
            point({{longitude: stop.LONGITUDE, latitude: stop.LATITUDE}}) AS stopPoint, \
            stop.LONGITUDE as stop_lon, stop.LATITUDE as stop_lat, \
            start, stop \
        WHERE stop.LONGITUDE=stop_lon and stop.LATITUDE=stop_lat \
            and round(point.distance(startPoint, stopPoint))<{ray} \
        RETURN COUNT(stop) AS nb; \
    ")
    with GraphDatabase.driver(NEO4J_URI,
                              auth=basic_auth(NEO4J_USER, NEO4J_PWD)
                              ) as driver:
        with driver.session() as session:
            res = session.run(queryfindNextStopNumber).data()
    return res[0]['nb']


# Function to be called in planner/planner.py
def compute_itinerary(first_poi: POI,
                      selected_pois: list[POI],
                      selected_restaurants: list[Restaurant],
                      selected_hostings: list[Hosting],
                      selected_trails: list[Trail]):

    # Clear nodes and relationships
    for relationship_type in ['TO_NEXT_POI', 'TO_NEXT_RESTAURANT',
                              'TO_NEXT_HOSTING', 'It_TO_NEXT']:
        clear_relationships(relationship_type)
    for node_type in ['POI2', 'Restaurant2', 'Hosting2', 'Trail2']:
        clear_nodes(node_type)

    # Create new nodes in neo4j, temporarly (POI2, restaurant2, hosting2)
    create_nodes(selected_pois, selected_restaurants,
                 selected_hostings, selected_trails)

    logger.info(
        f"number of nodes created = {len(selected_pois)}, \
            {len(selected_restaurants)}, {len(selected_hostings)}, \
                {len(selected_trails)}")

    # Number of POI per cluster
    clusters = {}
    for poi in selected_pois:
        try:
            clusters[poi.cluster] += 1
        except KeyError:
            clusters[poi.cluster] = 1

    logger.info(
        f"number of POIS to visit per cluster = {clusters}")

    # Begin the research of next nearest point (POI, Restaurant or Hosting)
    res_pois, res_restaurants, res_hostings, res_trails = [], [], [], []
    day = 1
    start_poi = first_poi
    start_poi.day, start_poi.rank = day, 1
    res_pois.append(start_poi)
    start_poi_uuid = start_poi.uuid
    start_poi_cluster = start_poi.cluster

    while len(clusters) > 0:
        nb_pois_to_visit_in_day = clusters[start_poi_cluster]
        match nb_pois_to_visit_in_day:
            case 4:
                next_poi_to_visit_uuid = find_next_poi_from_poi(start_poi_uuid)
                poi = find_node_by_uuid(selected_pois, next_poi_to_visit_uuid)
                poi.day, poi.rank = day, 2
                res_pois.append(poi)

                next_restaurant_uuid = find_next_restaurant_from_poi(
                    next_poi_to_visit_uuid, "POI2")
                restaurant = find_node_by_uuid(
                    selected_restaurants, next_restaurant_uuid)
                restaurant.day, restaurant.rank = day, 3
                res_restaurants.append(restaurant)

                next_poi_to_visit_uuid, cluster = find_next_poi_from_other(
                    next_restaurant_uuid, 'Restaurant2', start_poi_cluster)
                poi = find_node_by_uuid(selected_pois, next_poi_to_visit_uuid)
                poi.day, poi.rank = day, 4
                res_pois.append(poi)

                next_poi_to_visit_uuid = find_next_poi_from_poi(
                    next_poi_to_visit_uuid)
                poi = find_node_by_uuid(selected_pois, next_poi_to_visit_uuid)
                poi.day, poi.rank = day, 5
                res_pois.append(poi)

                next_restaurant_uuid = find_next_restaurant_from_poi(
                    next_poi_to_visit_uuid, "POI2")
                restaurant = find_node_by_uuid(
                    selected_restaurants, next_restaurant_uuid)
                restaurant.day, restaurant.rank = day, 6
                res_restaurants.append(restaurant)

                next_hosting_uuid = find_next_hosting_from_restaurant(
                    next_restaurant_uuid, "Restaurant2")
                hosting = find_node_by_uuid(
                    selected_hostings, next_hosting_uuid)
                hosting.day, hosting.rank = day, 7
                res_hostings.append(hosting)
            case 3:
                next_poi_to_visit_uuid = find_next_poi_from_poi(start_poi_uuid)
                poi = find_node_by_uuid(selected_pois, next_poi_to_visit_uuid)
                poi.day, poi.rank = day, 2
                res_pois.append(poi)

                next_restaurant_uuid = find_next_restaurant_from_poi(
                    next_poi_to_visit_uuid, "POI2")
                restaurant = find_node_by_uuid(
                    selected_restaurants, next_restaurant_uuid)
                restaurant.day, restaurant.rank = day, 3
                res_restaurants.append(restaurant)

                next_poi_to_visit_uuid, cluster = find_next_poi_from_other(
                    next_restaurant_uuid, 'Restaurant2', start_poi_cluster)
                poi = find_node_by_uuid(selected_pois, next_poi_to_visit_uuid)
                poi.day, poi.rank = day, 4
                res_pois.append(poi)

                next_restaurant_uuid = find_next_restaurant_from_poi(
                    next_poi_to_visit_uuid, "POI2")
                restaurant = find_node_by_uuid(
                    selected_restaurants, next_restaurant_uuid)
                restaurant.day, restaurant.rank = day, 5
                res_restaurants.append(restaurant)

                next_hosting_uuid = find_next_hosting_from_restaurant(
                    next_restaurant_uuid, "Restaurant2")
                hosting = find_node_by_uuid(
                    selected_hostings, next_hosting_uuid)
                hosting.day, hosting.rank = day, 6
                res_hostings.append(hosting)
            case 2:
                next_restaurant_uuid = find_next_restaurant_from_poi(
                    start_poi_uuid, "POI2")
                restaurant = find_node_by_uuid(
                    selected_restaurants, next_restaurant_uuid)
                restaurant.day, restaurant.rank = day, 2
                res_restaurants.append(restaurant)

                next_poi_to_visit_uuid, cluster = find_next_poi_from_other(
                    next_restaurant_uuid, 'Restaurant2', start_poi_cluster)
                poi = find_node_by_uuid(selected_pois, next_poi_to_visit_uuid)
                poi.day, poi.rank = day, 3
                res_pois.append(poi)

                next_restaurant_uuid = find_next_restaurant_from_poi(
                    next_poi_to_visit_uuid, "POI2")
                restaurant = find_node_by_uuid(
                    selected_restaurants, next_restaurant_uuid)
                restaurant.day, restaurant.rank = day, 4
                res_restaurants.append(restaurant)

                next_hosting_uuid = find_next_hosting_from_restaurant(
                    next_restaurant_uuid, "Restaurant2")
                hosting = find_node_by_uuid(
                    selected_hostings, next_hosting_uuid)
                hosting.day, hosting.rank = day, 5
                res_hostings.append(hosting)
            case 1:
                next_restaurant_uuid = find_next_restaurant_from_poi(
                    start_poi_uuid, "POI2")
                restaurant = find_node_by_uuid(
                    selected_restaurants, next_restaurant_uuid)
                restaurant.day, restaurant.rank = day, 2
                res_restaurants.append(restaurant)

                next_hosting_uuid = find_next_hosting_from_restaurant(
                    next_restaurant_uuid, "Restaurant2")
                hosting = find_node_by_uuid(
                    selected_hostings, next_hosting_uuid)
                hosting.day, hosting.rank = day, 3
                res_hostings.append(hosting)

        # delete the cluster
        del clusters[start_poi_cluster]
        logger.info(
            f"Calculation done for day {day}")

        # find next POI to visit on day +1
        if len(clusters) > 0:
            day += 1

            start_poi_uuid, start_poi_cluster = find_next_poi_from_other(
                next_hosting_uuid, 'Hosting2')
            poi = find_node_by_uuid(selected_pois, start_poi_uuid)
            poi.day, poi.rank = day, 1
            res_pois.append(poi)

    return res_pois + res_restaurants + res_hostings + res_trails


if __name__ == '__main__':

    for relationship_type in ['TO_NEXT_POI', 'TO_NEXT_RESTAURANT', 'TO_NEXT_HOSTING', 'It_TO_NEXT']:
        clear_relationships(relationship_type)
    for node_type in ['POI2', 'Restaurant2', 'Hosting2']:
        clear_nodes(node_type)

    # Temp only, to include the list of selected POIs
    selected_pois = [POI(longitude='-0.558869', latitude='44.840617', name='Eglise Sainte-Marie de la Bastide', city='Bordeaux', city_code=33100, type='POI', category='', notation=3, score=0, uuid='1d57ae11-bb1f-49fa-864f-47d814a23d45', cluster=0, rank=None), POI(longitude='-0.5644055', latitude='44.8472004', name='Parc aux Angéliques', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='32bd6051-31f4-4dd6-87d2-0cf79083fc44', cluster=0, rank=None), POI(longitude='-0.5692856', latitude='44.8544511', name='Musée du Vin et du Négoce', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='4edfa3f6-be5e-434d-93f3-1916f77c4398', cluster=0, rank=None), POI(longitude='-0.5667723', latitude='44.8557187', name='Le M.U.R de Bordeaux', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='6dec1235-2d6a-4d50-8ce8-2cc55b366159', cluster=0, rank=None), POI(longitude='-0.5819749', latitude='44.8245865', name='Jardin des Dames de la Foi', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='048bbb98-4c96-4cd6-bc59-ec022a439a45', cluster=1, rank=None), POI(longitude='-0.5811166', latitude='44.8377496', name='Jardin de la Mairie', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='15bc6b46-3f95-454c-8601-be162cc59ea4', cluster=1, rank=None), POI(longitude='-0.587269', latitude='44.8350088', name='Ville de Bordeaux', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='2c1ac0a0-31b7-4b60-ae71-f25b8aa4ba9d', cluster=1, rank=None), POI(longitude='-0.5798715', latitude='44.8389326', name='Musée des Arts Décoratifs et du Design', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='30b201f4-6c9f-4a86-8dd1-1597de549bf4', cluster=1, rank=None), POI(longitude='-0.5701544', latitude='44.8309401', name="Musée d'Ethnographie", city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='57543147-7467-4739-8d18-48087768c491', cluster=2, rank=None), POI(longitude='-0.5725751', latitude='44.8311575', name='Place de la Victoire', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='738b0d87-1963-4377-bdbd-5e8576d43bd2', cluster=2, rank=None), POI(longitude='-0.575788', latitude='44.8186303', name='Eglise Sainte-Geneviève', city='Bordeaux', city_code=33800, type='POI', category='', notation=3, score=0, uuid='76260c0f-d98f-4ccc-a214-8aef5e731d6a', cluster=2, rank=None), POI(longitude='-0.5749079', latitude='44.8354248', name="Musée d'Aquitaine", city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='82b805c1-118b-4d8f-b819-3efe70e19956', cluster=2, rank=None), POI(longitude='-0.5589808', latitude='44.8702832', name='Base sous-marine',
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='2256e5ad-86a2-41d0-9662-37959c8ba263', cluster=3, rank=None), POI(longitude='-0.5359228', latitude='44.87952', name="Pont d'Aquitaine", city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='29e53f3f-7042-4404-bc27-d9606acc2865', cluster=3, rank=None), POI(longitude='-0.5518423', latitude='44.8584526', name='Pont Jacques Chaban Delmas', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='7944d999-b6ca-400d-8f8f-72c66f40c2f5', cluster=3, rank=None), POI(longitude='-0.58224', latitude='44.849019', name='Le petit hôtel Labottière', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='02265ce9-fd4c-4f9a-a343-6c2b33732720', cluster=4, rank=None), POI(longitude='-0.584782', latitude='44.846231', name='Palais Gallien', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='401149a3-2be5-4de6-aa04-81a7175e2e26', cluster=4, rank=None), POI(longitude='-0.5891036', latitude='44.8539365', name='Institut culturel Bernard Magrez', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='54627204-7ab8-4aaf-8237-42cf65bbbc14', cluster=4, rank=None), POI(longitude='-0.6017074', latitude='44.8533258', name='Parc Bordelais', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='78e242cc-2aaa-409c-aa77-5c806c8fe839', cluster=4, rank=None), POI(longitude='-0.5762819', latitude='44.843941', name='Allées de Tourny', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='056b0813-5e86-4179-a5a9-69a132958bd8', cluster=5, rank=None), POI(longitude='-0.57602', latitude='44.842636', name='Eglise Notre Dame et Cour Mably', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='092d05f9-429a-4ace-b0ba-ab794e66f445', cluster=5, rank=None), POI(longitude='-0.5799471', latitude='44.8484631', name='Muséum de Bordeaux', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='12d0e495-055d-4db7-bb0a-d695f64673c2', cluster=5, rank=None), POI(longitude='-0.575835', latitude='44.848596', name='Jardin public', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='15039d78-a237-4ae3-89be-3ca10de3d180', cluster=5, rank=None), POI(longitude='-0.5788044', latitude='44.8782715', name='Plage du Lac', city='Bruges', city_code=33520, type='POI', category='', notation=3, score=0, uuid='35156e21-7de7-4dcb-8028-68ab310e8efa', cluster=6, rank=None), POI(longitude='-0.6017062', latitude='44.8794938', name='Le parc Ausone', city='Bruges', city_code=33520, type='POI', category='', notation=3, score=0, uuid='477cf819-96bc-4345-b759-8d22d4e44bb2', cluster=6, rank=None)]
    selected_restaurants, selected_hostings, selected_trails = [], [], []
    first_poi = selected_pois[0]

    # Create new nodes in neo4j, temporarly
    create_nodes(selected_pois, selected_restaurants,
                 selected_hostings, selected_trails)
    duplicate_nodes()

    selected_restaurants, selected_hostings, selected_trails = [], [], []
    first_poi = selected_pois[0]
    compute_itinerary(first_poi, selected_pois,
                      selected_restaurants, selected_hostings, selected_trails)
