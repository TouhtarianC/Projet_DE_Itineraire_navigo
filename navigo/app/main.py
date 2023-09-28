import json
import logging
from datetime import datetime
from pathlib import Path

import dash
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from pydantic import BaseModel

from navigo.map.dash_app import create_dash_app
from navigo.planner.models import UserData
from navigo.planner.planner import plan_trip


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
async def read_item(request: Request):
    today_date = datetime.now().strftime("%Y-%m-%d")
    return templates.TemplateResponse("index.html", {"request": request, "today_date": today_date})


# Request body model for the POST endpoint
# html is sending us all data in str format
class UserTripRequestInput(BaseModel):

    trip_zone: str
    trip_start: str
    trip_duration: str
    favorite_poi_categories: str
    favorite_restaurant_categories: str
    favorite_hosting_categories: str
    meantime_on_poi: str
    minimal_notation: str
    means_of_transport: str
    sensitivity_to_weather: str
    days_on_hiking: str

    def to_user_data(self) -> UserData:
        return UserData(
            trip_zone=int(self.trip_zone),
            trip_start=self.trip_start,
            trip_duration=int(self.trip_duration),
            favorite_poi_categories=self.favorite_poi_categories.split(", "),
            favorite_restaurant_categories=self.favorite_restaurant_categories.split(", "),
            favorite_hosting_categories=self.favorite_hosting_categories.split(", "),
            meantime_on_poi=float(self.meantime_on_poi),
            minimal_notation=int(self.minimal_notation),
            means_of_transport=self.means_of_transport,
            sensitivity_to_weather=float(self.sensitivity_to_weather),
            days_on_hiking=float(self.days_on_hiking)
        )


# POST endpoint to get recommendations
@app.post("/recommendations/")
async def create_trip_recommendations(user_request_input: UserTripRequestInput):
    try:
        logger.info(f"received planning request: {json.dumps(user_request_input.dict(), indent=4)}")

        geospatial_point_list = plan_trip(user_request_input.to_user_data())

        logger.info(f"result: {geospatial_point_list}")

        # create and serve Dash app
        app.mount("/dash", WSGIMiddleware(create_dash_app(geospatial_point_list).server))

        return
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))

