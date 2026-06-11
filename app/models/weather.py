from pydantic import BaseModel, Field


class RetellWeatherRequest(BaseModel):
    name: str | None = None
    args: dict | None = None
    city: str | None = None

    model_config = {"extra": "allow"}


class WeatherResponse(BaseModel):
    temperature_f: float | None = None
    description: str | None = None
    city: str | None = None
    is_cold: bool = False
    message: str
