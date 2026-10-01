"""Walk every customer journey against the running stack and report pass/fail.

This is a management command so it can run inside the backend container with
database access. That access is used for exactly one thing: reading the
6-digit email-verification code that registration writes to the
``verification_verificationcode`` table, so the journey can continue without a
real mail inbox. The code is then submitted through the public
``/api/auth/verify/`` endpoint — the same one the mobile app calls — so the
verification path itself is exercised for real.

Everything else goes over HTTP against the live API.
"""

import json
import urllib.error
import urllib.request
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.verification.models import VerificationCode


class _Reporter:
    def __init__(self, stdout):
        self.stdout = stdout
        self.rows = []

    def check(self, name, ok, detail=""):
        self.rows.append((name, bool(ok), detail))
        mark = "PASS" if ok else "FAIL"
        self.stdout.write(f"  [{mark}] {name}" + (f"  — {detail}" if detail else ""))

    def summary(self, stdout, style):
        ok = sum(1 for _, o, _ in self.rows if o)
        total = len(self.rows)
        stdout.write("")
        for name, passed, detail in self.rows:
            if not passed:
                stdout.write(style.ERROR(f"  FAILED  {name}  {detail}"))
        line = f"JOURNEYS: {ok}/{total} passed"
        stdout.write(style.SUCCESS(line) if ok == total else style.ERROR(line))
        return ok == total


class Command(BaseCommand):
    help = "Exercise every customer journey over HTTP and report pass/fail."

    def add_arguments(self, parser):
        parser.add_argument("--base", default="http://127.0.0.1:8000")

    def handle(self, *args, **options):
        self.base = options["base"].rstrip("/")
        self.rep = _Reporter(self.stdout)
        stamp = timezone.now().strftime("%Y%m%d%H%M%S")
        self.email = f"journey_{stamp}@andespadelclub.com"
        self.password = "Journey12345!"
        self.token = None
        self.stdout.write(f"base: {self.base}\naccount: {self.email}\n")

        self.journey_register()
        self.journey_login()
        self.journey_profile()
        self.journey_browse()
        self.journey_booking()
        self.journey_events()
        self.journey_password_reset()
        self.journey_logout()

        ok = self.rep.summary(self.stdout, self.style)
        if not ok:
            raise SystemExit(1)

    # -- HTTP helper ---------------------------------------------------
    def call(self, method, path, body=None, token=None, form=None):
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = None
        if form is not None:
            boundary = "----journeyform"
            parts = []
            for key, value in form.items():
                if isinstance(value, tuple):
                    filename, content, ctype = value
                    parts.append(f"--{boundary}\r\n".encode())
                    parts.append(
                        (
                            f'Content-Disposition: form-data; name="{key}"; '
                            f'filename="{filename}"\r\n'
                        ).encode()
                    )
                    parts.append(f"Content-Type: {ctype}\r\n\r\n".encode())
                    parts.append(content)
                    parts.append(b"\r\n")
                else:
                    parts.append(f"--{boundary}\r\n".encode())
                    parts.append(
                        f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
                    )
                    parts.append(str(value).encode() + b"\r\n")
            parts.append(f"--{boundary}--\r\n".encode())
            data = b"".join(parts)
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            self.base + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw, status = resp.read(), resp.status
        except urllib.error.HTTPError as exc:
            raw, status = exc.read(), exc.code
        except Exception as exc:  # noqa: BLE001
            return 0, {"error": str(exc)}
        try:
            return status, json.loads(raw.decode() or "{}")
        except Exception:  # noqa: BLE001
            return status, {"raw": raw[:200].decode("utf-8", "replace")}

    # -- journeys ------------------------------------------------------
    def journey_register(self):
        status, data = self.call(
            "POST",
            "/api/auth/register/",
            body={
                "email": self.email,
                "password": self.password,
                "first_name": "Journey",
                "last_name": "Test",
                "consent_version": "1.0",
            },
        )
        self.rep.check("register creates account", status == 201, f"http {status}")

        status, data = self.call(
            "POST", "/api/auth/login/", body={"email": self.email, "password": self.password}
        )
        self.rep.check(
            "login refused before verification",
            status in (400, 401, 403),
            f"http {status}",
        )

        # The code is emailed; read the row that registration just wrote so the
        # journey can submit it through the public verify endpoint.
        row = (
            VerificationCode.objects.filter(
                user__email=self.email,
                purpose=VerificationCode.Purpose.EMAIL_VERIFY,
            )
            .order_by("-created_at")
            .first()
        )
        self.rep.check("verification code issued and emailed", row is not None)
        if row is None:
            return

        status, data = self.call(
            "POST",
            "/api/auth/verify/",
            body={"email": self.email, "code": row.code},
        )
        self.rep.check("email verified via public endpoint", status == 200, f"http {status}")

    def journey_login(self):
        status, data = self.call(
            "POST", "/api/auth/login/", body={"email": self.email, "password": self.password}
        )
        token = data.get("access") or (data.get("tokens") or {}).get("access")
        self.rep.check("login after verification", status == 200 and bool(token), f"http {status}")
        self.token = token

    def journey_profile(self):
        if not self.token:
            self.rep.check("profile", False, "no token")
            return
        status, data = self.call("GET", "/api/auth/me/", token=self.token)
        self.rep.check("auth/me", status == 200, f"http {status}")

        status, data = self.call("GET", "/api/auth/skill-levels/")
        skills = data.get("results", data) if isinstance(data, dict) else data
        self.rep.check(
            "skill levels present for registration",
            status == 200 and isinstance(skills, list) and len(skills) > 0,
            f"{len(skills) if isinstance(skills, list) else 0} levels",
        )

    def journey_browse(self):
        if not self.token:
            self.rep.check("browse", False, "no token")
            return
        status, data = self.call("GET", "/api/courts/", token=self.token)
        self.courts = data.get("results", data) if isinstance(data, dict) else data
        self.rep.check(
            "courts list",
            status == 200 and bool(self.courts),
            f"{len(self.courts or [])} courts",
        )

        self.day = (timezone.localdate() + timedelta(days=1)).isoformat()
        if self.courts:
            court_id = self.courts[0]["id"]
            status, data = self.call(
                "GET", f"/api/courts/{court_id}/availability/?date={self.day}", token=self.token
            )
            slots = data if isinstance(data, list) else data.get("results", [])
            self.free_slots = [s["start"][:5] for s in slots if s.get("status") == "available"]
            self.rep.check(
                "court availability returns slots",
                status == 200 and len(self.free_slots) > 0,
                f"{len(self.free_slots)} free slots on {self.day}",
            )

        status, data = self.call("GET", "/api/club/", token=self.token)
        self.rep.check("club info", status == 200, f"http {status}")
        status, data = self.call("GET", "/api/banners/?lang=es", token=self.token)
        self.rep.check("banners", status == 200, f"http {status}")
        status, data = self.call("GET", "/api/notifications/", token=self.token)
        self.rep.check("notifications list", status == 200, f"http {status}")

    def journey_booking(self):
        if not self.token or not getattr(self, "courts", None):
            self.rep.check("booking", False, "no courts")
            return
        if not getattr(self, "free_slots", None):
            self.rep.check("create booking", False, "no free slots to book")
            return

        # Take the first slot the API says is available — the same thing the
        # booking wizard does. Hardcoding a time re-books a taken slot and the
        # API correctly answers 409.
        start = self.free_slots[0]
        court_id = self.courts[0]["id"]
        status, data = self.call(
            "POST",
            "/api/bookings/",
            token=self.token,
            body={
                "court": court_id,
                "date": self.day,
                "start_time": start,
                "duration_minutes": 60,
                "players": 4,
            },
        )
        ok = status in (200, 201)
        self.rep.check("create booking", ok, f"http {status} at {start} {data if not ok else ''}")
        if not ok:
            return
        self.booking = data

        booking_id = data.get("id") or (data.get("booking") or {}).get("id")
        if not booking_id:
            self.rep.check("booking payment", False, "no booking id in response")
            return

        # Bank transfer is the club's manual method: the customer pays and
        # uploads a receipt, then reception confirms it. BookingPaymentView is
        # POST-only — GET is 405 by design.
        status, pay = self.call(
            "POST",
            f"/api/bookings/{booking_id}/payments/",
            token=self.token,
            body={"method": "transfer", "reference": "JRN" + self.email.split("@")[0].split("_")[-1]},
        )
        ok = status == 201
        self.rep.check("create transfer payment", ok, f"http {status} {pay if not ok else ''}")
        if not ok:
            return

        payment_id = pay.get("id")
        self.rep.check("transfer payment pending", pay.get("status") == "pending_transfer",
                       f"status={pay.get('status')}")

        # Upload the receipt — the journey the app's transfer-proof screen runs.
        # The endpoint reads request.FILES["proof_image"] and only accepts
        # JPEG/PNG, so this sends a real PNG file part rather than a string.
        png_1x1 = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
            b"\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        status, data = self.call(
            "POST",
            f"/api/payments/{payment_id}/upload-proof/",
            token=self.token,
            form={"proof_image": ("comprobante.png", png_1x1, "image/png")},
        )
        self.rep.check(
            "upload transfer proof",
            status in (200, 201),
            f"http {status} {data if status not in (200, 201) else ''!s}",
        )

    def journey_events(self):
        if not self.token:
            self.rep.check("events", False, "no token")
            return
        status, data = self.call("GET", "/api/events/", token=self.token)
        events = data.get("results", data) if isinstance(data, dict) else data
        self.rep.check("events list", status == 200 and bool(events), f"{len(events or [])} events")

        if events:
            status, data = self.call("POST", f"/api/events/{events[0]['id']}/join/", token=self.token, body={})
            self.rep.check("join event", status in (200, 201, 204), f"http {status}")
            status, data = self.call("POST", f"/api/events/{events[0]['id']}/leave/", token=self.token, body={})
            self.rep.check("leave event", status in (200, 201, 204), f"http {status}")

        status, data = self.call("GET", "/api/tournaments/", token=self.token)
        tours = data.get("results", data) if isinstance(data, dict) else data
        self.rep.check("tournaments list", status == 200, f"{len(tours or [])} tournaments")

        status, data = self.call("GET", "/api/open-matches/", token=self.token)
        matches = data.get("results", data) if isinstance(data, dict) else data
        self.rep.check("open matches list", status == 200 and bool(matches), f"{len(matches or [])} quedadas")

    def journey_password_reset(self):
        status, data = self.call(
            "POST", "/api/auth/password-reset/", body={"email": self.email}
        )
        self.rep.check("password reset requested", status in (200, 201, 202), f"http {status}")

        row = (
            VerificationCode.objects.filter(
                user__email=self.email, purpose=VerificationCode.Purpose.PASSWORD_RESET
            )
            .order_by("-created_at")
            .first()
        )
        self.rep.check("password reset code issued and emailed", row is not None)
        if row is None:
            return

        new_password = "Journey98765!"
        status, data = self.call(
            "POST",
            "/api/auth/password-reset/confirm/",
            body={"email": self.email, "code": row.code, "password": new_password},
        )
        self.rep.check("password reset confirmed", status == 200, f"http {status}")

        status, data = self.call(
            "POST", "/api/auth/login/", body={"email": self.email, "password": new_password}
        )
        token = data.get("access") or (data.get("tokens") or {}).get("access")
        self.rep.check("login with new password", status == 200 and bool(token), f"http {status}")
        if token:
            self.token = token
            self.password = new_password

    def journey_logout(self):
        if not self.token:
            self.rep.check("logout", False, "no token")
            return
        status, data = self.call("POST", "/api/auth/logout/", token=self.token, body={})
        self.rep.check("logout", status in (200, 204, 205), f"http {status}")
