#!/usr/bin/env python3
"""Network Keeper's contact book: the people a student met, what they talked about,
and when there is a natural reason to reach back out.

Standard library only. State lives in ~/.config/network-keeper/contacts.json, which
survives restarts and Skill updates. Dates are passed in by Cubbie in the student's
local time (YYYY-MM-DD); the script never reads the sandbox clock.

    python3 scripts/contacts.py add --name "Dana Lee" --company "Charles Schwab" \
        --role "Risk analyst" --met-at "ASU fall career fair" --met-on 2026-10-24 \
        --notes "Does market risk; also ASU math" --hook "Apply to summer analyst role|2027-01-05"
    python3 scripts/contacts.py due --today 2026-10-24
    python3 scripts/contacts.py list --company schwab
    python3 scripts/contacts.py show --id c1
    python3 scripts/contacts.py done --id c1 --followup --on 2026-10-24
    python3 scripts/contacts.py done --id c1 --hook 1 --on 2027-01-05
    python3 scripts/contacts.py note --id c1 --text "Coffee chat, said to ping her in March" --on 2026-11-02
    python3 scripts/contacts.py hook --id c1 --text "Ask how the risk team intern project went" --on 2027-03-01
    python3 scripts/contacts.py edit --id c1 --email dana@example.com
    python3 scripts/contacts.py remove --id c1
    python3 scripts/contacts.py --sample due --today 2026-10-24   # bundled data, saves nothing

Exit codes: 0 done, 1 not found or bad input (one line on stderr), 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SAMPLE = HERE / "assets" / "sample_contacts.json"
STORE = Path.home() / ".config" / "network-keeper" / "contacts.json"
KEEP_WARM_DAYS = 90  # no contact and nothing scheduled for this long -> suggest a light check-in


class Problem(Exception):
    """Bad input or a missing contact; printed as one line, exit 1."""


# ------------------------------------------------------------------ storage


def load(sample: bool) -> dict:
    path = SAMPLE if sample else STORE
    if not path.exists():
        return {"next_id": 1, "contacts": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Problem(f"Can't read the contact book at {path}: {exc}") from None
    data.setdefault("next_id", 1)
    data.setdefault("contacts", [])
    return data


def save(data: dict, sample: bool) -> None:
    if sample:
        print("(sample data: nothing saved)")
        return
    STORE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=STORE.parent, prefix=".contacts.", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, STORE)


# ------------------------------------------------------------------ helpers


def parse_date(value: str, label: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        raise Problem(f"{label} must be a date like 2027-01-05, got {value!r}") from None


def parse_hook(raw: str) -> dict:
    text, sep, when = raw.rpartition("|")
    if not sep or not text.strip():
        raise Problem(f'--hook must look like "what to reach out about|YYYY-MM-DD", got {raw!r}')
    return {"text": text.strip(), "on": parse_date(when.strip(), "hook date"), "done": None}


def find(data: dict, cid: str) -> dict:
    for c in data["contacts"]:
        if c["id"].lower() == cid.lower():
            return c
    raise Problem(f"No contact with id {cid}. Run `list` to see ids.")


def label(c: dict) -> str:
    bits = [c["name"]]
    if c.get("role") and c.get("company"):
        bits.append(f'{c["role"]}, {c["company"]}')
    elif c.get("company"):
        bits.append(c["company"])
    return f'{c["id"]}  ' + " - ".join(bits)


def last_touch(c: dict) -> str:
    dates = [c.get("met_on") or ""] + [n["on"] for n in c.get("log", [])]
    if c.get("followed_up"):
        dates.append(c["followed_up"])
    dates += [h["done"] for h in c.get("hooks", []) if h.get("done")]
    return max(d for d in dates if d) if any(dates) else ""


def matches(c: dict, company: str | None, search: str | None) -> bool:
    if company and company.lower() not in (c.get("company") or "").lower():
        return False
    if search:
        hay = " ".join(str(c.get(k) or "") for k in ("name", "company", "role", "met_at", "notes", "email"))
        hay += " " + " ".join(n["text"] for n in c.get("log", []))
        hay += " " + " ".join(h["text"] for h in c.get("hooks", []))
        if search.lower() not in hay.lower():
            return False
    return True


# ------------------------------------------------------------------ commands


def cmd_add(data: dict, a: argparse.Namespace) -> bool:
    met_on = parse_date(a.met_on, "--met-on")
    hooks = [parse_hook(h) for h in a.hook or []]
    for c in data["contacts"]:
        same_name = c["name"].strip().lower() == a.name.strip().lower()
        same_company = (c.get("company") or "").strip().lower() == (a.company or "").strip().lower()
        if same_name and same_company and not a.force:
            print(f"Already saved: {label(c)}. Use `note` or `hook` to add to it, or add --force for a different person.")
            return False
    cid = f'c{data["next_id"]}'
    data["next_id"] += 1
    for i, h in enumerate(hooks, 1):
        h["n"] = i
    contact = {
        "id": cid, "name": a.name.strip(), "company": a.company, "role": a.role,
        "met_at": a.met_at, "met_on": met_on, "notes": a.notes,
        "email": a.email, "phone": a.phone, "linkedin": a.linkedin,
        "followed_up": None, "hooks": hooks, "log": [],
    }
    data["contacts"].append(contact)
    print(f"Saved {label(contact)}")
    for h in hooks:
        print(f'  reach back {h["on"]}: {h["text"]}')
    return True


def cmd_list(data: dict, a: argparse.Namespace) -> bool:
    found = [c for c in data["contacts"] if matches(c, a.company, a.search)]
    if not found:
        print("No contacts match." if data["contacts"] else "The contact book is empty.")
        return False
    found.sort(key=lambda c: c.get("met_on") or "", reverse=True)
    for c in found:
        where = f' | met {c["met_on"]}' + (f' at {c["met_at"]}' if c.get("met_at") else "")
        status = "" if c.get("followed_up") else " | follow-up not sent"
        print(label(c) + where + status)
    return False


def cmd_show(data: dict, a: argparse.Namespace) -> bool:
    c = find(data, a.id)
    print(label(c))
    for key, title in (("met_at", "Met at"), ("met_on", "Met on"), ("notes", "Talked about"),
                       ("email", "Email"), ("phone", "Phone"), ("linkedin", "LinkedIn")):
        if c.get(key):
            print(f"{title}: {c[key]}")
    print(f'Follow-up sent: {c["followed_up"] or "not yet"}')
    for h in c.get("hooks", []):
        state = f'done {h["done"]}' if h.get("done") else "open"
        print(f'Hook {h["n"]} ({h["on"]}, {state}): {h["text"]}')
    for n in c.get("log", []):
        print(f'{n["on"]}: {n["text"]}')
    return False


def cmd_due(data: dict, a: argparse.Namespace) -> bool:
    today = date.fromisoformat(parse_date(a.today, "--today"))
    horizon = today + timedelta(days=a.days)
    followups, hooks, warm = [], [], []
    for c in data["contacts"]:
        if not c.get("followed_up"):
            followups.append(c)
        open_hooks = [h for h in c.get("hooks", []) if not h.get("done")]
        for h in open_hooks:
            if date.fromisoformat(h["on"]) <= horizon:
                hooks.append((h["on"], c, h))
        touched = last_touch(c)
        if (c.get("followed_up") and not open_hooks and touched
                and (today - date.fromisoformat(touched)).days >= KEEP_WARM_DAYS):
            warm.append((touched, c))
    if not (followups or hooks or warm):
        print(f"Nothing due through {horizon.isoformat()}.")
        return False
    if followups:
        print("Follow-up not sent yet:")
        for c in sorted(followups, key=lambda c: c.get("met_on") or ""):
            age = (today - date.fromisoformat(c["met_on"])).days if c.get("met_on") else None
            when = "" if age is None else (" (met today)" if age == 0 else f" (met {age} days ago)")
            print(f"- {label(c)}{when}")
    if hooks:
        print(f"Reasons to reach back, through {horizon.isoformat()}:")
        for on, c, h in sorted(hooks, key=lambda x: x[0]):
            late = " OVERDUE" if date.fromisoformat(on) < today else ""
            print(f'- {on}{late}  {label(c)}  hook {h["n"]}: {h["text"]}')
    if warm:
        print(f"No contact in {KEEP_WARM_DAYS}+ days:")
        for touched, c in sorted(warm, key=lambda x: x[0]):
            print(f"- {label(c)} (last {touched})")
    return False


def cmd_done(data: dict, a: argparse.Namespace) -> bool:
    c = find(data, a.id)
    on = parse_date(a.on, "--on")
    if a.followup:
        c["followed_up"] = on
        print(f'Follow-up to {c["name"]} marked sent {on}.')
    if a.hook is not None:
        for h in c.get("hooks", []):
            if h["n"] == a.hook:
                h["done"] = on
                print(f'Hook {a.hook} for {c["name"]} marked done {on}.')
                break
        else:
            raise Problem(f'{c["name"]} has no hook {a.hook}. Run `show --id {c["id"]}`.')
    if not a.followup and a.hook is None:
        raise Problem("Say what is done: --followup or --hook N.")
    return True


def cmd_note(data: dict, a: argparse.Namespace) -> bool:
    c = find(data, a.id)
    c.setdefault("log", []).append({"on": parse_date(a.on, "--on"), "text": a.text.strip()})
    print(f'Noted for {c["name"]}.')
    return True


def cmd_hook(data: dict, a: argparse.Namespace) -> bool:
    c = find(data, a.id)
    h = parse_hook(f"{a.text}|{a.on}")
    h["n"] = max((x["n"] for x in c.get("hooks", [])), default=0) + 1
    c.setdefault("hooks", []).append(h)
    print(f'Reach back to {c["name"]} on {h["on"]}: {h["text"]} (hook {h["n"]})')
    return True


def cmd_edit(data: dict, a: argparse.Namespace) -> bool:
    c = find(data, a.id)
    changed = []
    for key in ("name", "company", "role", "met_at", "notes", "email", "phone", "linkedin"):
        value = getattr(a, key)
        if value is not None:
            c[key] = value
            changed.append(key.replace("_", " "))
    if a.met_on is not None:
        c["met_on"] = parse_date(a.met_on, "--met-on")
        changed.append("met on")
    if not changed:
        raise Problem("Nothing to change: pass a field such as --email.")
    print(f'Updated {c["name"]}: {", ".join(changed)}.')
    return True


def cmd_remove(data: dict, a: argparse.Namespace) -> bool:
    c = find(data, a.id)
    data["contacts"].remove(c)
    print(f'Removed {c["name"]}.')
    return True


# ------------------------------------------------------------------ CLI


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Network Keeper contact book.")
    p.add_argument("--sample", action="store_true", help="use the bundled sample data and save nothing")
    sub = p.add_subparsers(dest="command", required=True)

    def person_fields(sp, required: bool):
        sp.add_argument("--name", required=required)
        sp.add_argument("--company")
        sp.add_argument("--role")
        sp.add_argument("--met-at", dest="met_at")
        sp.add_argument("--met-on", dest="met_on", required=required, help="YYYY-MM-DD, student's local date")
        sp.add_argument("--notes")
        sp.add_argument("--email")
        sp.add_argument("--phone")
        sp.add_argument("--linkedin")

    sp = sub.add_parser("add", help="save someone the student met")
    person_fields(sp, required=True)
    sp.add_argument("--hook", action="append", help='"what to reach out about|YYYY-MM-DD", repeatable')
    sp.add_argument("--force", action="store_true", help="add even if the same name and company exist")

    sp = sub.add_parser("list", help="list contacts")
    sp.add_argument("--company")
    sp.add_argument("--search")

    sp = sub.add_parser("show", help="everything about one contact")
    sp.add_argument("--id", required=True)

    sp = sub.add_parser("due", help="follow-ups not sent, hooks coming up, contacts going cold")
    sp.add_argument("--today", required=True, help="student's local date, YYYY-MM-DD")
    sp.add_argument("--days", type=int, default=7, help="look this many days ahead for hooks (default 7)")

    sp = sub.add_parser("done", help="mark a follow-up sent or a hook handled")
    sp.add_argument("--id", required=True)
    sp.add_argument("--followup", action="store_true")
    sp.add_argument("--hook", type=int)
    sp.add_argument("--on", required=True)

    sp = sub.add_parser("note", help="log an interaction")
    sp.add_argument("--id", required=True)
    sp.add_argument("--text", required=True)
    sp.add_argument("--on", required=True)

    sp = sub.add_parser("hook", help="add a dated reason to reach back out")
    sp.add_argument("--id", required=True)
    sp.add_argument("--text", required=True)
    sp.add_argument("--on", required=True)

    sp = sub.add_parser("edit", help="change a contact's details")
    sp.add_argument("--id", required=True)
    person_fields(sp, required=False)

    sp = sub.add_parser("remove", help="delete a contact")
    sp.add_argument("--id", required=True)
    return p


COMMANDS = {"add": cmd_add, "list": cmd_list, "show": cmd_show, "due": cmd_due, "done": cmd_done,
            "note": cmd_note, "hook": cmd_hook, "edit": cmd_edit, "remove": cmd_remove}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = load(args.sample)
        if COMMANDS[args.command](data, args):
            save(data, args.sample)
    except Problem as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
