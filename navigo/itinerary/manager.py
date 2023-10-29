from dataclasses import asdict
from neo4j import GraphDatabase, basic_auth
from navigo.planner.models import GeospatialPoint, POI, Hosting, Restaurant, Trail
from navigo.settings import NEO4J_URI, NEO4J_USER, NEO4J_PWD
import time
import logging



driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PWD))
logger = logging.getLogger(__name__)


def clear_nodes(node_type):
    query = (f"MATCH (n:{node_type}) DETACH DELETE n;")
    with driver.session() as session:
        session.run(query)

def clear_relationships(relationship_type):
    query = (f"MATCH ()-[r:{relationship_type}]->() DETACH DELETE r;")
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
            SET c.UUID = p.uuid \
            SET c.TYPE = '{type.upper()}'; \
            ")
        
        with driver.session() as session:
            session.run(queryDuplicate)       

# Create nodes for POIs, Restaurants, Hostings, and Trails
def create_nodes(poi_list, restaurant_list, hosting_list, trail_list):
    
    for node in poi_list + restaurant_list + hosting_list + trail_list:
        # copy of new nodes and labels in upper to be consistent with neo4j db
        node_type = node.type+'2'
        params_node = {key.upper(): asdict(node)[key] for key in asdict(node).keys()}
        query = (
            f"CREATE (p:{node_type} $params)\
            SET p.LATITUDE = toFloat(p.LATITUDE) \
            SET p.LONGITUDE = toFloat(p.LONGITUDE) \
            ;" 
        )
        with driver.session() as session:
            session.run(query, params=params_node)


# Identify a POI among a list with its uuid, return a POI
def find_node_by_uuid(poi_list, uuid):    
    return next((poi for poi in poi_list if poi.uuid == uuid), None)


# Identify a POI among a list with its day and its rank, return a POI
def find_node_by_day_rank(poi_list, day, rank):
    return next((poi for poi in poi_list if poi.day == day and poi.rank == rank), None)

# Identify 4 nodes, before looking for lunch, dinner and hotel, return a tuple of 4 POI
def find_nodes_by_steps(poi_list, day, n_pois_to_visit): 
    poi_before_lunch, poi_after_lunch, poi_before_diner, poi_after_hosting = None, None, None, None
    match n_pois_to_visit: 
        case 4: 
            poi_before_lunch = find_node_by_day_rank(poi_list, day, 2)
            poi_after_lunch = find_node_by_day_rank(poi_list, day, 3)
            poi_before_diner = find_node_by_day_rank(poi_list, day, 4)
            poi_after_hosting = find_node_by_day_rank(poi_list, day+1, 1)
        case 3: 
            poi_before_lunch = find_node_by_day_rank(poi_list, day, 2)
            poi_after_lunch = find_node_by_day_rank(poi_list, day, 3)
            poi_before_diner = poi_after_lunch
            poi_after_hosting = find_node_by_day_rank(poi_list, day+1, 1)
        case 2: 
            poi_before_lunch = find_node_by_day_rank(poi_list, day, 1)
            poi_after_lunch = find_node_by_day_rank(poi_list, day, 2)
            poi_before_diner = poi_after_lunch
            poi_after_hosting = find_node_by_day_rank(poi_list, day+1, 1)
        case 1: 
            poi_before_lunch = find_node_by_day_rank(poi_list, day, 1)
            poi_after_lunch = find_node_by_day_rank(poi_list, day+1, 1)
            poi_before_diner = poi_after_lunch
            poi_after_hosting = poi_after_lunch

    return poi_before_lunch, poi_after_lunch, poi_before_diner, poi_after_hosting

# Identify uuids from POIs of a same cluster, return a tuple of 2 lists : uuids from a same cluster, all other uuids
def find_uuids_by_cluster(poi_list, cluster):
    uuid_list_cluster = [poi.uuid for poi in poi_list if poi.cluster == cluster]
    uuid_list_other = [poi.uuid for poi in poi_list if poi.cluster != cluster]
    return uuid_list_cluster, uuid_list_other


# find the number of nodes according to a ray
# e.g. find "start" with its uuid, end with its uuid and all the possible "stop"
#       then find all "stop" that meet the requirements of a distance < ray
#       finally return a number : nb 
def find_next_stop_number(source, target, stop_type, ray):  
    source_type = source.type + '2'
    target_type = target.type + '2'
    find_type = stop_type + '2'

    queryfindNextStopNumber = (
        f"MATCH (start:{source_type} {{UUID: '{source.uuid}'}}) \
        MATCH (end:{target_type} {{UUID: '{target.uuid}'}}) \
        MATCH (stop:{find_type}) \
        WITH \
            point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}) AS startPoint, \
            point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) AS endPoint, \
            point({{longitude: stop.LONGITUDE, latitude: stop.LATITUDE}}) AS stopPoint, \
            stop.LONGITUDE as stop_lon, stop.LATITUDE as stop_lat, \
            start, end, stop \
        WHERE stop.LONGITUDE=stop_lon and stop.LATITUDE=stop_lat \
            and round(point.distance(startPoint, stopPoint))<{ray} \
            and round(point.distance(stopPoint, endPoint))<{ray} \
        RETURN COUNT(stop) AS nb; \
    ")

    with driver.session() as session:
        res= session.run(queryfindNextStopNumber).data()

    return res[0]['nb']


# Compute next POI to visit, and return the next UUID and CLUSTER
# e.g. find "start" with its uuid, and all the possible "m" that are different from "start" and in a list of uuids
#       then find "end" that meet the requirements of a distance = dist_min
#       finally return a UUID and a CLUSTER
def compute_next_nearest_poi(source, remain_uuid):

    queryCreateToNextPOI = (
        f"MATCH (start:POI2 {{UUID:'{source.uuid}'}}) \
        MATCH (m:POI2) WHERE m.UUID <> start.UUID and m.UUID in {remain_uuid} \
        WITH \
            min(round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: m.LONGITUDE, latitude: m.LATITUDE}}) \
            ))) as dist_min, start \
        MATCH (end:POI2) WHERE end.UUID <> start.UUID \
            and end.UUID in {remain_uuid} \
            and round(point.distance( \
                point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}), \
                point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) \
                )) = dist_min \
        MERGE (start)-[r:TO_NEXT_POI]->(end) \
        SET r.DISTANCE=dist_min \
        RETURN end; \
    ")
      
    with driver.session() as session:
        res = session.run(queryCreateToNextPOI).data()
    
    res = res[0]['end']
    return res['UUID'], res['CLUSTER']


# Compute next stop (a restaurant or a hosting)
def compute_next_nearest_stop(source, target, stop_type): 

    ray_f=200
    n=find_next_stop_number(source, target, stop_type, ray_f)
    
    while (ray_f<20000 and n<3): 
        ray_f+=50
        n=find_next_stop_number(source, target, stop_type, ray_f)

    queryCreateRelationshipFromPOIToRestaurant = (
        f"MATCH (start:POI2 {{UUID:'{source.uuid}'}}) \
        MATCH (end:POI2 {{UUID:'{target.uuid}'}}) \
        MATCH (stop:Restaurant2) \
        WITH \
            point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}) AS startPoint, \
            point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) AS endPoint, \
            point({{longitude: stop.LONGITUDE, latitude: stop.LATITUDE}}) AS stopPoint, \
            stop.LONGITUDE as stop_lon, stop.LATITUDE as stop_lat, \
            start, end, stop \
        WHERE stop.LONGITUDE=stop_lon and stop.LATITUDE=stop_lat \
            and round(point.distance(startPoint, stopPoint))<={ray_f} \
            and round(point.distance(stopPoint, endPoint))<={ray_f} \
        CREATE (stop_dup:Restaurant2) \
        SET stop_dup += properties(stop) \
        MERGE (start)-[rTO:TO_RESTAURANT]->(stop_dup) \
        SET rTO.DISTANCE = round(point.distance(startPoint, stopPoint)) \
        MERGE (stop_dup)-[rFROM:TO_NEXT_POI]->(end) \
        SET rFROM.DISTANCE = round(point.distance(stopPoint, endPoint)); \
    ")

    queryDeleteRelationshipsFromPOIToPOI = (
        f"MATCH p=(start:POI2 {{UUID:'{source.uuid}'}})-[r:TO_NEXT_POI]->(end:POI2 {{UUID:'{target.uuid}'}}) "
        "DELETE r; "
    )

    queryCreateRelationshipFromRestaurantToHosting = (
        f"MATCH (start:POI2 {{UUID:'{source.uuid}'}}) \
        MATCH (end:POI2 {{UUID:'{target.uuid}'}}) \
        MATCH (stopR:Restaurant2) \
        MATCH p=(start)-[r:TO_RESTAURANT]->(stopR) \
        MATCH (stopH:Hosting2) \
        WITH \
            point({{longitude: start.LONGITUDE, latitude: start.LATITUDE}}) AS startPoint, \
            point({{longitude: end.LONGITUDE, latitude: end.LATITUDE}}) AS endPoint, \
            point({{longitude: stopR.LONGITUDE, latitude: stopR.LATITUDE}}) AS stopRPoint, \
            point({{longitude: stopH.LONGITUDE, latitude: stopH.LATITUDE}}) AS stopHPoint, \
            stopH.LONGITUDE as stopH_lon, stopH.LATITUDE as stopH_lat, \
            start, end, stopR, stopH \
        WHERE stopH.LONGITUDE=stopH_lon and stopH.LATITUDE=stopH_lat \
            and round(point.distance(stopRPoint, stopHPoint))<={ray_f} \
            and round(point.distance(stopHPoint, endPoint))<={ray_f} \
        CREATE (stopH_dup:Hosting2) \
        SET stopH_dup += properties(stopH) \
        MERGE (stopR)-[rTO:TO_HOSTING]->(stopH_dup) \
        SET rTO.DISTANCE = round(point.distance(stopRPoint, stopHPoint)) \
        MERGE (stopH_dup)-[rFROM:TO_NEXT_POI]->(end) \
        SET rFROM.DISTANCE = round(point.distance(stopHPoint, endPoint)); \
    ")

    queryDeleteRelationshipsFromRestaurantToPOI = (
        f"MATCH p1=(start:POI2 {{UUID:'{source.uuid}'}})-[r1:TO_RESTAURANT]->(stop:Restaurant2)-[r2:TO_NEXT_POI]->(end:POI2 {{UUID:'{target.uuid}'}}) "
        "DELETE r2; "
    )

    with driver.session() as session:
        if stop_type == 'Restaurant': 
            session.run(queryCreateRelationshipFromPOIToRestaurant)
            session.run(queryDeleteRelationshipsFromPOIToPOI)
        elif stop_type == 'Hosting': 
            session.run(queryCreateRelationshipFromRestaurantToHosting)
            session.run(queryDeleteRelationshipsFromRestaurantToPOI)
            

def compute_relationships(first_poi: POI, selected_pois: list[POI]):

    selected_pois_order=[]              
    selected_pois_pop = selected_pois   
    day, rank = 1, 1
    count_poi_per_day={1:1}

    # First poi to visit
    poi_start = first_poi
    selected_pois_pop.remove(poi_start)     # remove it from the list of remaining POIs to visit
    selected_pois_order.append(poi_start)   # append it with the right order

    # First cluster to start
    cluster_start = poi_start.cluster    
    poi_start.day, poi_start.rank = day, rank
    remain_uuid_cluster, remain_uuid_other = find_uuids_by_cluster(selected_pois_pop, cluster_start)                
    
    try:
    # 1/ Loop on POIs first
        # while there are POIs to visit
        while(len(selected_pois_pop) > 0):

            # verify that there are still pois to visit within the same cluster
            if (len(remain_uuid_cluster) > 0): 
                rank += 1
                next_poi_uuid, cluster_start = compute_next_nearest_poi(poi_start, remain_uuid_cluster)
            else:     
                day += 1    #another day
                rank = 1    #restart at 1
                next_poi_uuid, cluster_start = compute_next_nearest_poi(poi_start, remain_uuid_other)
    
            # return a POI according to its uuid
            poi_start = find_node_by_uuid(selected_pois_pop, next_poi_uuid)
            # remove it from the list of remaining POIs to visit
            selected_pois_pop.remove(poi_start)
            # append it with the right order
            poi_start.day, poi_start.rank = day, rank
            selected_pois_order.append(poi_start)
        
            # update the 2 lists of remaning POIs to visit
            remain_uuid_cluster, remain_uuid_other = find_uuids_by_cluster(selected_pois_pop, cluster_start)                

            # count the number of POIs to visit within the day
            try: 
                count_poi_per_day[day] +=1
            except KeyError: 
                count_poi_per_day[day] =1

        # itinary (POIs only)
        for pos, poi in enumerate(selected_pois_order): 
            print(pos, poi.day, poi.rank, poi.cluster, poi.name)

    # 2/ loop on restaurants and hostings 
        for day_trip in range(1,day+1):
            count_poi_day_trip = count_poi_per_day[day_trip]
            poi_before_lunch, poi_after_lunch, poi_before_diner,poi_after_hosting = \
                find_nodes_by_steps(selected_pois_order, day_trip, count_poi_day_trip)
            
            # plan a lunch
            if poi_after_lunch != None: 
                compute_next_nearest_stop(poi_before_lunch, poi_after_lunch, 'Restaurant')
                if day_trip<day:
                    # plan a dinner (except the last day)
                    compute_next_nearest_stop(poi_before_diner, poi_after_hosting, 'Restaurant')
                    # plan a hosting, except for the last night of the trip (except the last day)
                    compute_next_nearest_stop(poi_before_diner, poi_after_hosting, 'Hosting')
            else:
                if day_trip<day:
                    # plan a dinner (except the last day)
                    compute_next_nearest_stop(poi_before_lunch, poi_after_hosting, 'Restaurant')
                    # plan a hosting, except for the last night of the trip (except the last day)
                    compute_next_nearest_stop(poi_before_lunch, poi_after_hosting, 'Hosting')

    except KeyError:
        pass

    return selected_pois_order


# Algorithm : Dijkstra Source-Target Shortest Path
def compute_shortest_path(selected_pois: list[POI]):

    #project a graph and store it
    myGraphName = 'myGraph'+str(round(time.time()))
    queryGraphProject = (
        f"CALL gds.graph.project( \
            '{myGraphName}', \
            ['POI2', 'Restaurant2', 'Hosting2'], \
            ['TO_NEXT_POI', 'TO_RESTAURANT', 'TO_HOSTING'], \
            {{relationshipProperties:'DISTANCE'}} \
            ) \
        ")
    
    # estimate the memory it will take
    first_POI, last_POI = selected_pois[0], selected_pois[len(selected_pois)-1]
    queryMemoryEstimation = (
        f"MATCH \
            (source:POI2 {{UUID:'{first_POI.uuid}'}}), \
            (target:POI2 {{UUID:'{last_POI.uuid}'}}) \
        CALL gds.shortestPath.dijkstra.write.estimate('{myGraphName}', {{ \
            sourceNode: source, \
            targetNode: target, \
            relationshipWeightProperty: 'DISTANCE', \
            writeRelationshipType:'PATH' \
        }}) \
        YIELD nodeCount, relationshipCount, bytesMin, bytesMax, requiredMemory \
        RETURN nodeCount, relationshipCount, bytesMin, bytesMax, requiredMemory; \
        "
    )

    # stream the shortest path
    queryStream = (
        f"MATCH \
            (source:POI2 {{UUID:'{first_POI.uuid}'}}), \
            (target:POI2 {{UUID:'{last_POI.uuid}'}}) \
        CALL gds.shortestPath.dijkstra.stream('{myGraphName}', {{ \
            sourceNode: source, \
            targetNode: target, \
            relationshipWeightProperty: 'DISTANCE' \
        }}) \
        YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path \
        RETURN \
            index, \
            gds.util.asNode(sourceNode).UUID AS sourceNodeName, \
            gds.util.asNode(targetNode).UUID AS targetNodeName, \
            totalCost, \
            [nodeId IN nodeIds | gds.util.asNode(nodeId).UUID] AS nodeNames, \
            costs, \
            nodes(path) as path \
        ORDER BY totalCost ; \
        "
    )

    """# mutate (update the graph with new relationships) : no need here ...
    queryMutate = (
        f"MATCH \
            (source:POI2 {{UUID:'{first_POI.uuid}'}}), \
            (target:POI2 {{UUID:'{last_POI.uuid}'}}) \
        CALL gds.shortestPath.dijkstra.mutate('{myGraphName}', {{ \
            sourceNode: source, \
            targetNode: target, \
            relationshipWeightProperty: 'DISTANCE', \
            mutateRelationshipType: 'PATH' \
        }}) \
        YIELD relationshipsWritten \
        RETURN relationshipsWritten; \
        "
    )"""

    queryWrite = (
        f"MATCH \
            (source:POI2 {{UUID:'{first_POI.uuid}'}}), \
            (target:POI2 {{UUID:'{last_POI.uuid}'}}) \
        OPTIONAL MATCH (source)-[r:PATH]->(target) \
        WHERE r is null \
        CALL gds.shortestPath.dijkstra.write('{myGraphName}', {{ \
            sourceNode: source, \
            targetNode: target, \
            relationshipWeightProperty: 'DISTANCE', \
            writeRelationshipType: 'PATH', \
            writeNodeIds: true, \
            writeCosts: true \
        }}) \
        YIELD relationshipsWritten \
        RETURN relationshipsWritten; \
        "
    )
    
    # relationships to view the shortest itinary on neo4j navigator
    queryTempRelationships = (
        f"MATCH p=()-[r:PATH]->() \
        WITH min(r.totalCost) as costMin \
        MATCH pMin=()-[rMin:PATH]->() \
            WHERE rMin.totalCost = costMin \
        WITH rMin.nodeIds as nodeIds \
        UNWIND range(0, size(nodeIds) - 2) AS index \
        WITH nodeIds[index] AS idn, nodeIds[index+1] AS idm \
        MATCH (nOld), (mOld) \
            WHERE id(nOld)=idn AND id(mOld)=idm \
        CREATE p=(nOld)-[rel:It_TO_NEXT]->(mOld) \
        RETURN p; \
        "
    )

    queryTempDeletePath = (f"MATCH p=()-[r:PATH]->() delete r;")

    with driver.session() as session:
        # algo
        session.run(queryGraphProject)
        session.run(queryMemoryEstimation)
        session.run(queryStream)
        session.run(queryWrite)   
        
        # view the itinary on neo4j interface
        res = session.run(queryTempRelationships).data()
        
        # delete temp PATH
        session.run(queryTempDeletePath)

    return res
        

# Function to be called in planner/planner.py    
def compute_itinerary(first_poi: POI, selected_pois: list[POI], selected_restaurants: list[Restaurant],
                      selected_hostings: list[Hosting], selected_trails: list[Trail]):

    # Clear nodes and relationships
    for relationship_type in ['TO_NEXT_POI', 'TO_RESTAURANT', 'TO_HOSTING', 'It_TO_NEXT']: 
        clear_relationships(relationship_type)
    for node_type in ['POI2', 'Restaurant2', 'Hosting2', 'Trail2']:
        clear_nodes(node_type)
    
    # Create new nodes in neo4j, temporarly (POI2, restaurant2, hosting2)
    create_nodes(selected_pois, selected_restaurants, selected_hostings, selected_trails)
    logger.info(f"number of nodes created = {len(selected_pois)}, {len(selected_restaurants)}, {len(selected_hostings)}, {len(selected_trails)}")

    # temp only  because restaurants and hostings lists are too far away from selected POIs to visit
    # create_nodes(selected_pois, [], [], [])
    # duplicate_nodes()

    # Create new relationships 
    selected_pois_order = compute_relationships(first_poi, selected_pois)
    
    # Find the shortest path
    path = compute_shortest_path(selected_pois_order)

    # Return the 4 lists with order to show on dash
    res_pois, res_restaurants, res_hostings, res_trails = [selected_pois_order[0]], [], [], []
    day, rank = 1, 1

    for relation in path:
        match relation['p'][2]['TYPE']:
            case 'POI':
                if relation['p'][0]['TYPE'] == 'Hosting': 
                    day += 1
                    rank = 1
                    res = find_node_by_uuid(selected_pois_order, relation['p'][2]['UUID'])
                    res.day, res.rank = day, rank
                    res_pois.append(res)
                else:
                    rank += 1
                    res = find_node_by_uuid(selected_pois_order, relation['p'][2]['UUID'])
                    res.day, res.rank = day, rank
                    res_pois.append(res)
            case 'Restaurant':
                rank += 1
                res = find_node_by_uuid(selected_restaurants, relation['p'][2]['UUID'])
                res.day, res.rank = day, rank
                res_restaurants.append(res)
            case 'Hosting': 
                rank += 1
                res = find_node_by_uuid(selected_hostings, relation['p'][2]['UUID'])
                res.day, res.rank = day, rank
                res_hostings.append(res)
                 
    return res_pois, res_restaurants, res_hostings, res_trails


if __name__ == '__main__':

    for relationship_type in ['TO_NEXT_POI', 'TO_RESTAURANT', 'TO_HOSTING', 'It_TO_NEXT']: 
        clear_relationships(relationship_type)
    for node_type in ['POI2', 'Restaurant2', 'Hosting2']:
        clear_nodes(node_type)
    
    # Temp only, to include the list of selected POIs
    selected_pois = [POI(longitude='-0.558869', latitude='44.840617', name='Eglise Sainte-Marie de la Bastide', city='Bordeaux', city_code=33100, type='POI', category='', notation=3, score=0, uuid='1d57ae11-bb1f-49fa-864f-47d814a23d45', cluster=0, rank=None), POI(longitude='-0.5644055', latitude='44.8472004', name='Parc aux Angéliques', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='32bd6051-31f4-4dd6-87d2-0cf79083fc44', cluster=0, rank=None), POI(longitude='-0.5692856', latitude='44.8544511', name='Musée du Vin et du Négoce', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='4edfa3f6-be5e-434d-93f3-1916f77c4398', cluster=0, rank=None), POI(longitude='-0.5667723', latitude='44.8557187', name='Le M.U.R de Bordeaux', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='6dec1235-2d6a-4d50-8ce8-2cc55b366159', cluster=0, rank=None), POI(longitude='-0.5819749', latitude='44.8245865', name='Jardin des Dames de la Foi', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='048bbb98-4c96-4cd6-bc59-ec022a439a45', cluster=1, rank=None), POI(longitude='-0.5811166', latitude='44.8377496', name='Jardin de la Mairie', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='15bc6b46-3f95-454c-8601-be162cc59ea4', cluster=1, rank=None), POI(longitude='-0.587269', latitude='44.8350088', name='Ville de Bordeaux', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='2c1ac0a0-31b7-4b60-ae71-f25b8aa4ba9d', cluster=1, rank=None), POI(longitude='-0.5798715', latitude='44.8389326', name='Musée des Arts Décoratifs et du Design', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='30b201f4-6c9f-4a86-8dd1-1597de549bf4', cluster=1, rank=None), POI(longitude='-0.5701544', latitude='44.8309401', name="Musée d'Ethnographie", city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='57543147-7467-4739-8d18-48087768c491', cluster=2, rank=None), POI(longitude='-0.5725751', latitude='44.8311575', name='Place de la Victoire', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='738b0d87-1963-4377-bdbd-5e8576d43bd2', cluster=2, rank=None), POI(longitude='-0.575788', latitude='44.8186303', name='Eglise Sainte-Geneviève', city='Bordeaux', city_code=33800, type='POI', category='', notation=3, score=0, uuid='76260c0f-d98f-4ccc-a214-8aef5e731d6a', cluster=2, rank=None), POI(longitude='-0.5749079', latitude='44.8354248', name="Musée d'Aquitaine", city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='82b805c1-118b-4d8f-b819-3efe70e19956', cluster=2, rank=None), POI(longitude='-0.5589808', latitude='44.8702832', name='Base sous-marine', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='2256e5ad-86a2-41d0-9662-37959c8ba263', cluster=3, rank=None), POI(longitude='-0.5359228', latitude='44.87952', name="Pont d'Aquitaine", city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='29e53f3f-7042-4404-bc27-d9606acc2865', cluster=3, rank=None), POI(longitude='-0.5518423', latitude='44.8584526', name='Pont Jacques Chaban Delmas', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='7944d999-b6ca-400d-8f8f-72c66f40c2f5', cluster=3, rank=None), POI(longitude='-0.58224', latitude='44.849019', name='Le petit hôtel Labottière', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='02265ce9-fd4c-4f9a-a343-6c2b33732720', cluster=4, rank=None), POI(longitude='-0.584782', latitude='44.846231', name='Palais Gallien', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='401149a3-2be5-4de6-aa04-81a7175e2e26', cluster=4, rank=None), POI(longitude='-0.5891036', latitude='44.8539365', name='Institut culturel Bernard Magrez', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='54627204-7ab8-4aaf-8237-42cf65bbbc14', cluster=4, rank=None), POI(longitude='-0.6017074', latitude='44.8533258', name='Parc Bordelais', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='78e242cc-2aaa-409c-aa77-5c806c8fe839', cluster=4, rank=None), POI(longitude='-0.5762819', latitude='44.843941', name='Allées de Tourny', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='056b0813-5e86-4179-a5a9-69a132958bd8', cluster=5, rank=None), POI(longitude='-0.57602', latitude='44.842636', name='Eglise Notre Dame et Cour Mably', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='092d05f9-429a-4ace-b0ba-ab794e66f445', cluster=5, rank=None), POI(longitude='-0.5799471', latitude='44.8484631', name='Muséum de Bordeaux', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='12d0e495-055d-4db7-bb0a-d695f64673c2', cluster=5, rank=None), POI(longitude='-0.575835', latitude='44.848596', name='Jardin public', city='Bordeaux', city_code=33000, type='POI', category='', notation=3, score=0, uuid='15039d78-a237-4ae3-89be-3ca10de3d180', cluster=5, rank=None), POI(longitude='-0.5788044', latitude='44.8782715', name='Plage du Lac', city='Bruges', city_code=33520, type='POI', category='', notation=3, score=0, uuid='35156e21-7de7-4dcb-8028-68ab310e8efa', cluster=6, rank=None), POI(longitude='-0.6017062', latitude='44.8794938', name='Le parc Ausone', city='Bruges', city_code=33520, type='POI', category='', notation=3, score=0, uuid='477cf819-96bc-4345-b759-8d22d4e44bb2', cluster=6, rank=None)]
    selected_restaurants, selected_hostings, selected_trails = [], [], []
    first_poi = selected_pois[0]

    # Create new nodes in neo4j, temporarly
    create_nodes(selected_pois, selected_restaurants, selected_hostings, selected_trails)
    duplicate_nodes()

    selected_pois_order = compute_relationships(first_poi, selected_pois)
    
    chemin = compute_shortest_path(selected_pois_order)

    for relation in chemin: 
        print(relation) 



