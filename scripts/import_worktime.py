#!/usr/bin/env python3
"""One-shot import of sessions and manual entries from the old worktime tracker."""

import requests

OLD = "http://192.168.0.125:8000"
NEW = "http://192.168.0.125:8001"

IMPORT_START = "2026-01-01T00:00:00"
IMPORT_END   = "2026-05-17T00:00:00"  # exclusive — covers through May 16


# ── Sessions ──────────────────────────────────────────────────────────────────

def fetch_all_old_sessions():
    sessions = []
    page = 1
    while True:
        data = requests.get(f"{OLD}/api/sessions", params={"page": page, "per_page": 50}).json()
        batch = data["sessions"]
        if not batch:
            break
        for s in batch:
            if s["login_at"] < IMPORT_START:
                return sessions
            if s["logout_at"] and s["login_at"] < IMPORT_END:
                sessions.append(s)
        if len(sessions) >= data["total"]:
            break
        page += 1
    return sessions


def fetch_all_cad_sessions():
    sessions = []
    page = 1
    while True:
        data = requests.get(f"{NEW}/api/sessions", params={"page": page, "per_page": 50}).json()
        sessions.extend(data["sessions"])
        if len(sessions) >= data["total"]:
            break
        page += 1
    return sessions


def import_sessions():
    old_sessions = fetch_all_old_sessions()
    cad_sessions = fetch_all_cad_sessions()

    existing = {(s["computer"].lower(), s["started_at"]) for s in cad_sessions}
    to_import = [
        s for s in old_sessions
        if (s["computer"].lower(), s["login_at"]) not in existing
    ]

    # Delete CAD sessions fully contained within an old session being imported
    old_ranges = [(s["computer"].lower(), s["login_at"], s["logout_at"]) for s in to_import]
    old_starts = {(s["computer"].lower(), s["login_at"]) for s in old_sessions}
    for cad in cad_sessions:
        for comp, start, end in old_ranges:
            if (cad["computer"].lower() == comp
                    and cad["started_at"] >= start
                    and cad["ended_at"] <= end
                    and (cad["computer"].lower(), cad["started_at"]) not in old_starts):
                r = requests.delete(f"{NEW}/api/sessions/{cad['id']}")
                print(f"Deleted fragment: CAD session {cad['id']} ({cad['started_at']}–{cad['ended_at']})")

    imported = 0
    for s in sorted(to_import, key=lambda x: x["login_at"]):
        r = requests.post(f"{NEW}/api/sessions", json={
            "computer": s["computer"],
            "started_at": s["login_at"],
            "ended_at": s["logout_at"],
            "is_work": s["is_work"],
            "note": s["note"],
        })
        if r.status_code == 201:
            imported += 1
            print(f"Imported session: {s['login_at']}  {s['computer']}")
        else:
            print(f"FAILED session:   {s['login_at']}  {s['computer']}  {r.status_code} {r.text}")

    print(f"Sessions: {imported}/{len(to_import)} imported.")
    return imported


# ── Manual entries ────────────────────────────────────────────────────────────

def import_manual_entries():
    old_manual = requests.get(f"{OLD}/api/manual").json()
    cad_manual = requests.get(f"{NEW}/api/manual").json()

    # Filter to our date range
    old_manual = [m for m in old_manual if IMPORT_START[:10] <= m["date"] <= IMPORT_END[:10]]

    existing = {(m["date"], m.get("note")) for m in cad_manual}
    to_import = [m for m in old_manual if (m["date"], m.get("note")) not in existing]

    imported = 0
    for m in sorted(to_import, key=lambda x: x["date"]):
        payload = {
            "date": m["date"],
            "hours": m.get("hours"),
            "note": m.get("note"),
        }
        if m.get("start_at"):
            payload["start_at"] = m["start_at"]
        if m.get("end_at"):
            payload["end_at"] = m["end_at"]

        r = requests.post(f"{NEW}/api/manual", json=payload)
        if r.status_code == 201:
            imported += 1
            print(f"Imported manual:  {m['date']}  {m.get('hours', '')}h  {m.get('note', '')}")
        else:
            print(f"FAILED manual:    {m['date']}  {r.status_code} {r.text}")

    print(f"Manual entries: {imported}/{len(to_import)} imported.")
    return imported


# ── Main ──────────────────────────────────────────────────────────────────────

print(f"Importing from {IMPORT_START[:10]} through {IMPORT_END[:10]}\n")
import_sessions()
print()
import_manual_entries()
