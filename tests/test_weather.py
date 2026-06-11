import pytest

from app.services.retell import extract_caller_phone, extract_city
from app.services.weather import build_sms_message, build_weather_response


def test_extract_city_from_retell_payload():
    payload = {"name": "check_weather", "args": {"city": "London"}}
    assert extract_city(payload) == "London"


def test_extract_city_from_nested_body():
    payload = {"body": {"args": {"city": "Paris"}}}
    assert extract_city(payload) == "Paris"


def test_extract_city_missing():
    assert extract_city({"args": {}}) is None


def test_extract_caller_phone_inbound():
    payload = {
        "args": {"city": "London"},
        "call": {
            "direction": "inbound",
            "from_number": "+15559876543",
        },
    }
    assert extract_caller_phone(payload) == "+15559876543"


def test_extract_caller_phone_outbound():
    payload = {
        "call": {
            "direction": "outbound",
            "to_number": "+15551234567",
        },
    }
    assert extract_caller_phone(payload) == "+15551234567"


def test_build_weather_response_cold_with_sms():
    weather = {
        "name": "Reykjavik",
        "main": {"temp": 39},
        "weather": [{"description": "snow"}],
    }
    result = build_weather_response(weather, threshold_f=50, sms_sent=True)
    assert result["is_cold"] is True
    assert "coat reminder" in result["message"]
    assert "°F" in result["message"]


def test_build_weather_response_cold_without_sms():
    weather = {
        "name": "Reykjavik",
        "main": {"temp": 39},
        "weather": [{"description": "snow"}],
    }
    result = build_weather_response(weather, threshold_f=50)
    assert result["is_cold"] is True
    assert "bring a coat" in result["message"]


def test_build_weather_response_cold_with_email():
    weather = {
        "name": "Reykjavik",
        "main": {"temp": 39},
        "weather": [{"description": "snow"}],
    }
    result = build_weather_response(weather, threshold_f=50, email_sent=True)
    assert result["is_cold"] is True
    assert "emailed you" in result["message"]


    weather = {
        "name": "Dubai",
        "main": {"temp": 89},
        "weather": [{"description": "clear sky"}],
    }
    result = build_weather_response(weather, threshold_f=50)
    assert result["is_cold"] is False
    assert "No coat needed" in result["message"]


def test_build_weather_response_boundary():
    weather = {
        "name": "Test",
        "main": {"temp": 50},
        "weather": [{"description": "clouds"}],
    }
    result = build_weather_response(weather, threshold_f=50)
    assert result["is_cold"] is False


def test_build_sms_message():
    weather = {"name": "London", "main": {"temp": 45}}
    sms = build_sms_message(weather)
    assert "London" in sms
    assert "45°F" in sms
    assert "Bring a coat" in sms
