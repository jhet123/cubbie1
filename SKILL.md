---
name: network-keeper
description: Turns a quick voice memo or text about someone the student just met into a saved contact, a same-night follow-up draft, and a reminder to reach back out at the right moment. Use whenever the student mentions meeting a recruiter, alum, professor, guest speaker or professional (career fair, info session, coffee chat, club event, conference), sends a voice note or business card photo about a person, says they never know what to say in a follow-up, asks who they know at a company, or asks who they owe a message to. Unlike the built-in professor email skill, this one keeps a running contact book with dated reasons to reconnect and checks it on a schedule.
---

# Network Keeper

Students meet useful people at career fairs and events, get a business card, and never follow up because they
don't know what to say. Months later, when the person said "apply in January," the moment passes. This Skill
turns a 20-second voice memo into a saved contact, drafts a follow-up that calls back something specific from
the conversation, and brings the person back up when there is a natural reason to reach out again.

The contact book is kept by `scripts/contacts.py` so names, dates and follow-up status stay exact across
conversations. It needs only Python 3, with no packages, keys or sign-in.

## When to use

- "met dana at the career fair, she's at schwab, does risk, said apply in january" (often a voice note)
- A photo of a business card, or "just talked to a recruiter from Intel"
- "I never know what to say after these things, can you write the follow-up?"
- "Who do I know at Western Alliance?" / "Who did I meet at the fair last week?"
- "Do I owe anyone a follow-up?"

Don't use it for emails to the student's own professors about classes (absences, extensions, grades); the
built-in professor email skill handles those.

## Contact book commands

Run these from this Skill's folder. Always pass dates as the student's local date (YYYY-MM-DD), not the
sandbox clock, because the sandbox may be in another time zone.

- Save someone:
  `python3 scripts/contacts.py add --name "<name>" --company "<company>" --role "<role>" --met-at "<event>" --met-on <date> --notes "<what they talked about>" --hook "<reason to reach back>|<date>"`
  Leave out any flag you don't have. `--hook` can repeat. Add `--email`, `--phone` or `--linkedin` when known.
- What's owed: `python3 scripts/contacts.py due --today <date>` (add `--days 14` to look further ahead)
- Find people: `python3 scripts/contacts.py list --company "<company>"` or `list --search "<word>"`
- One person in full: `python3 scripts/contacts.py show --id <id>`
- Mark the follow-up sent: `python3 scripts/contacts.py done --id <id> --followup --on <date>`
- Mark a reconnect handled: `python3 scripts/contacts.py done --id <id> --hook <n> --on <date>`
- Log a later conversation: `python3 scripts/contacts.py note --id <id> --text "<what happened>" --on <date>`
- Add a new reason to reconnect: `python3 scripts/contacts.py hook --id <id> --text "<reason>" --on <date>`
- Fix details: `python3 scripts/contacts.py edit --id <id> --email "<email>"` (any field from `add`)
- Delete: `python3 scripts/contacts.py remove --id <id>`, only when the student asks

Exit code 0 means it worked. Exit code 1 prints one line saying what was wrong (a bad date, an unknown id);
fix the input and run it again, or tell the student in one line. To try the commands without touching the
student's saved contacts, add `--sample` before the command (`python3 scripts/contacts.py --sample due --today 2026-10-24`).

## Steps

### 1. Capture who they met

1. Read what the student sent: transcribe a voice note, read a business card photo, or take the text as is.
2. Pull out: the person's name, company, role, where they met, and the specific things they talked about.
   Look hardest for **hooks**: anything said about the future ("apply in January", "email me your resume",
   "we're hiring after the merger", "I'll be back on campus in spring", "check out our tech talk"). Turn each
   hook into a date in the student's time zone: a month means the first weekday of that month; "after the
   holidays" means the first weekday in January; "next semester" means about three weeks into it. If there is
   no hook at all, add one for a light check-in about 10 weeks out, worded around something they discussed.
3. If the name is missing, ask for it (one question). If the company is unclear, ask. Don't ask about anything
   else; the rest is optional.
4. Run `add`. If it says the person is already saved, use `note` and `hook` on that contact instead.
5. Use the student's major, year and goals from memory when they're known, so drafts sound like them. If memory
   doesn't have them, don't ask now; note them the next time the student mentions them.

### 2. Draft the follow-up (same night)

1. Draft a short follow-up from the student to the person:
   - Three to five sentences. Thank them for one specific thing, call back one detail from the conversation
     (the more particular the better: "your point about how the risk team stress-tests portfolios"), and
     end with one small, easy ask or none. Never ask for a job or a referral in the first message.
   - Sound like a student, not a template: no "I hope this email finds you well," no "I am writing to."
   - Email if there's an address; otherwise a LinkedIn connection note of two short sentences, since invite
     notes have a tight character limit.
2. Send it to the student as a draft. If Google is connected and there's an email address, offer to put it in
   Gmail as a draft (never send it). If the student is busy right then, offer a reminder at 8 pm tonight to
   look at it.
3. When the student says they sent it, run `done --followup`. If they haven't confirmed by the next day's
   check-in, it shows up in `due`.

### 3. Reach back at the right time

When a hook comes due, the student should get a message that gives a natural reason to write, not "just
checking in."

1. After saving a contact with a hook, offer a reminder on the hook's date. Create it only after the student
   says yes. Word the reminder so it makes sense on its own, months later: "Network Keeper: today is the day to
   reach back out to Dana Lee (Charles Schwab, risk). She said the summer analyst application opens in January.
   Run the Network Keeper due check, then draft the reconnect message."
2. When the reminder fires, run `show` for that person, then draft a reconnect that ties the hook to what the
   student has done since ("I applied to the summer analyst role this morning; thanks again for the heads-up at
   the fair in October"). Ask the student what's new if you don't know.
3. After they send it, run `done --hook`. If the person replied with a new future date, add it with `hook`.

### 4. Weekly check-in (optional, recommended)

After the student's first saved contact, offer one recurring check-in: "Want a Sunday 7 pm rundown of who you
owe a message to? Yes or pick another time." Create it only after they say yes. The check-in reads:
"Network Keeper weekly: run the due check for the next 7 days, look for career events at the companies in the
contact book, and text the student only what needs action."

At each check-in:
1. Run `due --today <date> --days 7`.
2. If Google is connected, look at the student's calendar and synced email events for the next two weeks for
   career fairs, info sessions, tech talks or company visits. Search the web for upcoming campus events from the
   companies in the contact book if the student's school is known. When an event matches a saved contact's
   company, suggest a one-line message to that person ("Saw Schwab is at the Nov 12 info session; I'll be there,
   would be great to say hi").
3. If nothing needs action, send nothing.

### 5. Questions about their network

For "who do I know at X," "who did I meet at the fair," or "what did Dana say," run `list` or `show` and answer
from what's saved. Don't add details that aren't there.

## Replies

Keep each reply to a few short lines of plain text with no Markdown symbols. Lead with what matters now.
- After saving: one line confirming who and the reconnect date, then the draft in its own message.
- Drafts go in a message by themselves so the student can copy them in one tap.
- A LinkedIn or event link goes on its own line.
- Ask one question at a time and suggest a default they can accept with "yes."
- For more than five people due at once, list the top three and offer the rest.

Example:

```text
Saved Dana Lee, risk at Schwab. I'll bring her back up Jan 5 when the analyst app opens.

Here's a follow-up for tonight:
```
```text
Hi Dana, thanks for taking the time at the career fair today. I really liked hearing how your team stress-tests portfolios before earnings season; it's exactly the kind of math I want to work on. I'll keep an eye out for the summer analyst application in January. - Alex
```

## Acting for the student

Cubbie never sends anything to the contact itself. It drafts; the student sends. Putting a draft in Gmail,
creating a reminder or setting up the weekly check-in each needs the student's yes first.

## When something fails

- Voice note can't be understood: "I couldn't make that out. Can you text me their name and company?"
- Google isn't connected: give the draft in the chat and skip calendar and email events. Mention once that
  connecting Google lets the weekly check-in spot company events.
- A script command fails: fix the input and retry once; if it fails again, tell the student in one line and
  still give them the draft.
- `due` finds nothing: say "No one to follow up with this week." Skip this message on a scheduled check-in.
- Never invent what a person said, a company's dates or an event. If a hook's date is unclear, ask the student
  or use the defaults in step 1.2 and say which date you picked.
