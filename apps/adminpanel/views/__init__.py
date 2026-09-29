"""Admin panel views package.

Re-exports the class-based views so `from apps.adminpanel.views import X`
and `urls.py` keep working unchanged.
"""

from apps.adminpanel.views.audit import AuditListView
from apps.adminpanel.views.banners import BannersAdminView
from apps.adminpanel.views.calendar import CalendarView
from apps.adminpanel.views.courts import CourtsAdminView
from apps.adminpanel.views.dashboard import AdminLoginView, AdminLogoutView, DashboardView
from apps.adminpanel.views.events import EventsAdminView
from apps.adminpanel.views.payments import PaymentsAdminView
from apps.adminpanel.views.reports import ReportsAdminView
from apps.adminpanel.views.settings import SettingsAdminView
from apps.adminpanel.views.users import UsersAdminView

__all__ = [
    "AdminLoginView",
    "AdminLogoutView",
    "AuditListView",
    "BannersAdminView",
    "CalendarView",
    "CourtsAdminView",
    "DashboardView",
    "EventsAdminView",
    "PaymentsAdminView",
    "ReportsAdminView",
    "SettingsAdminView",
    "UsersAdminView",
]
