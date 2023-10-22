from dataclasses import asdict

from neo4j import GraphDatabase, basic_auth

from navigo.planner.models import GeospatialPoint, POI, Hosting, Restaurant, Trail
from navigo.settings import NEO4J_URI, NEO4J_USER, NEO4J_PWD


driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PWD))


def clear_nodes():
    query = "MATCH (n) DETACH DELETE n"
    with driver.session() as session:
        session.run(query)


# Create nodes for POIs, Restaurants, Hostings, and Trails
def create_nodes(poi_list, restaurant_list, hosting_list, trail_list):
    for node in poi_list + restaurant_list + hosting_list + trail_list:
        query = (
            f"CREATE (p:{node.type} $params)"
        )
        with driver.session() as session:
            session.run(query, params=asdict(node))

    # create links between POIs
    query = (
        """MATCH (a:POI), (b:POI)
        WHERE id(a) < id(b)  // To avoid creating duplicate relationships
        CREATE (a)-[r:CONNECTED_TO]->(b)
        SET r.weight = point.distance(a, b)
        """
    )
    with driver.session() as session:
        session.run(query)


def compute_shortest_path(start_node, end_nodes):
    # todo implement me
    # query = (
    #     f"""MATCH (start:POI {{latitude: {start_node.latitude}, longitude: {start_node.longitude}}})
    #     MATCH (end:POI) WHERE end IN $end_nodes
    #     CALL gds.alpha.shortestPath.stream({{
    #       nodeQuery: 'MATCH (n) RETURN id(n) as id',
    #       relationshipQuery: 'MATCH (n1)-[r]-(n2) RETURN id(r) as id, id(n1) as source, id(n2) as target, r.weight as weight',
    #       startNode: start,
    #       endNode: end,
    #       relationshipWeightProperty: 'weight'
    #     }})
    #     YIELD nodeId, cost
    #     RETURN gds.util.asNode(nodeId), cost
    #     ;
    #     """
    # )

    query = """
        MATCH (n) RETURN n
    """

    with driver.session() as session:
        result = session.run(query, end_nodes=end_nodes).data()

    shortest_path = []
    for record in result:
        record = record['n']
        shortest_path.append(
            GeospatialPoint(
                record["longitude"],
                record["latitude"],
                record["name"],
                record["city"],
                record["city_code"],
                record["type"],
                record["category"],
                record["notation"],
                record["type"],
            )
        )

    return shortest_path


def compute_itinerary(selected_poi: list[POI], selected_restaurants: list[Restaurant],
                      selected_hosting: list[Hosting], selected_trails: list[Trail]):

    # todo verify this
    # clear all nodes
    # clear_nodes()

    # create all nodes
    create_nodes(selected_poi, selected_restaurants, selected_hosting, selected_trails)

    # select first POI as start node and the rest as end nodes
    start_node = selected_poi[0]
    end_nodes = [(poi.latitude, poi.longitude) for poi in selected_poi]

    shortest_path = compute_shortest_path(start_node, end_nodes)

    print("Shortest Path:", shortest_path)

    return shortest_path


if __name__ == '__main__':
    # Simulated list of selected POIs, Restaurants, Hostings, and Trails with their geospatial points
    # selected_pois = [
    #     GeospatialPoint(2.3522, 48.8566),  # Paris
    #     GeospatialPoint(4.8055, 52.3676),  # Amsterdam
    #     GeospatialPoint(-0.1276, 51.5072),  # London
    #     # ... add more POIs ...
    # ]
    print('**')

