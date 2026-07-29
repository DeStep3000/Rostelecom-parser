from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Tariff:
    """Данные одного тарифа для выгрузки в Excel."""

    name: str
    channels: int | None
    speed_mbps: int | float
    monthly_fee: int
