from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.services import ReportService
from apps.users.permissions import IsManagerRole


def _parse_range(request):
    today = timezone.localdate()
    start = request.GET.get("start", "")
    end = request.GET.get("end", "")
    try:
        start = timezone.datetime.strptime(start, "%Y-%m-%d").date() if start else today
        end = timezone.datetime.strptime(end, "%Y-%m-%d").date() if end else today
    except ValueError:
        start, end = today, today
    if end < start:
        start, end = end, start
    return start, end


class RevenueReportView(APIView):
    permission_classes = (IsAuthenticated, IsManagerRole)

    def get(self, request):
        start, end = _parse_range(request)
        group = request.GET.get("group", "day")
        if group == "court":
            rows = ReportService.revenue_by_court(start, end)
            headers = ("Cancha", "Ingresos")
            data = [(r["court"], f"{r['total']:.2f}") for r in rows]
            title = f"Ingresos por cancha {start} a {end}"
        elif group == "method":
            rows = ReportService.revenue_by_method(start, end)
            headers = ("Metodo", "Ingresos")
            data = [(r["method"], f"{r['total']:.2f}") for r in rows]
            title = f"Ingresos por metodo {start} a {end}"
        else:
            rows = ReportService.revenue_by_period(start, end, period=group)
            headers = ("Periodo", "Ingresos")
            data = [(r["period"], f"{r['total']:.2f}") for r in rows]
            title = f"Ingresos por {group} {start} a {end}"

        fmt = request.GET.get("output", "json")
        if fmt == "csv":
            content = ReportService.revenue_csv(data, headers)
            return Response(
                content,
                headers={"Content-Disposition": 'attachment; filename="revenue.csv"'},
                content_type="text/csv",
            )
        if fmt == "pdf":
            content = ReportService.revenue_pdf(title, data, headers)
            from django.http import HttpResponse

            resp = HttpResponse(content, content_type="application/pdf")
            resp["Content-Disposition"] = 'attachment; filename="revenue.pdf"'
            return resp
        return Response(rows)


class OccupancyReportView(APIView):
    permission_classes = (IsAuthenticated, IsManagerRole)

    def get(self, request):
        start, end = _parse_range(request)
        return Response(ReportService.occupancy_percentage(start, end))


class CustomersReportView(APIView):
    permission_classes = (IsAuthenticated, IsManagerRole)

    def get(self, request):
        start, end = _parse_range(request)
        try:
            limit = max(1, min(int(request.GET.get("limit", 10)), 100))
        except (ValueError, TypeError):
            limit = 10
        return Response(ReportService.top_customers(start, end, limit=limit))


class CancellationReportView(APIView):
    permission_classes = (IsAuthenticated, IsManagerRole)

    def get(self, request):
        start, end = _parse_range(request)
        result = ReportService.cancellation_rate(start, end)
        result["no_show"] = ReportService.no_show_rate(start, end)
        return Response(result)
