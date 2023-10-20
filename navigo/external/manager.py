from navigo.planner.models import ExternalData


def get_weather_forecast(ville, start_date, end_date):
    '''
    fFnction that takes a city name and travel start and end dates, and returns True if the weather is favorable.during the specified period, and False otherwise. 
    Weather is considered favorable if there is little to no rain and temperature between 10 and 30°.
    If, for any reasy, there is no weather information available, returns True()."
    '''
    KEY = "bd5e378503939ddaee76f12ad7a97608"
    url = f"https://api.openweathermap.org/data/2.5/forecast/daily?q={ville}&cnt=16&appid={KEY}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data_dict = response.json()
        normalized_data = pd.json_normalize(data_dict).list[0]
        df_brut = pd.DataFrame(normalized_data)

        # conversion date unix en date
        df_brut["date"] = pd.to_datetime(df_brut["dt"], unit='s')
        # température ressentie
        df_brut["tempRessentie"] = df_brut["feels_like"].apply(lambda x: round(x["day"]))
        # ID et description de la météo
        df_brut[["idTemps", "tempsPrevu"]] = df_brut["weather"].apply(lambda x: pd.Series((x[0]["id"], x[0]["description"])))
        # url : https://openweathermap.org/weather-conditions
        # si la météo est clémente. Si un peu de pluie (id = 500) on dit que c'est clément
        df_brut["condition"] = df_brut.apply(lambda row: (row['idTemps'] >= 800 and 10 <= row['tempRessentie'] <= 30) or row['idTemps'] == 500, axis=1)

        # Df avec les infos qui m'intéressent
        df_filtered = df_brut[['date', 'tempRessentie', 'idTemps', 'tempsPrevu', 'condition']]

        start_date = pd.Timestamp(start_date)
        # ajout d'une journée poru avoir le premier jour
        end_date = pd.Timestamp(end_date) + pd.Timedelta(seconds=86400)
        
        filtered_data = df_filtered[(df_filtered['date'] >= start_date)& (df_filtered['date'] <= end_date)]

        # Afficher pour un log / vérif
        for index, row in filtered_data.iterrows():
            date = row['date'].strftime('%Y-%m-%d')
            temperature = row['tempRessentie']
            id_temps = row['idTemps']
            clemente = row['condition']
            city = ville 
            
            result = [date, city, temperature, id_temps, clemente]
            print(result)
        
        #print(filtered_data['condition'])
        result = all(filtered_data['condition'])
        # si des prévision sont absentes, renvoie True
        return result


    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données : {e}")
        return True
    except ValueError as e:
        print(f"Erreur lors de la conversion des données : {e}")
        return True


def get_most_popular_poi_by_zone(zone: int) -> list:
    # todo Implement the logic
    return []


def get_most_popular_restaurant_by_zone(zone: int) -> list:
    # todo Implement the logic
    return []


def get_external_data(zone: int) -> ExternalData:
    return ExternalData(
        weather_forecast=get_weather_forecast_by_zone(zone),
        top_poi_list=get_most_popular_poi_by_zone(zone),
        top_restaurant_list=get_most_popular_restaurant_by_zone(zone)
    )
