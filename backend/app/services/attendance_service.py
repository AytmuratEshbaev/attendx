"""Attendance business logic service."""

import io
import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceLog
from app.repositories.attendance_repo import AttendanceRepository
from app.repositories.student_repo import StudentRepository
from app.schemas.attendance import (
    AttendanceFilter,
    AttendanceStats,
    DailyAttendance,
)


class AttendanceService:
    def __init__(self, session: AsyncSession):
        self.repo = AttendanceRepository(session)
        self.student_repo = StudentRepository(session)
        self.session = session

    async def get_attendance(
        self,
        filters: AttendanceFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[AttendanceLog], int]:
        date_from = filters.date_from or date.today()
        date_to = filters.date_to or date.today()
        filter_dict = {}
        if filters.student_id:
            filter_dict["student_id"] = filters.student_id
        if filters.event_type:
            filter_dict["event_type"] = filters.event_type
        return await self.repo.get_by_date_range(
            date_from, date_to, filter_dict, skip, limit
        )

    async def get_today(
        self, class_name: str | None = None
    ) -> list[AttendanceLog]:
        return await self.repo.get_today(class_name)

    async def get_recent(self, limit: int = 100) -> list[AttendanceLog]:
        return await self.repo.get_recent(limit)

    async def get_stats(
        self, target_date: date | None = None, class_name: str | None = None
    ) -> AttendanceStats:
        target = target_date or date.today()

        if class_name:
            total_students = await self.student_repo.count_by_class(class_name)
        else:
            total_students = await self.student_repo.count_active()

        day_stats = await self.repo.get_daily_stats(target)
        present = day_stats["present"]

        # Stats by class
        by_class: dict[str, dict] = {}
        class_names = await self.student_repo.get_class_names()
        for cn in class_names:
            if class_name and cn != class_name:
                continue
            class_total = await self.student_repo.count_by_class(cn)
            class_logs = await self.repo.get_today(cn)
            class_present = len({log.student_id for log in class_logs})
            by_class[cn] = {
                "total": class_total,
                "present": class_present,
                "absent": max(0, class_total - class_present),
                "percentage": round(
                    (class_present / class_total * 100), 1
                )
                if class_total
                else 0.0,
            }

        if class_name:
            present = sum(c["present"] for c in by_class.values())

        absent = max(0, total_students - present)
        pct = round((present / total_students * 100), 1) if total_students else 0.0

        return AttendanceStats(
            total_students=total_students,
            present_today=present,
            absent_today=absent,
            attendance_percentage=pct,
            by_class=by_class,
        )

    async def get_weekly_stats(
        self,
        start_date: date | None = None,
        class_name: str | None = None,
    ) -> list[DailyAttendance]:
        start = start_date or (date.today() - timedelta(days=6))
        if class_name:
            total = await self.student_repo.count_by_class(class_name)
        else:
            total = await self.student_repo.count_active()
        stats = await self.repo.get_weekly_stats(start)
        result = []
        for day in stats:
            present = day["present"]
            absent = max(0, total - present)
            pct = round((present / total * 100), 1) if total else 0.0
            result.append(
                DailyAttendance(
                    date=date.fromisoformat(day["date"]),
                    present=present,
                    absent=absent,
                    percentage=pct,
                )
            )
        return result

    async def get_student_attendance(
        self,
        student_id: uuid.UUID,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[AttendanceLog]:
        start = date_from or (date.today() - timedelta(days=30))
        end = date_to or date.today()
        return await self.repo.get_student_attendance(student_id, start, end)

    async def record_event(
        self,
        student_id: uuid.UUID,
        device_id: int | None,
        event_time: str,
        event_type: str,
        raw_event_id: str | None,
        verify_mode: str = "face",
    ) -> AttendanceLog | None:
        """Record an attendance event with deduplication."""
        if raw_event_id:
            is_dup = await self.repo.check_duplicate(raw_event_id)
            if is_dup:
                return None

        return await self.repo.create(
            {
                "student_id": student_id,
                "device_id": device_id,
                "event_time": event_time,
                "event_type": event_type,
                "raw_event_id": raw_event_id,
                "verify_mode": verify_mode,
            }
        )

    async def generate_report(
        self,
        date_from: date,
        date_to: date,
        class_name: str | None = None,
        fmt: str = "xlsx",
    ) -> bytes:
        """Generate attendance report as XLSX or PDF."""
        if fmt == "pdf":
            return await self._generate_pdf_report(date_from, date_to, class_name)
        return await self._generate_xlsx_report(date_from, date_to, class_name)

    async def _generate_xlsx_report(
        self, date_from: date, date_to: date, class_name: str | None = None
    ) -> bytes:
        import openpyxl

        wb = openpyxl.Workbook()

        # Sheet 1: Summary
        ws_summary = wb.active
        ws_summary.title = "Summary"
        ws_summary.append(["Date", "Total Students", "Present", "Absent", "Percentage"])

        current = date_from
        while current <= date_to:
            day_stats = await self.repo.get_daily_stats(current)
            if class_name:
                total = await self.student_repo.count_by_class(class_name)
            else:
                total = await self.student_repo.count_active()
            present = day_stats["present"]
            absent = max(0, total - present)
            pct = round((present / total * 100), 1) if total else 0.0
            ws_summary.append([
                current.isoformat(), total, present, absent, pct
            ])
            current += timedelta(days=1)

        # Sheet 2: Details
        ws_detail = wb.create_sheet("Details")
        students, _ = await self.student_repo.get_all_students(
            skip=0, limit=10000, class_name=class_name
        )

        # Header
        dates = []
        current = date_from
        while current <= date_to:
            dates.append(current)
            current += timedelta(days=1)

        header = ["Student", "Class"] + [d.isoformat() for d in dates]
        ws_detail.append(header)

        for student in students:
            row = [student.name, student.class_name or ""]
            for d in dates:
                logs = await self.repo.get_student_attendance(student.id, d, d)
                row.append("P" if logs else "A")
            ws_detail.append(row)

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    async def _generate_pdf_report(
        self, date_from: date, date_to: date, class_name: str | None = None
    ) -> bytes:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        elements = []

        # Title
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import getSampleStyleSheet

        styles = getSampleStyleSheet()
        elements.append(
            Paragraph(
                f"AttendX Attendance Report: {date_from} to {date_to}",
                styles["Title"],
            )
        )
        elements.append(Spacer(1, 0.25 * inch))

        # Summary table
        summary_data = [["Date", "Total", "Present", "Absent", "%"]]
        current = date_from
        while current <= date_to:
            day_stats = await self.repo.get_daily_stats(current)
            if class_name:
                total = await self.student_repo.count_by_class(class_name)
            else:
                total = await self.student_repo.count_active()
            present = day_stats["present"]
            absent = max(0, total - present)
            pct = round((present / total * 100), 1) if total else 0.0
            summary_data.append([
                current.isoformat(), str(total), str(present),
                str(absent), f"{pct}%",
            ])
            current += timedelta(days=1)

        table = Table(summary_data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)

        doc.build(elements)
        return buf.getvalue()
