from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx

from app.core.config import settings
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


def fetch_weather_signals() -> list[WeatherSignal]:
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
                    started_at=datetime.now(UTC) - timedelta(minutes=15),
                    weather_api_raw={"source": "mock_weather", "event_id": str(uuid4())},
                )
            )
        return signals

    return []


def issue_mock_payout_reference(claim_id: str) -> str:
    return f"mock_{claim_id[:8]}"
