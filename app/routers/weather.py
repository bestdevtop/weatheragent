import logging

from fastapi import APIRouter, Request

from app.models.weather import WeatherResponse
from app.services.retell import extract_caller_phone, extract_city
from app.services.sms import send_coat_reminder, twilio_configured
from app.services.weather import WeatherError, build_weather_response, fetch_weather

logger = logging.getLogger(__name__)
router = APIRouter(tags=["weather"])


@router.post("/webhook/weather-check", response_model=WeatherResponse)
async def check_weather(request: Request) -> WeatherResponse:
    payload = await request.json()
    city = extract_city(payload)
    caller_phone = extract_caller_phone(payload)

    if not city:
        return WeatherResponse(
            message="I couldn't find a city name. Which town would you like me to check?"
        )

    try:
        weather = await fetch_weather(city)
    except WeatherError as exc:
        return WeatherResponse(message=exc.message)

    result = build_weather_response(weather)

    if not result["is_cold"]:
        return WeatherResponse(**result)

    sms_sent = False

    if caller_phone and twilio_configured():
        try:
            send_coat_reminder(weather, caller_phone)
            sms_sent = True
        except Exception:
            logger.exception("Failed to send Twilio SMS for city=%s", city)
    elif not caller_phone:
        logger.warning("Cold weather for %s but no caller phone in Retell payload.", city)

    result = build_weather_response(weather, sms_sent=sms_sent)
    return WeatherResponse(**result)
