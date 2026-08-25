from django.db.models import Count, Sum

from apps.bookings.models import Booking
from apps.payments.models import Payment

CAPTURED = ("captured", "confirmed")


class ReportService:
    @staticmethod
    def _paid_filter(start, end):
        return Payment.objects.filter(
            status__in=CAPTURED, created_at__date__gte=start, created_at__date__lte=end
        )

    @staticmethod
    def revenue_by_period(start, end, period="day"):
        query = ReportService._paid_filter(start, end)
        key = {
            "day": "created_at__date",
            "week": "created_at__week",
            "month": "created_at__month",
            "year": "created_at__year",
        }.get(period, "created_at__date")
        rows = query.values(key).annotate(total=Sum("amount")).order_by(key)
        return [{"period": r[key], "total": float(r["total"])} for r in rows]

    @staticmethod
    def revenue_by_court(start, end):
        rows = (
            ReportService._paid_filter(start, end)
            .values("booking__court__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        return [{"court": r["booking__court__name"], "total": float(r["total"])} for r in rows]

    @staticmethod
    def revenue_by_method(start, end):
        rows = (
            ReportService._paid_filter(start, end)
            .values("method")
            .annotate(total=Sum("amount"))
            .order_by("method")
        )
        return [{"method": r["method"], "total": float(r["total"])} for r in rows]

    @staticmethod
    def occupancy_percentage(start, end):
        from apps.scheduling.models import TimeSlot

        slots = TimeSlot.objects.filter(date__gte=start, date__lte=end)
        total = slots.count()
        booked = slots.filter(status__in=("booked", "held", "blocked")).count()
        return {
            "booked": booked,
            "total": total,
            "pct": round(booked * 100 / total, 1) if total else 0.0,
        }

    @staticmethod
    def top_customers(start, end, limit=10):
        rows = (
            ReportService._paid_filter(start, end)
            .values("user__email")
            .annotate(revenue=Sum("amount"), bookings=Count("booking", distinct=True))
            .order_by("-revenue")[:limit]
        )
        return [
            {"email": r["user__email"], "revenue": float(r["revenue"]), "bookings": r["bookings"]}
            for r in rows
        ]

    @staticmethod
    def cancellation_rate(start, end):
        bookings = Booking.objects.filter(date__gte=start, date__lte=end)
        total = bookings.count()
        cancelled = bookings.filter(status=Booking.Status.CANCELLED).count()
        pct = round(cancelled * 100 / total, 1) if total else 0.0
        return {"cancelled": cancelled, "total": total, "pct": pct}

    @staticmethod
    def no_show_rate(start, end):
        bookings = Booking.objects.filter(date__gte=start, date__lte=end)
        total = bookings.count()
        no_show = bookings.filter(status=Booking.Status.NO_SHOW).count()
        pct = round(no_show * 100 / total, 1) if total else 0.0
        return {"no_show": no_show, "total": total, "pct": pct}

    @staticmethod
    def revenue_csv(rows, headers):
        import csv
        from io import StringIO

        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        return buf.getvalue()

    @staticmethod
    def revenue_pdf(title, rows, headers):
        from io import BytesIO

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
        table = Table([headers] + [list(r) for r in rows])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#002F48")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        elements.append(table)
        doc.build(elements)
        return buf.getvalue()
