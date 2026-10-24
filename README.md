# Network Keeper

A Cubbie Skill for the Cubbie Hackathon (Track 1).

You meet someone at a career fair, get their card, and never follow up because you don't know what to say.
Network Keeper fixes that. Text Cubbie a 20-second voice memo ("met Dana, Schwab, does risk, said apply in
January") and it:

- saves Dana to your contact book, along with what you talked about
- drafts a follow-up for tonight that calls back something specific from the conversation
- brings Dana back up in January with a natural reason to reach out
- (optional) checks every Sunday who you owe a message to and which of your contacts' companies have events
  coming up

Cubbie only drafts. You send.

## Install

Text this repository's link to Cubbie and reply "yes" when it asks to fetch it.

## Try it

- Send a voice note: "just met a recruiter from Intel named Priya, she said to apply when the spring intern
  posting goes up in February"
- "Who do I know at Schwab?"
- "Do I owe anyone a follow-up?"

## How it's built

- `SKILL.md`: what Cubbie does, in plain words, using the abilities it already has (voice notes, memory,
  Gmail drafts, calendar and email events, web, scheduled check-ins).
- `scripts/contacts.py`: a small contact book, using only the Python standard library, so names, dates and
  follow-up status stay exact across conversations. It saves to `~/.config/network-keeper/contacts.json`.
- `assets/sample_contacts.json`: sample data for `python3 scripts/contacts.py --sample due --today 2026-10-24`.
