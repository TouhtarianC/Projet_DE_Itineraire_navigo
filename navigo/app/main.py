import dataclasses
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from pydantic import BaseModel

from navigo.db import get_restaurants_by_zone, get_poi_by_zone, get_hosting_by_zone, get_trails_by_zone, \
    get_wc_by_zone
from navigo.external import get_zipcode
from navigo.map import create_dash_app
from navigo.planner.models import UserData
from navigo.planner.planner import plan_trip
from navigo.db import get_poi_types, get_poi_themes


logger = logging.getLogger(__name__)


app = FastAPI()
app.mount("/static",
          StaticFiles(directory=str(
              Path(Path(__file__).resolve().parent, 'static'))
          ))

templates = Jinja2Templates(
    directory=str(
        Path(Path(__file__).resolve().parent, 'templates'))
)


@app.get("/favicon.ico")
async def get_favicon():
    return FileResponse("static/img/favicon.ico")


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    today_date = datetime.now().strftime("%Y-%m-%d")
    try:
        types = get_poi_types()
        themes = get_poi_themes()
        logger.info(
            f"""Serving form with types = ({[t['NAME'] for t in types]})
            Serving form with themes = ({[t['NAME'] for t in themes]})""")
    except Exception as e:
        msg = f"unable to fetch themes and/or types: {str(e)}"
        logger.error(msg)
        raise
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "today_date": today_date, "types": types, "themes": themes})


# Request body model for the POST endpoint
# html is sending us all data in str format
class UserTripRequestInput(BaseModel):
    trip_zone: str
    trip_start: str
    trip_duration: str
    # favorite_poi_categories: list
    favorite_poi_type_list: list
    favorite_poi_theme_list: list
    favorite_restaurant_categories: str
    favorite_hosting_categories: str
    # meantime_on_poi: str
    # minimal_notation: str
    means_of_transport: str
    sensitivity_to_weather: str
    days_on_hiking: str

    def to_user_data(self) -> UserData:
        # check if trip zone a zip code, else translate it
        try:
            _trip_zone = int(self.trip_zone)
        except ValueError:
            _trip_zone = get_zipcode(self.trip_zone)

        return UserData(
            trip_zone=_trip_zone,
            trip_start=self.trip_start,
            trip_duration=int(self.trip_duration),
            # favorite_poi_categories=[s.lower() for s in self.favorite_poi_categories.split(", ")],
            favorite_poi_type_list=self.favorite_poi_type_list,
            favorite_poi_theme_list=self.favorite_poi_theme_list,
            favorite_restaurant_categories=[
                s.lower() for s in self.favorite_restaurant_categories.split(", ")],
            favorite_hosting_categories=[
                s.lower() for s in self.favorite_hosting_categories.split(", ")],
            # meantime_on_poi=float(self.meantime_on_poi),
            # minimal_notation=int(self.minimal_notation),
            means_of_transport=self.means_of_transport,
            sensitivity_to_weather=bool(self.sensitivity_to_weather),
            days_on_hiking=float(self.days_on_hiking)
        )


# POST endpoint to get recommendations
@app.post("/recommendations/")
async def create_trip_recommendations(user_request_input: UserTripRequestInput):
    try:
        logger.info(f"""received planning request: {json.dumps(
            user_request_input.model_dump(),
            indent=4)}""")

        geospatial_point_list = plan_trip(user_request_input.to_user_data())

        logger.info(f"result: {geospatial_point_list}")

        # create and serve Dash app
        app.mount(
            "/dash", WSGIMiddleware(
                create_dash_app(geospatial_point_list).server))

        return
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Technical APIs to fetch DATA
@app.get("/data/pois")
async def get_pois(zip_code: Annotated[str, 'zip code'], rayon: Annotated[str, 'rayon']):
    try:
        _zip_code = int(zip_code)
        _rayon = int(rayon)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    res = get_poi_by_zone(_zip_code, _rayon)
    res = [dataclasses.asdict(r) for r in res]

    return res


@app.get("/data/restaurants")
async def get_restaurants(zip_code: Annotated[str, 'zip code'], rayon: Annotated[str, 'rayon']):
    try:
        _zip_code = int(zip_code)
        _rayon = int(rayon)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    res = get_restaurants_by_zone(_zip_code, _rayon)
    res = [dataclasses.asdict(r) for r in res]

    return res


@app.get("/data/hostings")
async def get_hosting(zip_code: Annotated[str, 'zip code'], rayon: Annotated[str, 'rayon']):
    try:
        _zip_code = int(zip_code)
        _rayon = int(rayon)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    res = get_hosting_by_zone(_zip_code, _rayon)
    res = [dataclasses.asdict(r) for r in res]

    return res


@app.get("/data/trails")
async def get_trails(zip_code: Annotated[str, 'zip code'], rayon: Annotated[str, 'rayon']):
    try:
        _zip_code = int(zip_code)
        _rayon = int(rayon)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    res = get_trails_by_zone(_zip_code, _rayon)
    res = [dataclasses.asdict(r) for r in res]

    return res


@app.get("/data/wcs")
async def get_wcs(zip_code: Annotated[str, 'zip code'], rayon: Annotated[str, 'rayon']):
    try:
        _zip_code = int(zip_code)
        _rayon = int(rayon)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    res = get_wc_by_zone(_zip_code, _rayon)
    res = [dataclasses.asdict(r) for r in res]

    return res

# todo api du modèle ML ?
# todo: dependeing on mean of transport => define search zone
