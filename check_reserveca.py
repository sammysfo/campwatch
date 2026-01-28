#!/usr/bin/env python3
import os
import socket
import ssl
import smtplib
from datetime import date, timedelta, datetime
from email.message import EmailMessage

import requests

ENDPOINT = "https://california-rdr.prod.cali.rd12.recreation-management.tylerapp.com/rdr/search/place"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://reservecalifornia.com",
    "referer": "https://reservecalifornia.com/",
    "tenantid": "cali",
    "user-agent": "campwatch/1.0",
}

LOG_PATH = "/tmp/campwatch.run.log"

def log_line(msg: str) -> None:
    with open(LOG_PATH, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")

def have_internet(timeout_sec: float = 3.0) -> bool:
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=timeout_sec).close()
        return True
    except OSError:
        return False

def build_payload(place_id: int, start_date: str, nights: int) -> dict:
    return {
        "PlaceId": place_id,
        "StartDate": start_date,
        "Nights": str(nights),
    }

def parse_place(data: dict, place_id: int) -> tuple[bool, str]:
    selected = data.get("SelectedPlace") or {}
    if selected.get("PlaceId") != place_id:
        return False, f"SelectedPlace was not PlaceId {place_id}."

    place_name = selected.get("Name", f"PlaceId {place_id} (unknown name)")
    facilities = selected.get("Facilities") or {}

    hits = []

    for fac in facilities.values():
        fac_name = fac.get("Name", "Unknown facility")
        unit_types = fac.get("UnitTypes") or {}

        for ut in unit_types.values():
            ut_name = ut.get("Name", "Unknown unit type")
            count = int(ut.get("AvailableCount") or 0)
            if count > 0:
                hits.append(
                    f"{fac_name} | {ut_name} | AvailableCount={count}"
                )

    if hits:
        return True, (
            f"{place_name}: AVAILABILITY FOUND\n"
            + "\n".join(hits)
        )

    avail_places = data.get("AvailablePlaces")
    return False, (
        f"{place_name}: no availability found (all AvailableCount = 0)\n"
        f"SelectedPlace.AvailableUnitCount={selected.get('AvailableUnitCount')}\n"
        f"AvailablePlaces (nearby parks metric)={avail_places}\n"
        f"StartDate={data.get('StartDate')} "
        f"NightsRequested={data.get('NightsRequested')}"
    )

def send_email(cfg: dict, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = cfg["email_from"]
    msg["To"] = cfg["email_to"]
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
        server.starttls(context=context)
        server.login(cfg["smtp_user"], cfg["smtp_pass"])
        server.send_message(msg)

def load_email_cfg() -> dict:
    return {
        "smtp_host": os.environ["CW_SMTP_HOST"],
        "smtp_port": int(os.getenv("CW_SMTP_PORT", "587")),
        "smtp_user": os.environ["CW_SMTP_USER"],
        "smtp_pass": os.environ["CW_SMTP_PASS"],
        "email_to": os.environ["CW_EMAIL_TO"],
        "email_from": os.environ.get("CW_EMAIL_FROM", os.environ["CW_SMTP_USER"]),
    }

def pick_start_date() -> tuple[str, str]:
    fixed = os.getenv("CW_START_DATE", "").strip()
    if fixed:
        return fixed, f"fixed start date {fixed}"

    start_in_days = int(os.getenv("CW_START_IN_DAYS", "30"))
    d = date.today() + timedelta(days=start_in_days)
    return d.isoformat(), f"rolling start date today+{start_in_days}"

def main() -> None:
    if not have_internet():
        log_line("no internet, skipping")
        return

    email_cfg = load_email_cfg()

    nights = int(os.getenv("CW_NIGHTS", "1"))
    start_date_iso, date_mode_desc = pick_start_date()
    place_id = int(os.getenv("CW_PLACE_ID", "681"))

    payload = build_payload(place_id, start_date_iso, nights)

    t0 = datetime.now().isoformat(timespec="seconds")

    try:
        r = requests.post(ENDPOINT, headers=HEADERS, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log_line(f"ERROR PlaceId={place_id} StartDate={start_date_iso} nights={nights} err={repr(e)}")
        return

    place_name = (data.get("SelectedPlace") or {}).get("Name") or f"PlaceId {place_id}"
    available, summary = parse_place(data, place_id)

    if available:
        subject = f"CampWatch OPEN {place_name} {start_date_iso} nights={nights}"
        body = (
            f"Time: {t0}\n"
            f"Date mode: {date_mode_desc}\n"
            f"Endpoint: {ENDPOINT}\n"
            f"PlaceId: {place_id}\n"
            f"StartDate: {start_date_iso}\n"
            f"Nights: {nights}\n\n"
            f"{summary}\n"
        )
        log_line(f"OPEN {place_name} {start_date_iso} nights={nights} emailing")
        send_email(email_cfg, subject, body)
    else:
        log_line(f"CLOSED {place_name} {start_date_iso} nights={nights}")

if __name__ == "__main__":
    main()
