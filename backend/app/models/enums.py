from enum import Enum


class Platform(str, Enum):
    zomato = "zomato"
    swiggy = "swiggy"
    zepto = "zepto"
    blinkit = "blinkit"


class CoverageTier(str, Enum):
    basic = "basic"
    standard = "standard"
    premium = "premium"


class PolicyStatus(str, Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class DisruptionEventType(str, Enum):
    heavy_rain = "heavy_rain"
    extreme_heat = "extreme_heat"
    flood = "flood"
    aqi = "aqi"
    curfew = "curfew"
    outage = "outage"


class ClaimStatus(str, Enum):
    auto_approved = "auto_approved"
    manual_review = "manual_review"
    rejected = "rejected"
    paid = "paid"


class PayoutStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class PaymentMethod(str, Enum):
    upi = "upi"
    bank_transfer = "bank_transfer"
