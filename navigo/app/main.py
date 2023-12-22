import dataclasses
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from a2wsgi import WSGIMiddleware
from pydantic import BaseModel
from starlette.routing import Mount

from navigo.app.paginate import PageParams, PagedResponseSchema, paginate

from navigo.db import get_restaurants_by_zone, get_poi_by_zone, \
    get_hosting_by_zone, get_trails_by_zone, get_wc_by_zone, get_poi_types, \
    get_poi_themes, get_restaurants_types, get_hostings_types, \
    get_poi_categories_of_theme, get_poi_categories_of_type
from navigo.external import get_zipcode
from navigo.map import create_dash_app
from navigo.planner.models import UserData
from navigo.planner.planner import plan_trip
from navigo.settings import DEBUG

from navigo.planner.models import POI, Restaurant, Hosting, Trail, WC

logger = logging.getLogger(__name__)


app = FastAPI(debug=DEBUG)
app.mount("/static",
          StaticFiles(directory=str(
              Path(Path(__file__).resolve().parent, 'static'))
          ))

templates = Jinja2Templates(
    directory=str(
        Path(Path(__file__).resolve().parent, 'templates'))
)


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    today_date = datetime.now().strftime("%Y-%m-%d")
    try:
        # types = get_poi_types()
        # themes = get_poi_themes()
        types_agg = get_poi_categories_of_type()
        themes_agg = get_poi_categories_of_theme()
        rest_types = get_restaurants_types()
        hosting_types = get_hostings_types()
        logger.info(
            f"""
            Serving form with categories of types = ({types_agg})
            Serving form with categories of themes = ({themes_agg})
            Serving form with rest_types = ({[t['TYPE'] for t in rest_types]})
            Serving form with hosting_types = (
                {[t['TYPE'] for t in hosting_types]})""")
    except Exception as e:
        msg = f"unable to fetch themes and/or types: {str(e)}"
        logger.error(msg)
        raise
    return templates.TemplateResponse(
        "index.html",
        {"request": request,
         "today_date": today_date,
         "types": types_agg,
         "themes": themes_agg,
         "rest_types": rest_types,
         "hosting_types": hosting_types})


# Request body model for the POST endpoint
# html is sending us all data in str format
class UserTripRequestInput(BaseModel):
    trip_zone: str
    trip_start: str
    trip_duration: str
    # favorite_poi_type_list: list
    # favorite_poi_theme_list: list
    favorite_category_poi_type_list: list
    favorite_category_poi_theme_list: list
    favorite_restaurant_categories: list
    favorite_hosting_categories: list
    # means_of_transport: str
    sensitivity_to_weather: str
    days_on_hiking: str

    def to_user_data(self) -> UserData:
        # check if trip zone a zip code, else translate it
        try:
            _trip_zone = int(self.trip_zone)
        except ValueError:
            _trip_zone = get_zipcode(self.trip_zone)

        try:
            # transform from a request of a list of categories to a list
            # of types (or themes) it will allowed to stay with a list
            # of poi types and a list of poi themes for the UserData
            poi_type_list = get_poi_types()
            # logger.info(f"poi_type_list = {poi_type_list}")
            poi_theme_list = get_poi_themes()
            favorite_poi_type_list, favorite_poi_theme_list = [], []
            for t in poi_type_list:
                # logger.info(f"t.CATEGORY = {t.CATEGORY}")
                if t.CATEGORY in self.favorite_category_poi_type_list:
                    favorite_poi_type_list.append(t.NAME)
            for t in poi_theme_list:
                if t.CATEGORY in self.favorite_category_poi_theme_list:
                    favorite_poi_theme_list.append(t.NAME)
        except Exception as e:
            logger.error(e)
        logger.info(f"favorite_poi_type_list = {favorite_poi_type_list}")
        logger.info(f"favorite_poi_theme_list = {favorite_poi_theme_list}")

        return UserData(
            trip_zone=_trip_zone,
            trip_start=self.trip_start,
            trip_duration=int(self.trip_duration),
            favorite_poi_type_list=favorite_poi_type_list,
            favorite_poi_theme_list=favorite_poi_theme_list,
            favorite_restaurant_categories=self.favorite_restaurant_categories,
            favorite_hosting_categories=self.favorite_hosting_categories,
            # means_of_transport=self.means_of_transport,
            sensitivity_to_weather=bool(self.sensitivity_to_weather == 'true'),
            days_on_hiking=float(self.days_on_hiking)
        )


# POST endpoint to get recommendations
@app.post("/recommendations/")
async def create_trip_recommendations(
        user_request_input: UserTripRequestInput):
    try:
        logger.info(f"""received planning request: {json.dumps(
            user_request_input.model_dump(),
            indent=4)}""")

        geospatial_point_list, selected_toilets = plan_trip(
            user_request_input.to_user_data())

        # logger.info(f"result: {geospatial_point_list}")

        # create and serve Dash app
        _dash_app = create_dash_app(geospatial_point_list, selected_toilets)

        # delete any /dash mount before updating the dashboard
        for index, route in enumerate(app.routes):
            if isinstance(route, Mount) and route.path == "/dash":
                del app.routes[index]
                break

        app.mount(
            "/dash", WSGIMiddleware(
                _dash_app.server))

        return
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Technical APIs to fetch DATA
@app.get("/favicon.ico")
async def get_favicon():
    return FileResponse("navigo/app/static/img/favicon.ico", 200)


@app.get("/data/pois", response_model=PagedResponseSchema[POI])
async def get_pois(
    zip_code: Annotated[str, 'zip code'],
    rayon: Annotated[str, 'rayon'],
    request: Request,
    page_params: PageParams = Depends()
):
    try:
        _zip_code = int(zip_code)
        _rayon = int(rayon)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    res = get_poi_by_zone(_zip_code, _rayon)
    if res is None:
        logger.warning(f"no POI found for zone {_zip_code} \
                       with rayon {_rayon}")
        raise HTTPException(status_code=404, detail="no POI found \
                            for this zone")
    try:
        res = [dataclasses.asdict(r) for r in res]
    except TypeError as e:
        logger.error(f"unable to convert POI to dict: {res}")
        raise HTTPException(status_code=500, detail=str(e))
    return paginate(page_params, res, POI)


@app.get("/data/restaurants", response_model=PagedResponseSchema[Restaurant])
async def get_restaurants(
    zip_code: Annotated[str, 'zip code'],
    rayon: Annotated[str, 'rayon'],
    request: Request,
    page_params: PageParams = Depends()
):
    try:
        _zip_code = int(zip_code)
        _rayon = int(rayon)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    res = get_restaurants_by_zone(_zip_code, _rayon)
    if res is None:
        logger.warning(f"no Restaurants found for zone {_zip_code} \
                       with rayon {_rayon}")
        raise HTTPException(status_code=404, detail="no restaurants found \
                            for this zone")
    try:
        res = [dataclasses.asdict(r) for r in res]
    except TypeError as e:
        logger.error(f"unable to convert restaurants to dict: {res}")
        raise HTTPException(status_code=500, detail=str(e))

    return paginate(page_params, res, Restaurant)


@app.get("/data/hostings", response_model=PagedResponseSchema[Hosting])
async def get_hosting(
    zip_code: Annotated[str, 'zip code'],
    rayon: Annotated[str, 'rayon'],
    request: Request,
    page_params: PageParams = Depends()
):
    try:
        _zip_code = int(zip_code)
        _rayon = int(rayon)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    res = get_hosting_by_zone(_zip_code, _rayon)
    if res is None:
        logger.warning(f"no hosting found for zone {_zip_code} \
                       with rayon {_rayon}")
        raise HTTPException(status_code=404, detail="no hosting found \
                            for this zone")
    try:
        res = [dataclasses.asdict(r) for r in res]
    except TypeError as e:
        logger.error(f"unable to convert hostings to dict: {res}")
        raise HTTPException(status_code=500, detail=str(e))

    return paginate(page_params, res, Hosting)


@app.get("/data/trails", response_model=PagedResponseSchema[Trail])
async def get_trails(
    zip_code: Annotated[str, 'zip code'],
    rayon: Annotated[str, 'rayon'],
    request: Request,
    page_params: PageParams = Depends()
):
    try:
        _zip_code = int(zip_code)
        _rayon = int(rayon)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    res = get_trails_by_zone(_zip_code, _rayon)
    if res is None:
        logger.warning(f"no trail found for zone {_zip_code} \
                       with rayon {_rayon}")
        raise HTTPException(status_code=404, detail="no trail found \
                            for this zone")
    try:
        res = [dataclasses.asdict(r) for r in res]
    except TypeError as e:
        logger.error(f"unable to convert trail to dict: {res}")
        raise HTTPException(status_code=500, detail=str(e))

    return paginate(page_params, res, Trail)


@app.get("/data/wcs", response_model=PagedResponseSchema[WC])
async def get_wcs(
    zip_code: Annotated[str, 'zip code'],
    rayon: Annotated[str, 'rayon'],
    request: Request,
    page_params: PageParams = Depends()
):
    try:
        _zip_code = int(zip_code)
        _rayon = int(rayon)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    res = get_wc_by_zone(_zip_code, _rayon)
    if res is None:
        logger.warning(f"no WC found for zone {_zip_code} \
                       with rayon {_rayon}")
        raise HTTPException(status_code=404, detail="no wc found \
                            for this zone")
    try:
        res = [dataclasses.asdict(r) for r in res]
    except TypeError as e:
        logger.error(f"unable to convert wc to dict: {res}")
        raise HTTPException(status_code=500, detail=str(e))

    return paginate(page_params, res, WC)

# todo api du modèle ML ?
# todo: dependeing on mean of transport => define search zone


def main():
    uvicorn.run("navigo.app.main:app", host="0.0.0.0",
                port=8000, log_level="info")


if __name__ == "__main__":
    main()
