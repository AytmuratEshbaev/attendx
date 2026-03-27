"""Hikvision ISAPI sync — push/remove students on terminals."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import structlog

from app.core.security import decrypt_device_password
from app.models.device import Device
from app.models.student import Student

logger = structlog.get_logger()


class HikvisionSyncError(Exception):
    pass


async def ensure_plan_template(timetable: object, device: Device) -> int:
    """Push plan template to Hikvision terminal for a given timetable.

    Returns the plan_template_id used (timetable.id + 10).
    Idempotent — safe to call multiple times.
    """
    template_id = timetable.id + 10  # type: ignore[attr-defined]
    # Hikvision devices typically support plan IDs 1-255; cap to avoid range errors
    template_id = min(template_id, 255)
    password = decrypt_device_password(device.password_enc)
    base_url = f"http://{device.ip_address}:{device.port}"
    auth = httpx.DigestAuth(device.username, password)

    async with httpx.AsyncClient(auth=auth, timeout=10.0) as client:
        if timetable.timetable_type == "recurring":  # type: ignore[attr-defined]
            # Step 1: push WeekPlan (schedule definition)
            week_xml = _build_week_plan_xml(timetable, template_id)
            resp = await client.put(
                f"{base_url}/ISAPI/AccessControl/WeekPlan/{template_id}",
                content=week_xml,
                headers={"Content-Type": "application/xml"},
            )
            if resp.status_code not in (200, 201):
                raise HikvisionSyncError(
                    f"WeekPlan push failed [{resp.status_code}]: {resp.text[:200]}"
                )

            # Step 2: push PlanTemplate referencing the WeekPlan
            plan_xml = _build_plan_template_ref_xml(timetable, template_id)
        else:
            plan_xml = _build_holiday_plan_template_xml(timetable, template_id)

        resp = await client.put(
            f"{base_url}/ISAPI/AccessControl/PlanTemplate/{template_id}",
            content=plan_xml,
            headers={"Content-Type": "application/xml"},
        )
        if resp.status_code not in (200, 201):
            raise HikvisionSyncError(
                f"PlanTemplate push failed [{resp.status_code}]: {resp.text[:200]}"
            )

    logger.info(
        "plan_template_pushed",
        timetable=timetable.name,  # type: ignore[attr-defined]
        device=device.name,
        template_id=template_id,
    )
    return template_id


async def sync_person(student: Student, device: Device, plan_template_no: int = 1) -> None:
    """Add or update person record on Hikvision terminal.

    Tries JSON format first (?format=json); falls back to XML if the device
    responds with methodNotAllowed or explicitly rejects JSON.
    """
    password = decrypt_device_password(device.password_enc)
    base_url = f"http://{device.ip_address}:{device.port}"
    auth = httpx.DigestAuth(device.username, password)

    employee_no = _safe_employee_no(student)
    logger.debug(
        "sync_person_request",
        employee_no=employee_no,
        plan_template_no=plan_template_no,
    )

    json_body = _build_user_json(student, plan_template_no)

    async with httpx.AsyncClient(auth=auth, timeout=10.0) as client:
        resp = await _post_user(client, base_url, json_body)

        if resp.status_code == 400 and "employeeNoAlreadyExist" in resp.text:
            # Delete existing user then re-create
            await _delete_user_on_device(client, base_url, employee_no)
            resp = await _post_user(client, base_url, json_body)

        if resp.status_code == 400 and "badJsonFormat" in resp.text:
            # Device doesn't support JSON → XML fallback
            xml_body = _build_user_xml(student, plan_template_no)
            resp = await client.post(
                f"{base_url}/ISAPI/AccessControl/UserInfo/Record",
                content=xml_body,
                headers={"Content-Type": "application/xml"},
            )
            if resp.status_code == 400 and "employeeNoAlreadyExist" in resp.text:
                await _delete_user_on_device(client, base_url, employee_no)
                resp = await client.post(
                    f"{base_url}/ISAPI/AccessControl/UserInfo/Record",
                    content=xml_body,
                    headers={"Content-Type": "application/xml"},
                )

        logger.debug("sync_person_response", status=resp.status_code, body=resp.text[:200])
        if resp.status_code not in (200, 201):
            raise HikvisionSyncError(
                f"Person sync failed [{resp.status_code}]: {resp.text}"
            )

    logger.info("person_synced", student=student.name, device=device.name)


async def sync_face(student: Student, device: Device) -> None:
    """Upload face photo to Hikvision terminal."""
    if not student.face_image_path:
        logger.debug("no_face_image_skip", student=student.name)
        return

    image_path = Path(student.face_image_path)
    if not image_path.exists():
        logger.warning("face_image_missing", path=str(image_path))
        return

    password = decrypt_device_password(device.password_enc)
    base_url = f"http://{device.ip_address}:{device.port}"
    auth = httpx.DigestAuth(device.username, password)

    image_bytes = image_path.read_bytes()
    fpid = _safe_employee_no(student)

    # Hikvision face enrollment: multipart with JSON metadata + JPEG image
    # faceLibType="normalFD" — regular face library (not blacklist)
    boundary = "----AttendXBoundary"
    json_meta = f'{{"faceLibType":"normalFD","FDID":"1","FPID":"{fpid}"}}'
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="FaceDataRecord"\r\n'
        f"Content-Type: application/json\r\n\r\n"
        f"{json_meta}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="img"; filename="face.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()

    ct = f"multipart/form-data; boundary={boundary}"
    async with httpx.AsyncClient(auth=auth, timeout=15.0) as client:
        # POST — add new face record
        resp = await client.post(
            f"{base_url}/ISAPI/Intelligent/FDLib/FaceDataRecord",
            content=body,
            headers={"Content-Type": ct},
        )
        # If record already exists, update it via PUT
        if resp.status_code in (400, 405) and (
            "methodNotAllowed" in resp.text or "recordExist" in resp.text
        ):
            resp = await client.put(
                f"{base_url}/ISAPI/Intelligent/FDLib/FaceDataRecord",
                content=body,
                headers={"Content-Type": ct},
            )
        if resp.status_code not in (200, 201):
            raise HikvisionSyncError(
                f"Face sync failed [{resp.status_code}]: {resp.text[:200]}"
            )

    logger.info("face_synced", student=student.name, device=device.name)


async def fetch_persons_from_device(device: Device) -> list[dict]:
    """Fetch all persons from Hikvision terminal via UserInfo/Search."""
    password = decrypt_device_password(device.password_enc)
    base_url = f"http://{device.ip_address}:{device.port}"
    auth = httpx.DigestAuth(device.username, password)

    persons: list[dict] = []
    search_position = 0
    page_size = 50

    async with httpx.AsyncClient(auth=auth, timeout=15.0) as client:
        while True:
            payload = {
                "UserInfoSearchCond": {
                    "searchID": "attendx_import",
                    "searchResultPosition": search_position,
                    "maxResults": page_size,
                }
            }
            resp = await client.post(
                f"{base_url}/ISAPI/AccessControl/UserInfo/Search?format=json",
                json=payload,
            )
            if resp.status_code not in (200, 201):
                raise HikvisionSyncError(
                    f"UserInfo/Search failed [{resp.status_code}]: {resp.text[:200]}"
                )
            data = resp.json()
            result = data.get("UserInfoSearch", {})
            records = result.get("UserInfo", [])
            for r in records:
                employee_no = str(r.get("employeeNo") or "").strip()
                name = str(r.get("name") or "").strip()
                if employee_no and name:
                    persons.append({"employee_no": employee_no, "name": name})

            total = result.get("totalMatches", 0)
            search_position += len(records)
            if search_position >= total or not records:
                break

    return persons


async def remove_person(student: Student, device: Device) -> None:
    """Remove person from Hikvision terminal."""
    password = decrypt_device_password(device.password_enc)
    base_url = f"http://{device.ip_address}:{device.port}"
    auth = httpx.DigestAuth(device.username, password)

    employee_no = _safe_employee_no(student)
    xml_body = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<UserInfoDelCond>\n"
        "  <EmployeeNoList>\n"
        f"    <employeeNo>{employee_no}</employeeNo>\n"
        "  </EmployeeNoList>\n"
        "</UserInfoDelCond>"
    ).encode("utf-8")

    async with httpx.AsyncClient(auth=auth, timeout=10.0) as client:
        resp = await client.put(
            f"{base_url}/ISAPI/AccessControl/UserInfo/Delete",
            content=xml_body,
            headers={"Content-Type": "application/xml"},
        )
        # 404 = already removed — acceptable
        if resp.status_code not in (200, 404):
            raise HikvisionSyncError(
                f"Person remove failed [{resp.status_code}]: {resp.text[:200]}"
            )

    logger.info("person_removed", student=student.name, device=device.name)


async def _post_user(client: httpx.AsyncClient, base_url: str, json_body: dict) -> httpx.Response:
    return await client.post(
        f"{base_url}/ISAPI/AccessControl/UserInfo/Record?format=json",
        json=json_body,
    )


async def _delete_user_on_device(client: httpx.AsyncClient, base_url: str, employee_no: str) -> None:
    del_xml = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<UserInfoDelCond>\n"
        "  <EmployeeNoList>\n"
        f"    <employeeNo>{employee_no}</employeeNo>\n"
        "  </EmployeeNoList>\n"
        "</UserInfoDelCond>"
    ).encode("utf-8")
    await client.put(
        f"{base_url}/ISAPI/AccessControl/UserInfo/Delete",
        content=del_xml,
        headers={"Content-Type": "application/xml"},
    )


def _safe_employee_no(student: Student) -> str:
    """Return a Hikvision-safe employee number: no hyphens, ≤ 32 chars."""
    if student.employee_no:
        return student.employee_no
    return str(student.id).replace("-", "")  # 32 hex chars


def _build_user_json(student: Student, plan_template_no: int = 1) -> dict:
    """Build Hikvision UserInfo payload as dict (for ?format=json requests).

    RightPlan is omitted — device assigns default access rights.
    Custom schedule (planTemplateNo) is pushed via a separate
    /ISAPI/AccessControl/UserRightPlan call after user creation.
    """
    employee_no = _safe_employee_no(student)
    return {
        "UserInfo": {
            "employeeNo": employee_no,
            "name": student.name,
            "userType": "normal",
            "Valid": {
                "enable": True,
                "beginTime": "2024-01-01T00:00:00",
                "endTime": "2030-12-31T23:59:59",
            },
        }
    }


def _build_user_xml(student: Student, plan_template_no: int = 1) -> bytes:
    employee_no = _safe_employee_no(student)
    xml = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<UserInfo>\n"
        f"  <employeeNo>{employee_no}</employeeNo>\n"
        f"  <name>{student.name}</name>\n"
        "  <userType>normal</userType>\n"
        "  <Valid>\n"
        "    <enable>true</enable>\n"
        "    <beginTime>2024-01-01T00:00:00</beginTime>\n"
        "    <endTime>2030-12-31T23:59:59</endTime>\n"
        "  </Valid>\n"
        "</UserInfo>"
    )
    return xml.encode("utf-8")


_WEEKDAY_MAP: dict[str, str] = {
    "monday": "Mon",
    "tuesday": "Tue",
    "wednesday": "Wed",
    "thursday": "Thu",
    "friday": "Fri",
    "saturday": "Sat",
    "sunday": "Sun",
}


def _build_week_plan_xml(timetable: object, plan_no: int) -> bytes:
    """Build Hikvision WeekPlan XML — pushed to /ISAPI/AccessControl/WeekPlan/{no}."""
    weekdays_raw = getattr(timetable, "weekdays", None) or "[]"
    try:
        weekdays: list[str] = json.loads(weekdays_raw)
    except (ValueError, TypeError):
        weekdays = []

    start_t = getattr(timetable, "start_time", None)
    end_t = getattr(timetable, "end_time", None)
    start_str = start_t.strftime("%H:%M:%S") if start_t else "00:00:00"
    end_str = end_t.strftime("%H:%M:%S") if end_t else "23:59:59"

    day_segments = ""
    for day in weekdays:
        hik_day = _WEEKDAY_MAP.get(day.lower(), day)
        day_segments += (
            f"  <{hik_day}>\n"
            "    <TimeSegment>\n"
            f"      <startTime>{start_str}</startTime>\n"
            f"      <endTime>{end_str}</endTime>\n"
            "    </TimeSegment>\n"
            f"  </{hik_day}>\n"
        )

    xml = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<WeekPlan>\n"
        f"  <weekPlanNo>{plan_no}</weekPlanNo>\n"
        "  <enable>true</enable>\n"
        f"{day_segments}"
        "</WeekPlan>"
    )
    return xml.encode("utf-8")


def _build_plan_template_ref_xml(timetable: object, template_id: int) -> bytes:
    """Build Hikvision PlanTemplate XML that references a WeekPlan by number."""
    name = getattr(timetable, "name", "Timetable")
    xml = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<PlanTemplate>\n"
        f"  <planTemplateNo>{template_id}</planTemplateNo>\n"
        f"  <planTemplateName>{name}</planTemplateName>\n"
        f"  <weekPlanNo>{template_id}</weekPlanNo>\n"
        "</PlanTemplate>"
    )
    return xml.encode("utf-8")


def _build_holiday_plan_template_xml(timetable: object, template_id: int) -> bytes:
    """Build Hikvision PlanTemplate XML with HolidayGroupCfg for a one-time timetable."""
    date_from = getattr(timetable, "date_from", None)
    date_to = getattr(timetable, "date_to", None)
    ot_start = getattr(timetable, "ot_start_time", None)
    ot_end = getattr(timetable, "ot_end_time", None)
    name = getattr(timetable, "name", "Timetable")

    start_date = date_from.isoformat() if date_from else "2024-01-01"
    end_date = date_to.isoformat() if date_to else "2030-12-31"
    start_str = ot_start.strftime("%H:%M:%S") if ot_start else "00:00:00"
    end_str = ot_end.strftime("%H:%M:%S") if ot_end else "23:59:59"

    xml = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<PlanTemplate>\n"
        f"  <planTemplateNo>{template_id}</planTemplateNo>\n"
        f"  <planTemplateName>{name}</planTemplateName>\n"
        "  <HolidayGroupCfg>\n"
        "    <HolidayList>\n"
        "      <Holiday>\n"
        "        <enable>true</enable>\n"
        f"        <startDate>{start_date}</startDate>\n"
        f"        <endDate>{end_date}</endDate>\n"
        "        <TimeSegment>\n"
        f"          <startTime>{start_str}</startTime>\n"
        f"          <endTime>{end_str}</endTime>\n"
        "        </TimeSegment>\n"
        "      </Holiday>\n"
        "    </HolidayList>\n"
        "  </HolidayGroupCfg>\n"
        "</PlanTemplate>"
    )
    return xml.encode("utf-8")
