"""Controleert de IntoGolf-API van Golfbaan Delfland op nieuwe vrije starttijden
en stuurt een pushmelding via ntfy zodra er een tijd bijkomt."""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API = "https://delfland.baan.intogolf.nl/api/igg?date={date}&locNr=29"
BOOK_URL = "https://www.delflandgolf.nl/reserveer-starttijd/reserveren-starttijd/"
TZ = ZoneInfo("Europe/Amsterdam")
STATE_FILE = "state/seen.json"

# Leeg = automatisch de eerstvolgende WEEKDAY (0=maandag ... 5=zaterdag).
DATES = [d.strip() for d in os.environ.get("DATES", "").split(",") if d.strip()]
WEEKDAY = int(os.environ.get("WEEKDAY", "5"))
TIME_FROM = os.environ.get("TIME_FROM", "11:15")
TIME_TO = os.environ.get("TIME_TO", "13:45")
COURSES = [c.strip().lower() for c in os.environ.get("COURSES", "rood,geel,blauw").split(",") if c.strip()]
MIN_PLAYERS = int(os.environ.get("MIN_PLAYERS", "1"))
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")


def minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def hhmm(mins):
    return f"{mins // 60:02d}:{mins % 60:02d}"


def fetch(date):
    req = urllib.request.Request(API.format(date=date), headers={"User-Agent": "starttijd-alert"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["payload"]


def available_slots(date):
    """Vrije tijden binnen het tijdvenster, als {sleutel: omschrijving}."""
    lo, hi = minutes(TIME_FROM), minutes(TIME_TO)
    courses = fetch(date)
    names = {c["crlNr"]: c["crlNameInternet"] or c["crlName"] for c in courses}
    slots = {}
    for course in courses:
        name = (course["crlNameInternet"] or course["crlName"]).lower()
        if COURSES and name not in COURSES:
            continue
        times = course["times"].values() if isinstance(course["times"], dict) else course["times"]
        for t in times:
            start = t["sttTimeFrom"]
            free = t["sttMaxPlayers"] - t.get("playerCount", 0)
            if not lo <= start <= hi or free < MIN_PLAYERS:
                continue
            holes = "9 holes"
            if t.get("sttCrlNrNext"):
                holes = f"9 of 18 holes (daarna {names.get(t['sttCrlNrNext'], '?')})"
            key = f"{date} {hhmm(start)} {name}"
            slots[key] = f"{hhmm(start)} lus {name}, {holes}, {free} plek(ken) vrij"
    return slots


def target_dates(now):
    if DATES:
        return [d for d in DATES if now.date() <= datetime.strptime(d, "%Y-%m-%d").date()]
    day = now.date() + timedelta(days=(WEEKDAY - now.weekday()) % 7)
    if day == now.date() and now.strftime("%H:%M") > TIME_TO:
        day += timedelta(days=7)
    return [day.isoformat()]


def notify(title, body, priority="high"):
    print(f"[melding] {title}\n{body}")
    if not NTFY_TOPIC:
        print("NTFY_TOPIC ontbreekt, geen melding verstuurd")
        return
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=body.encode("utf-8"),
        headers={"Title": title, "Priority": priority, "Tags": "golf", "Click": BOOK_URL},
    )
    urllib.request.urlopen(req, timeout=30).read()


def main():
    now = datetime.now(TZ)
    dates = target_dates(now)
    if not dates:
        print("Alle opgegeven data zijn voorbij.")
        return

    if os.environ.get("TEST_RUN"):
        global COURSES
        COURSES = []  # test: alle lussen, zodat er ook echt tijden in de melding staan
        current = {}
        for date in dates:
            current.update(available_slots(date))
        body = "\n".join(list(current.values())[:15]) or "Er is nu niets vrij."
        notify(f"TEST starttijd-alert ({', '.join(dates)})", f"Dit is een test. Vrij tussen {TIME_FROM} en {TIME_TO}, alle lussen:\n{body}")
        return

    state = json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}
    # Nieuwe doeldatum (of eerste run): alleen een overzicht sturen, niet elke tijd als "nieuw".
    first_run = state.get("dates") != dates
    seen = {} if first_run else state.get("slots", {})

    current = {}
    for date in dates:
        current.update(available_slots(date))

    new = {k: v for k, v in current.items() if k not in seen}
    print(f"{now:%Y-%m-%d %H:%M} - {len(current)} vrij in venster, {len(new)} nieuw")
    for v in current.values():
        print("  ", v)

    window = f"{', '.join(dates)} tussen {TIME_FROM} en {TIME_TO} ({', '.join(COURSES) or 'alle lussen'})"
    if first_run:
        body = "Nu vrij:\n" + "\n".join(current.values()) if current else "Er is nu nog niets vrij."
        notify(f"Starttijd-alert: ik let nu op {', '.join(dates)}", f"Ik let op {window}.\n{body}", priority="default")
    elif new:
        new_dates = sorted({k.split()[0] for k in new})
        notify(f"Nieuwe starttijd vrij! ({', '.join(new_dates)})", "\n".join(new.values()) + "\n\nSnel boeken!", priority="urgent")

    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    json.dump({"dates": dates, "slots": current}, open(STATE_FILE, "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
