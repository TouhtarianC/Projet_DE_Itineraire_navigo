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
8. means of transport (default to : by foot) => Not Implemented
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
User may specify city name or a zip code, either cases, the search of points is based on zip codes

To find close interesting points to the trip zone, we request "villes voisines" API.
Example:
```sh
 https://www.villes-voisines.fr/getcp.php?cp=91190&rayon=10
```
Where:
        
        cp: The postal code of the commune to search for.
        rayon: The search radius in kilometers.

Then based on the returned communes zip codes, we use it to fetch concerned points from DB
As result, we have 4 types of SQLAlchemy ORM object lists: POI, Restaurants, Hosting and Trails

The search is iterative, we search in close radius then we increase it to met needed points limit

### Step 2: Scoring points based on user criteria
Compute a score for each point 

#### scoring function

##### Input
Scoring function takes 3 objects as input: rules (scoring weights), point (POI, Restaurant, ..) to score, user input

##### Algorithm
start with the default zero score

if point is of type POI: 
    if the category of POI is in the list of the user favorite categories of POI: 
        increment score by 'user preference weight' * (length of list - index of category in list)
        this increments most favorite categories (lower index in list)

    if point is present in the list of most popular POI:
        increment score by 'popularity weight' * (length of list - index of POI in list)

    if user is sensitive to the weather:
        if the weather forecast is good for the trip date and location:
            if point is of type external activity:
                 increment score by 'weather weight'
        
        else if weather forecast is bad for the trip date and location:
            if point is of type internal activity:
                 increment score by 'weather weight'

if point is of type Restaurant: 
    if the category of Restaurant is in the list of user favorite categories of Restaurant: 
        increment score by 'user preference weight' * (length of list - index of category in list)

    if point is present in the list of most popular Restaurants:
        increment score by 'popularity weight' * (length of list - index of Restaurant in list)

if point is of type Hosting: 
    if the category of Hosting is in the list of user favorite categories of Hosting: 
        increment score by 'user preference weight' * (length of list - index of category in list)

if point has non-zero notation:
    if notation > minimal tolerated notation:
        increment score by 'notation weight' * (notation - minimal tolerated notation) 


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
