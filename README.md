# EXPLOREIT

EXPLore Optimal Route and Itinerary Engine for Intelligent Travel

## Architecture
navigo application is based on clean and functional architecture


## TODO
enrich database with Google notes 
fetch top list for each category (wikipedia top most popular attractions in cities)

## Algorithm

### Input
Algorithm input are captured from user data and computed external data

#### User input data:
1. trip zone (region or department or a city) (default to department 33 la Gironde)
2. trip start day + duration of trip in days (default: today and 7 days trip)
3. ordered favorite categories of POI (default to )
4. ordered favorite categories of Restaurant (default to )
5. ordered favorite categories of Hosting (default to )
6. meantime to be spent on POI in days (default to 0.5 day)
7. minimal tolerated notation (default to 3 on 5)
8. means of transport (default to : by foot)
9. sensitivity to weather (default to 5 to 10) 
10. time to be spent on hiking in days (default to half of duration) 


#### External data (computed by application)
1. weather forecast notation by day (for trip duration) and by concerned city 
2. top ten visited POI in selected zone by user
3. top ten visited Restaurants in selected zone by user


#### Internal rules (internal algorithm parameters and rules)
1. criteria weights 

### Scoring and Selection

### Step 1: Geographic Selection of POI & Restaurant & Hosting, Trail
Based on trip zone criteria, get from SQL DB all concerned points 

To find close interesting points to the trip zone, we request "villes voisines" API.
Example:
```sh
 https://www.villes-voisines.fr/getcp.php?cp=91190&rayon=10
```
Where:
        
        cp: The postal code of the commune to search for.
        rayon: The search radius in kilometers.

Then based on the returned communes CP, we use it to fetch concerned points from DB
As result, we have 4 types of SQLAlchemy ORM object lists: POI, Restaurants, Hosting and Trails


### Step 2: Scoring points based on user criteria
Compute a score for each point 

#### scoring function

##### Input
3 objects: rules, point, input

##### Algorithm
start with a zero score

if point is of type POI: 
    if category of POI is in list of favorite categories of POI: 
        increment score by 10 * (length of list - index of category in list)

if point is of type Restaurant: 
    if category of Restaurant is in list of favorite categories of Restaurant: 
        increment score by 10 * (length of list - index of category in list)

if point is of type Hosting: 
    if category of Hosting is in list of favorite categories of Hosting: 
        increment score by 10 * (length of list - index of category in list)

if point has non-zero notation:
    if notation > minimal tolerated notation:
        increment score by 10 * (notation - minimal tolerated notation) 

if point has city:
    if city is in weather forecast:
        increment score by sensitivity to weather * weather notation from weather forecast

return score

##### Output
point score


### Step 3: Compute the maximum points that can be visited 
Determine the maximum number (N) of points that could be visited by dividing duration of vacation on (user input) meantime to be spent on POI


### Step 4: Selection of top ones
After updating the score of all points, sort them by descending score and pick at maximum (N) points from each category list


### Itinerary computation 

The result of Scoring and Selection step is 4 lists of the best suitable elements for the user, 4 lists of POI, Restaurant, Hosting and Trails.
Each element of these lists has longitude and latitude properties and thus can be treated as a geospatial point.

The next step is to compute possible Trip Itineraries for user by applying the following rules:
compute the shortest path to visit all POI that were selected
choose and add two Restaurants per day (lunch and dinner) that are close to the path
choose one Hosting per day (to sleep)


### Itinerary display 

Represent the final Itinerary on a Map and display it to the user

