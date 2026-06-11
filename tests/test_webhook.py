from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_webhook_missing_city():
    response = client.post(
        "/webhook/weather-check",
        json={"name": "check_weather", "args": {}},
    )
    assert response.status_code == 200
    data = response.json()
    assert "city" in data["message"].lower()


def test_webhook_invalid_city_without_api_key():
    response = client.post(
        "/webhook/weather-check",
        json={"name": "check_weather", "args": {"city": "London"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
