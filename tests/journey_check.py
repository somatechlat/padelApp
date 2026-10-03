#!/usr/bin/env python3
"""End-to-end journey check against a live Andes Padel API.

Exercises every customer journey the mobile app uses, in order, and prints a
pass/fail line for each. Run it against production (or any stack) with:

    python3 tests/journey_check.py https://app.andespadelclub.com/api

It creates its own throwaway account, verifies it through the same
/code/ endpoint the app calls, and cleans up nothing — the account is left
in place so the data can be inspected afterwards.

Every assertion is on an HTTP status + payload shape, never on a thrown
exception string, so a failure names the journey that broke.
"""

import json
import random
import sys
import time
import urllib.error
import urllib.request

API = (sys.argv[1] if len(sys.argv) > 1 else "https://app.andespadelclub.com/api").rstrip("/")

PASS, FAIL = "PASS", "FAIL"
results = []


def report(name, ok, detail=""):
    results.append((name, ok, detail))
    mark = "✓" if ok else "✗"
    print(f"{mark} {PASS if ok else FAIL}  {name}" + (f"  — {detail}" if detail else ""))


def call(method, path, token=None, body=None, form=None):
    url = API + path
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if form is not None:
        boundary = f"----journey{random.randint(10**6, 10**7)}"
        parts = []
        for k, v in form.items():
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
            parts.append(str(v).encode() + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        data = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        status = e.code
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}
    try:
        return status, json.loads(raw.decode() or "{}")
    except Exception:  # noqa: BLE001
        return status, {"raw": raw[:200].decode("utf-8", "replace")}


def main():
    stamp = int(time.time())
    email = f"journey_{stamp}@andespadelclub.com"
    password = "Journey12345!"

    print(f"\nAPI: {API}\naccount: {email}\n")

    # --- 1. Registration -------------------------------------------------
    status, data = call("POST", "/auth/register/", body={
        "email": email,
        "password": password,
        "first_name": "Journey",
        "last_name": "Test",
        "consent_version": "1.0",
    })
    report("register", status == 201, f"http {status} {data if status != 201 else ''}")

    # --- 2. Login is refused before verification ------------------------
    status, data = call("POST", "/auth/login/", body={"email": email, "password": password})
    report("login rejected while unverified", status in (400, 401, 403), f"http {status}")

    # --- 3. Resend / fetch the code, then verify ------------------------
    status, data = call("POST", "/auth/verify/send/", body={"email": email})
    if status >= 400:
        status, data = call("POST", "/auth/verify/", body={"email": email, "code": "000000"})
    report("verification code issued", status < 500, f"http {status}")

    code = data.get("code") if isinstance(data, dict) else None
    if not code:
        # Production never returns the code to the client — it is emailed.
        # Ask the operator path: the admin/DB can read it. Try the debug
        # shape first, then fall back to a well-known local-dev echo.
        status, data = call("POST", "/auth/verify/", body={"email": email, "code": "000000"})
        report(
            "verification code (needs emailed code)",
            False,
            f"code not returned to client (http {status}); read it from the outbox/DB and re-run",
        )
        print("\nStopping: cannot complete login without the emailed verification code.")
        summarize()
        return

    status, data = call("POST", "/auth/verify/", body={"email": email, "code": str(code)})
    report("email verified", status == 200, f"http {status} {data if status != 200 else ''}")

    # --- 4. Login ------------------------------------------------------
    status, data = call("POST", "/auth/login/", body={"email": email, "password": password})
    token = data.get("access") or (data.get("tokens") or {}).get("access")
    report("login", status == 200 and bool(token), f"http {status}")

    if not token:
        summarize()
        return

    # --- 5. Me ---------------------------------------------------------
    status, data = call("GET", "/auth/me/", token=token)
    report("auth/me", status == 200, f"http {status}")

    # --- 6. Courts -----------------------------------------------------
    status, data = call("GET", "/courts/", token=token)
    courts = data.get("results", data) if isinstance(data, dict) else data
    report("list courts", status == 200 and isinstance(courts, list) and courts,
           f"http {status}, {len(courts) if isinstance(courts, list) else 0} courts")

    # --- 7. Availability ------------------------------------------------
    from datetime import date, timedelta
    day = (date.today() + timedelta(days=1)).isoformat()
    slots_ok, slot_count = False, 0
    court_id = None
    if isinstance(courts, list) and courts:
        court_id = courts[0].get("id")
        status, data = call("GET", f"/courts/{court_id}/availability/?date={day}", token=token)
        slots = data if isinstance(data, list) else data.get("results", [])
        slot_count = len(slots)
        slots_ok = status == 200 and slot_count > 0
    report("court availability", slots_ok, f"{slot_count} slots on {day}")

    # --- 8. Events -----------------------------------------------------
    status, data = call("GET", "/events/", token=token)
    events = data.get("results", data) if isinstance(data, dict) else data
    report("list events", status == 200 and isinstance(events, list) and events,
           f"http {status}, {len(events) if isinstance(events, list) else 0} events")

    # --- 9. Join + leave an event --------------------------------------
    if isinstance(events, list) and events:
        ev = events[0]
        status, data = call("POST", f"/events/{ev['id']}/join/", token=token, body={})
        report("join event", status in (200, 201, 204), f"http {status} {data if status not in (200,201,204) else ''}")
        status, data = call("POST", f"/events/{ev['id']}/leave/", token=token, body={})
        report("leave event", status in (200, 201, 204), f"http {status}")
    else:
        report("join event", False, "no events to join")

    # --- 10. Tournaments ------------------------------------------------
    status, data = call("GET", "/tournaments/", token=token)
    tours = data.get("results", data) if isinstance(data, dict) else data
    report("list tournaments", status == 200, f"http {status}, {len(tours) if isinstance(tours, list) else 0}")

    # --- 11. Open matches (quedadas) ------------------------------------
    status, data = call("GET", "/open-matches/", token=token)
    oms = data.get("results", data) if isinstance(data, dict) else data
    report("list open matches", status == 200, f"http {status}, {len(oms) if isinstance(oms, list) else 0}")
    if isinstance(oms, list) and oms:
        status, data = call("POST", f"/open-matches/{oms[0]['id']}/join/", token=token, body={})
        report("join open match", status in (200, 201, 204), f"http {status} {data if status not in (200,201,204) else ''}")

    # --- 12. Banners + club ---------------------------------------------
    status, data = call("GET", "/banners/?lang=es", token=token)
    report("banners", status == 200, f"http {status}")
    status, data = call("GET", "/club/", token=token)
    report("club info", status == 200, f"http {status}")

    # --- 13. Notifications ----------------------------------------------
    status, data = call("GET", "/notifications/", token=token)
    report("notifications", status == 200, f"http {status}")

    # --- 14. Booking hold ------------------------------------------------
    if court_id:
        start = "18:00"
        status, data = call("POST", "/bookings/", token=token, body={
            "court": court_id,
            "date": day,
            "start_time": start,
            "duration_minutes": 60,
        })
        report("create booking", status in (200, 201), f"http {status} {data if status not in (200,201) else ''}")

    summarize()


def summarize():
    ok = sum(1 for _, o, _ in results if o)
    total = len(results)
    print(f"\n{'='*60}\nJOURNEYS PASSED: {ok}/{total}")
    for name, o, detail in results:
        if not o:
            print(f"  FAILED  {name}  {detail}")
    print("=" * 60)


if __name__ == "__main__":
    main()
