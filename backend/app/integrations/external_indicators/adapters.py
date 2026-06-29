from __future__ import annotations

import json
import math
from collections.abc import Callable
from datetime import date, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from defusedxml import ElementTree

from app.integrations.external_indicators.base import ExternalIndicatorsAdapter
from app.integrations.external_indicators.types import ExternalIndicatorPoint
from app.services.data_generator_config import RU_HOLIDAYS, event_pressure_for_day


def _date_range(*, start_date: date, end_date: date) -> list[date]:
    total_days = (end_date - start_date).days
    return [start_date + timedelta(days=offset) for offset in range(total_days + 1)]


def _forward_fill_daily_points(
    *,
    start_date: date,
    end_date: date,
    source: dict[date, float],
    unit: str,
) -> list[ExternalIndicatorPoint]:
    if not source:
        return []

    dates = _date_range(start_date=start_date, end_date=end_date)
    first_known = min(source.keys())
    last_value = source[first_known]
    points: list[ExternalIndicatorPoint] = []

    for current_date in dates:
        if current_date in source:
            last_value = source[current_date]
        points.append(
            ExternalIndicatorPoint(
                indicator_date=current_date,
                value_numeric=last_value,
                unit=unit,
                metadata={},
            )
        )
    return points


class BrentEiaAdapter(ExternalIndicatorsAdapter):
    provider_name = "eia"
    indicator_codes = ("crude_brent_usd",)

    def fetch_live_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        normalized_code = self.validate_indicator_code(indicator_code, self.indicator_codes)
        params = {
            "api_key": "DEMO_KEY",
            "frequency": "daily",
            "data[0]": "value",
            "facets[product][]": "EPCBRENT",
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": "0",
            "length": "5000",
        }
        endpoint = "https://api.eia.gov/v2/petroleum/pri/spt/data/?" + urlencode(params, doseq=True)
        payload = _read_json_from_url(endpoint)
        rows = payload.get("response", {}).get("data", [])
        if not isinstance(rows, list) or not rows:
            raise RuntimeError(f"{normalized_code}: no live EIA rows returned")

        values_by_date: dict[date, float] = {}
        for item in rows:
            if not isinstance(item, dict):
                continue
            raw_period = item.get("period")
            raw_value = item.get("value")
            if not isinstance(raw_period, str):
                continue
            try:
                point_date = date.fromisoformat(raw_period)
                point_value = float(raw_value)
            except (TypeError, ValueError):
                continue
            values_by_date[point_date] = point_value

        points = _forward_fill_daily_points(
            start_date=start_date,
            end_date=end_date,
            source=values_by_date,
            unit="usd_per_bbl",
        )
        if not points:
            raise RuntimeError(f"{normalized_code}: failed to parse live EIA rows")
        return points

    def fetch_manual_snapshot_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        points: list[ExternalIndicatorPoint] = []
        for offset, current_date in enumerate(
            _date_range(start_date=start_date, end_date=end_date)
        ):
            seasonal = 4.0 * math.sin((2 * math.pi * current_date.timetuple().tm_yday) / 365.0)
            trend = 0.01 * offset
            points.append(
                ExternalIndicatorPoint(
                    indicator_date=current_date,
                    value_numeric=82.0 + seasonal + trend,
                    unit="usd_per_bbl",
                    metadata={"source": "manual_snapshot"},
                )
            )
        return points


class UsdRubCbrAdapter(ExternalIndicatorsAdapter):
    provider_name = "cbr"
    indicator_codes = ("usd_rub",)

    def fetch_live_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        normalized_code = self.validate_indicator_code(indicator_code, self.indicator_codes)
        endpoint = (
            "https://www.cbr.ru/scripts/XML_dynamic.asp"
            f"?date_req1={start_date.strftime('%d/%m/%Y')}"
            f"&date_req2={end_date.strftime('%d/%m/%Y')}"
            "&VAL_NM_RQ=R01235"
        )
        xml_content = _read_text_from_url(endpoint)
        root = ElementTree.fromstring(xml_content)
        values_by_date: dict[date, float] = {}
        for record in root.findall(".//Record"):
            raw_date = record.attrib.get("Date")
            value_node = record.find("Value")
            if raw_date is None or value_node is None or value_node.text is None:
                continue
            try:
                point_date = datetime.strptime(raw_date, "%d.%m.%Y").date()
                point_value = float(value_node.text.replace(",", "."))
            except ValueError:
                continue
            values_by_date[point_date] = point_value

        points = _forward_fill_daily_points(
            start_date=start_date,
            end_date=end_date,
            source=values_by_date,
            unit="rub_per_usd",
        )
        if not points:
            raise RuntimeError(f"{normalized_code}: failed to parse live CBR rows")
        return points

    def fetch_manual_snapshot_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        points: list[ExternalIndicatorPoint] = []
        for offset, current_date in enumerate(
            _date_range(start_date=start_date, end_date=end_date)
        ):
            seasonal = 2.5 * math.sin((2 * math.pi * current_date.timetuple().tm_yday) / 365.0)
            drift = 0.004 * offset
            points.append(
                ExternalIndicatorPoint(
                    indicator_date=current_date,
                    value_numeric=88.0 + seasonal + drift,
                    unit="rub_per_usd",
                    metadata={"source": "manual_snapshot"},
                )
            )
        return points


class CuratedWholesaleAdapter(ExternalIndicatorsAdapter):
    provider_name = "curated_wholesale"
    indicator_codes = ("wholesale_gasoline_index", "wholesale_diesel_index")

    @property
    def supports_live(self) -> bool:
        return False

    def fetch_live_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        raise RuntimeError("live endpoint is not configured for wholesale indicators")

    def fetch_manual_snapshot_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        normalized_code = self.validate_indicator_code(indicator_code, self.indicator_codes)
        base_value = 102.0 if normalized_code == "wholesale_gasoline_index" else 108.0
        points: list[ExternalIndicatorPoint] = []
        for offset, current_date in enumerate(
            _date_range(start_date=start_date, end_date=end_date)
        ):
            doy = current_date.timetuple().tm_yday
            seasonal = math.sin((2 * math.pi * doy) / 365.0)
            long_trend = 0.02 * offset
            if normalized_code == "wholesale_gasoline_index":
                value = base_value + (2.4 * seasonal) + long_trend
            else:
                winter_boost = 2.0 if current_date.month in {11, 12, 1, 2} else -0.8
                value = base_value + (1.6 * seasonal) + winter_boost + long_trend
            points.append(
                ExternalIndicatorPoint(
                    indicator_date=current_date,
                    value_numeric=value,
                    unit="index_points",
                    metadata={"source": "curated_snapshot"},
                )
            )
        return points


class HolidayFlagAdapter(ExternalIndicatorsAdapter):
    provider_name = "ru_calendar"
    indicator_codes = ("holiday_flag",)

    @property
    def supports_live(self) -> bool:
        return False

    def fetch_live_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        raise RuntimeError("live endpoint is not configured for holiday flag")

    def fetch_manual_snapshot_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        points: list[ExternalIndicatorPoint] = []
        for current_date in _date_range(start_date=start_date, end_date=end_date):
            is_holiday = (current_date.month, current_date.day) in RU_HOLIDAYS
            points.append(
                ExternalIndicatorPoint(
                    indicator_date=current_date,
                    value_numeric=1.0 if is_holiday else 0.0,
                    unit="flag",
                    metadata={"source": "ru_calendar"},
                )
            )
        return points


class EventPressureAdapter(ExternalIndicatorsAdapter):
    provider_name = "curated_event_catalog"
    indicator_codes = ("event_pressure_score",)

    def __init__(
        self,
        *,
        event_pressure_provider: Callable[[date], float] | None = None,
    ) -> None:
        self._event_pressure_provider = event_pressure_provider or event_pressure_for_day

    @property
    def supports_live(self) -> bool:
        return False

    def fetch_live_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        raise RuntimeError("live endpoint is not configured for event pressure")

    def fetch_manual_snapshot_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        points: list[ExternalIndicatorPoint] = []
        for current_date in _date_range(start_date=start_date, end_date=end_date):
            points.append(
                ExternalIndicatorPoint(
                    indicator_date=current_date,
                    value_numeric=self._event_pressure_provider(current_date),
                    unit="score",
                    metadata={"source": "curated_event_catalog"},
                )
            )
        return points


def _read_text_from_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("https_url_required")
    request = Request(url, headers={"accept": "application/json, text/plain, */*"})
    try:
        with urlopen(request, timeout=20) as response:  # nosec B310
            raw = response.read()
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"HTTP request failed for url={url}") from exc
    for encoding in ("utf-8", "cp1251", "windows-1251"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _read_json_from_url(url: str) -> dict:
    payload = _read_text_from_url(url)
    try:
        result = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON payload from url={url}") from exc
    if not isinstance(result, dict):
        raise RuntimeError(f"Unexpected payload shape from url={url}")
    return result
