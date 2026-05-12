from dataclasses import dataclass
from collections.abc import Callable


@dataclass
class VehicleInfo:
    vin: str
    model: str
    family: str
    model_year: int
    market: str


class VINLookupService:
    def __init__(self, vehicle_resolver: Callable[[str], VehicleInfo | None] | None = None) -> None:
        self._vehicle_resolver = vehicle_resolver

    _mock_db: dict[str, VehicleInfo] = {
        "AK550-POC-0001": VehicleInfo(
            vin="AK550-POC-0001",
            model="AK550",
            family="Scooter GT",
            model_year=2022,
            market="ES",
        ),
        "AK550-POC-0002": VehicleInfo(
            vin="AK550-POC-0002",
            model="AK550",
            family="Scooter GT",
            model_year=2023,
            market="ES",
        ),
        "AK550-POC-0003": VehicleInfo(
            vin="AK550-POC-0003",
            model="AK550",
            family="Scooter GT",
            model_year=2024,
            market="ES",
        ),
        "XCITING-POC-0001": VehicleInfo(
            vin="XCITING-POC-0001",
            model="Xciting 400",
            family="Scooter GT",
            model_year=2021,
            market="ES",
        ),
    }

    def resolve(self, raw_vin: str) -> VehicleInfo | None:
        vin = raw_vin.strip().upper()
        if self._vehicle_resolver is not None:
            return self._vehicle_resolver(vin)
        return self._mock_db.get(vin)
