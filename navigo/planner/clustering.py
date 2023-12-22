from sklearn.cluster import KMeans
import pandas as pd

from navigo.planner.models import POI


def clustering_by_days(nb_days: int, POI_List: list[POI]):
    """
    function that apply KMeans clustering to divided POIs by cluster
    for each travelling days and store the result into cluster attribute
    of each POI's in InternalNodesData
    """
    df_POI_coord = pd.DataFrame(POI_List)

    # Creating an instance of KMeans to find 1 cluster by travel days
    kmeans_1 = KMeans(n_clusters=nb_days, n_init=10)
    # Using fit_predict to cluster the dataset
    X = df_POI_coord[['longitude', 'latitude']].values
    predictions = kmeans_1.fit_predict(X)

    # store result into cluster attribut of POIs object
    for index, poi in enumerate(POI_List):
        poi.cluster = predictions[index]


if __name__ == "__main__":
    # ecrire un test en bouchonnant les données
    pass
