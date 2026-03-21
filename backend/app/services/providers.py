from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

import httpx

from app.core.config import settings
from app.core.time import utcnow
from app.models.enums import DisruptionEventType


@dataclass
class SmsDelivery:
    delivery_mode: str
    provider_message_id: str


def send_otp_sms(phone: str, otp_code: str) -> SmsDelivery:
    if settings.use_mock_sms or not settings.twilio_account_sid:
        return SmsDelivery(delivery_mode="mock", provider_message_id=f"mock-sms-{phone}")

    payload = {
        "To": f"+91{phone}",
        "From": settings.twilio_phone_number,
        "Body": f"Your GigShield OTP is {otp_code}. It expires in {settings.otp_ttl_minutes} minutes.",
    }
    response = httpx.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json",
        data=payload,
        auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        timeout=10.0,
    )
    response.raise_for_status()
    message_sid = response.json()["sid"]
    return SmsDelivery(delivery_mode="twilio", provider_message_id=message_sid)


@dataclass
class WeatherSignal:
    event_type: DisruptionEventType
    zone_id: str
    severity: int
    started_at: datetime
    weather_api_raw: dict


def _city_from_zone_id(zone_id: str) -> str:
    city_key = zone_id.split("_", 1)[0].strip().lower()
    return {
        "chennai": "Chennai",
        "mumbai": "Mumbai",
        "delhi": "Delhi",
        "bengaluru": "Bengaluru",
        "bangalore": "Bengaluru",
    }.get(city_key, city_key.title())


def _severity_from_rainfall(rainfall_mm_per_hr: float) -> int:
    if rainfall_mm_per_hr >= 50:
        return 4
    if rainfall_mm_per_hr >= 25:
        return 3
    if rainfall_mm_per_hr >= 15:
        return 2
    return 1


def _severity_from_temp(temp_c: float) -> int:
    if temp_c >= 48:
        return 4
    if temp_c >= 45:
        return 3
    if temp_c >= 43:
        return 2
    return 1


def _severity_from_aqi(aqi_band: int) -> int:
    if aqi_band >= 5:
        return 4
    if aqi_band >= 4:
        return 3
    if aqi_band >= 3:
        return 2
    return 1


def _fetch_openweathermap_payload(city: str) -> dict:
    geo_response = httpx.get(
        "https://api.openweathermap.org/geo/1.0/direct",
        params={"q": city, "limit": 1, "appid": settings.openweathermap_api_key},
        timeout=10.0,
    )
    geo_response.raise_for_status()
    locations = geo_response.json()
    if not locations:
        return {}

    location = locations[0]
    lat = float(location["lat"])
    lon = float(location["lon"])

    weather_response = httpx.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"lat": lat, "lon": lon, "units": "metric", "appid": settings.openweathermap_api_key},
        timeout=10.0,
    )
    weather_response.raise_for_status()

    air_response = httpx.get(
        "https://api.openweathermap.org/data/2.5/air_pollution",
        params={"lat": lat, "lon": lon, "appid": settings.openweathermap_api_key},
        timeout=10.0,
    )
    air_response.raise_for_status()

    weather_data = weather_response.json()
    air_data = air_response.json()
    rain_1h = float(weather_data.get("rain", {}).get("1h") or 0)
    temp_c = float(weather_data.get("main", {}).get("temp") or 0)
    pressure = int(weather_data.get("main", {}).get("pressure") or 0)
    humidity = int(weather_data.get("main", {}).get("humidity") or 0)
    aqi_band = int(air_data.get("list", [{}])[0].get("main", {}).get("aqi") or 0)

    return {
        "source": "openweathermap",
        "city": location.get("name", city),
        "country": location.get("country"),
        "lat": lat,
        "lon": lon,
        "weather_id": weather_data.get("weather", [{}])[0].get("id"),
        "weather_main": weather_data.get("weather", [{}])[0].get("main"),
        "weather_description": weather_data.get("weather", [{}])[0].get("description"),
        "rainfall_mm_per_hr": rain_1h,
        "temp_c": temp_c,
        "pressure_hpa": pressure,
        "humidity_pct": humidity,
        "aqi": 450 if aqi_band >= 4 else 300 if aqi_band == 3 else 100 * aqi_band,
        "aqi_band": aqi_band,
    }


def fetch_weather_signals(zone_ids: list[str] | None = None) -> list[WeatherSignal]:
    if settings.use_mock_weather or not settings.openweathermap_api_key:
        signals: list[WeatherSignal] = []
        for raw_event in settings.mock_weather_events.split(";"):
            if not raw_event.strip():
                continue
            event_type, zone_id, severity = [value.strip() for value in raw_event.split("|")]
            signals.append(
                WeatherSignal(
                    event_type=DisruptionEventType(event_type),
                    zone_id=zone_id,
                    severity=int(severity),
                    started_at=utcnow() - timedelta(minutes=15),
                    weather_api_raw={"source": "mock_weather", "event_id": str(uuid4())},
                )
            )
        return signals

    signals: list[WeatherSignal] = []
    target_zone_ids = zone_ids or []
    for zone_id in target_zone_ids:
        city = _city_from_zone_id(zone_id)
        try:
            payload = _fetch_openweathermap_payload(city)
        except httpx.HTTPError:
            continue

        if not payload:
            continue

        rainfall = float(payload.get("rainfall_mm_per_hr") or 0)
        temp_c = float(payload.get("temp_c") or 0)
        aqi_band = int(payload.get("aqi_band") or 0)
        weather_main = str(payload.get("weather_main") or "").lower()
        weather_id = int(payload.get("weather_id") or 0)
        weather_description = str(payload.get("weather_description") or "").lower()

        if rainfall >= 15 or weather_id // 100 == 5 or "rain" in weather_main or "rain" in weather_description:
            signals.append(
                WeatherSignal(
                    event_type=DisruptionEventType.heavy_rain,
                    zone_id=zone_id,
                    severity=_severity_from_rainfall(rainfall),
                    started_at=utcnow() - timedelta(minutes=15),
                    weather_api_raw=payload,
                )
            )

        if temp_c >= 43:
            signals.append(
                WeatherSignal(
                    event_type=DisruptionEventType.extreme_heat,
                    zone_id=zone_id,
                    severity=_severity_from_temp(temp_c),
                    started_at=utcnow() - timedelta(minutes=15),
                    weather_api_raw=payload,
                )
            )

        if aqi_band >= 4:
            signals.append(
                WeatherSignal(
                    event_type=DisruptionEventType.aqi,
                    zone_id=zone_id,
                    severity=_severity_from_aqi(aqi_band),
                    started_at=utcnow() - timedelta(minutes=15),
                    weather_api_raw=payload,
                )
            )

        if rainfall >= 45:
            signals.append(
                WeatherSignal(
                    event_type=DisruptionEventType.flood,
                    zone_id=zone_id,
                    severity=4,
                    started_at=utcnow() - timedelta(minutes=15),
                    weather_api_raw=payload,
                )
            )

    return signals


def issue_mock_payout_reference(claim_id: str) -> str:
    return f"mock_{claim_id[:8]}"
