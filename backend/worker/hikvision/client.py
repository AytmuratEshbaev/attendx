"""Hikvision ISAPI HTTP client for terminal communication."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger()

_VERIFY_MODE_MAP: dict[int, str] = {
    0: "face",
    1: "fingerprint",
    2: "card",
    200: "card",
    201: "card",
}

_IN_OUT_MAP: dict[str, str] = {
    "entry": "entry",
    "exit": "exit",
    "0": "entry",
    "1": "exit",
}


@dataclass
class DeviceInfo:
    model: str
    serial_number: str
    firmware_version: str


@dataclass
class AttendanceEvent:
    employee_no: str
    name: str
    event_time: datetime
    event_type: str   # "entry" | "exit"
    verify_mode: str  # "face" | "fingerprint" | "card"
    serial_no: int    # unique event serial on device
    picture_url: str | None = None  # capture photo URL from device


class HikvisionClient:
    """Async Hikvision ISAPI HTTP client with Digest authentication."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = f"http://{host}:{port}"
        self._auth = httpx.DigestAuth(username, password)
        self._timeout = timeout

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_device_info(self) -> DeviceInfo:
        """Fetch device info from GET /ISAPI/System/deviceInfo."""
        async with httpx.AsyncClient(auth=self._auth, timeout=self._timeout) as client:
            resp = await client.get(f"{self.base_url}/ISAPI/System/deviceInfo")
            resp.raise_for_status()

        root = ET.fromstring(resp.text)
        ns = {"h": "http://www.hikvision.com/ver20/XMLSchema"}

        def _find(tag: str) -> str:
            el = root.find(f"h:{tag}", ns)
            if el is None:
                el = root.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        return DeviceInfo(
            model=_find("model"),
            serial_number=_find("serialNumber"),
            firmware_version=_find("firmwareVersion"),
        )

    async def get_device_time(self) -> str:
        """Fetch the device's current local time string via GET /ISAPI/System/time."""
        try:
            async with httpx.AsyncClient(auth=self._auth, timeout=self._timeout) as client:
                resp = await client.get(f"{self.base_url}/ISAPI/System/time")
            return resp.text[:400]
        except Exception as exc:
            return f"ERROR: {exc}"

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_attendance_logs(
        self,
        start_time: datetime,
        end_time: datetime,
        page_size: int = 100,
    ) -> list[AttendanceEvent]:
        """
        Fetch attendance events via POST /ISAPI/AccessControl/AcsEvent?format=json.
        Falls back to XML format if JSON returns empty results.
        Paginates automatically until all events are retrieved.
        """
        events: list[AttendanceEvent] = []
        position = 0
        json_endpoint_ok = False  # True if JSON endpoint responded with HTTP 200
        # Hikvision devices typically expect LOCAL device time (no timezone suffix)
        fmt = "%Y-%m-%dT%H:%M:%S"
        search_id = str(uuid.uuid4())

        async with httpx.AsyncClient(auth=self._auth, timeout=self._timeout) as client:
            while True:
                payload = {
                    "AcsEventCond": {
                        "searchID": search_id,
                        "searchResultPosition": position,
                        "maxResults": page_size,
                        "major": 5,
                        "minor": 0,
                        "startTime": start_time.strftime(fmt),
                        "endTime": end_time.strftime(fmt),
                    }
                }
                resp = await client.post(
                    f"{self.base_url}/ISAPI/AccessControl/AcsEvent?format=json",
                    json=payload,
                )
                logger.info("hikvision_acs_raw", status=resp.status_code, body=resp.text[:600])
                resp.raise_for_status()
                json_endpoint_ok = True  # JSON endpoint is reachable and returned HTTP 200
                data = resp.json()

                acs = data.get("AcsEvent", {})
                # Some Hikvision models return "AcsEventInfo", others "InfoList"
                records = acs.get("InfoList") or acs.get("AcsEventInfo") or []

                for rec in records:
                    event = _parse_event(rec)
                    if event:
                        events.append(event)

                total = acs.get("totalMatches", 0)
                position += len(records)
                if position >= total or not records:
                    break

        # Only try XML fallback if the JSON endpoint failed (non-200) or is unavailable.
        # If JSON returned HTTP 200 (even with 0 results), the device supports JSON — no XML needed.
        if not json_endpoint_ok:
            events = await self._get_attendance_logs_xml(start_time, end_time, page_size)

        return events

    async def _get_attendance_logs_xml(
        self,
        start_time: datetime,
        end_time: datetime,
        page_size: int = 100,
    ) -> list[AttendanceEvent]:
        """XML fallback for AcsEvent — used by older/some DS-K1T models."""
        events: list[AttendanceEvent] = []
        position = 0
        fmt = "%Y-%m-%dT%H:%M:%S"  # No tz suffix — device interprets as local time

        async with httpx.AsyncClient(auth=self._auth, timeout=self._timeout) as client:
            while True:
                xml_body = (
                    f"<?xml version='1.0' encoding='UTF-8'?>"
                    f"<AcsEventCond version='2.0' xmlns='http://www.hikvision.com/ver20/XMLSchema'>"
                    f"<searchID>{uuid.uuid4()}</searchID>"
                    f"<searchResultPosition>{position}</searchResultPosition>"
                    f"<maxResults>{page_size}</maxResults>"
                    f"<major>5</major>"
                    f"<startTime>{start_time.strftime(fmt)}</startTime>"
                    f"<endTime>{end_time.strftime(fmt)}</endTime>"
                    f"</AcsEventCond>"
                )
                resp = await client.post(
                    f"{self.base_url}/ISAPI/AccessControl/AcsEvent",
                    content=xml_body,
                    headers={"Content-Type": "application/xml"},
                )
                logger.info("hikvision_acs_xml_raw", status=resp.status_code, body=resp.text[:600])
                if resp.status_code != 200:
                    break

                root = ET.fromstring(resp.text)
                ns = {"h": "http://www.hikvision.com/ver20/XMLSchema"}

                def _findall(tag: str):
                    els = root.findall(f"h:{tag}", ns)
                    if not els:
                        els = root.findall(tag)
                    return els

                def _findtext(el, tag: str) -> str:
                    child = el.find(f"h:{tag}", ns) or el.find(tag)
                    return child.text.strip() if child is not None and child.text else ""

                total_el = root.find("h:totalMatches", ns) or root.find("totalMatches")
                total = int(total_el.text) if total_el is not None and total_el.text else 0

                records = _findall("AcsEventInfo")
                for rec in records:
                    try:
                        employee_no = (_findtext(rec, "employeeNoString") or _findtext(rec, "cardNo")).strip()
                        if not employee_no:
                            continue
                        serial_no = int(_findtext(rec, "serialNo") or "0")
                        name = _findtext(rec, "name")
                        time_str = _findtext(rec, "time")
                        event_time = _parse_time(time_str)
                        if event_time is None:
                            continue
                        in_out = _findtext(rec, "inOutStatus").lower() or "entry"
                        event_type = _IN_OUT_MAP.get(in_out, "entry")
                        verify_raw = _findtext(rec, "type") or "0"
                        verify_mode = _VERIFY_MODE_MAP.get(int(verify_raw), "face")
                        events.append(AttendanceEvent(
                            employee_no=employee_no,
                            name=name,
                            event_time=event_time,
                            event_type=event_type,
                            verify_mode=verify_mode,
                            serial_no=serial_no,
                        ))
                    except Exception:
                        logger.warning("hikvision_xml_parse_error", rec=ET.tostring(rec, encoding="unicode")[:200])

                position += len(records)
                if position >= total or not records:
                    break

        return events


def _parse_event(rec: dict) -> AttendanceEvent | None:
    """Parse a single AcsEventInfo record into AttendanceEvent."""
    try:
        employee_no = str(
            rec.get("employeeNoString") or rec.get("cardNo") or ""
        ).strip()
        if not employee_no:
            return None

        serial_no = int(rec.get("serialNo", 0))
        name = str(rec.get("name") or "").strip()

        time_str = str(rec.get("time") or "")
        event_time = _parse_time(time_str)
        if event_time is None:
            return None

        in_out = str(rec.get("inOutStatus", "entry")).lower()
        event_type = _IN_OUT_MAP.get(in_out, "entry")

        verify_raw = rec.get("type", 0)
        verify_mode = _VERIFY_MODE_MAP.get(int(verify_raw), "face")

        picture_url = str(rec.get("pictureURL") or "").strip() or None

        # Log the actual minor code so we can diagnose filter issues
        minor_code = rec.get("minor", "?")
        logger.debug("hikvision_event_minor", minor=minor_code, employee_no=employee_no, event_type=event_type)

        return AttendanceEvent(
            employee_no=employee_no,
            name=name,
            event_time=event_time,
            event_type=event_type,
            verify_mode=verify_mode,
            serial_no=serial_no,
            picture_url=picture_url,
        )
    except Exception:
        logger.warning("hikvision_parse_error", record=rec)
        return None


def _parse_time(time_str: str) -> datetime | None:
    """Parse Hikvision time string (ISO 8601) to UTC datetime."""
    if not time_str:
        return None
    try:
        dt = datetime.fromisoformat(time_str)
        return dt.astimezone(timezone.utc)
    except ValueError:
        logger.warning("hikvision_time_parse_failed", raw=time_str)
        return None
