import argparse
import csv
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PERSONAL = {'pet_birthday', 'birthday', 'family_event', 'personal_event'}
DATED = PERSONAL | {'business_date', 'handover'}
KINDS = DATED | {'interest', 'preference'}
SENSITIVE = {'health', 'religion', 'politics', 'ethnicity', 'union', 'sexuality', 'finances'}
LEAD_DAYS = {'business_date': 7, 'handover': 5}

TEMPLATES = {
    'pet_birthday': 'Hi {first}, if I remember right {pet_line} on {weekday}. Hope there is an extra treat on the day. {sign}',
    'birthday': 'Hi {first}, happy birthday for {weekday}. Hope you get a few hours away from site. {sign}',
    'family_event': 'Hi {first}, all the best to {subject} for the {detail} on {weekday}. You must be proud. {sign}',
    'personal_event': 'Hi {first}, good luck with the {detail} on {weekday}. {sign}',
    'business_date': 'Hi {first}, with the {detail} coming up on {long_date}, is there anything you need from our side before then? Happy to come by. {sign}',
    'handover': 'Hi {first}, it is {years} since we handed over {subject}. How is it holding up? I would be glad to walk the site with your team and hear what is planned next. {sign}',
    'quiet': 'Hi {first}, it has been a while since we last spoke. {hook}Would you have 20 minutes for a coffee in the next two weeks? {sign}',
}
ACTIONS = {
    'business_date': 'Call before the date and offer help or a site visit',
    'handover': 'Propose a site walk and ask about the next phase',
    'quiet': 'Ask for a short coffee meeting',
}


def read(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def load(contacts_path, notes_path):
    contacts = {c['contact_id']: c for c in read(contacts_path)}
    notes = []
    for n in read(notes_path):
        if n['kind'] in SENSITIVE:
            print(f"skipped note for {n['contact_id']}: '{n['kind']}' is sensitive personal data and is not used", file=sys.stderr)
        elif n['kind'] not in KINDS:
            print(f"skipped note for {n['contact_id']}: unknown kind '{n['kind']}'", file=sys.stderr)
        elif not n.get('source', '').strip():
            print(f"skipped note for {n['contact_id']}: no source recorded", file=sys.stderr)
        elif n['contact_id'] not in contacts:
            print(f"skipped note: no contact {n['contact_id']}", file=sys.stderr)
        else:
            notes.append(n)
    return contacts, notes


def occurrences(note, start, end):
    raw = note['date'].strip()
    if not raw:
        return []
    if len(raw) == 5:
        month, day, first_year = int(raw[:2]), int(raw[3:]), None
    else:
        d = date.fromisoformat(raw)
        if note.get('recurring', '').lower() != 'yes':
            return [(d, None)] if start <= d <= end else []
        month, day, first_year = d.month, d.day, d.year
    found = []
    for year in (start.year, start.year + 1):
        try:
            d = date(year, month, day)
        except ValueError:
            continue
        if start <= d <= end:
            found.append((d, year - first_year if first_year else None))
    return found


def first_name(full):
    return full.split()[0]


def channel(notes, contact_id):
    return next((n['detail'] for n in notes if n['contact_id'] == contact_id and n['kind'] == 'preference'), '')


def gift_rule(contact, kind, cap):
    if kind not in PERSONAL:
        return 'No gift'
    if contact['sector'].strip().lower() == 'public':
        return 'Message only, no gift: public-sector contact'
    return f'Optional small gift, up to MUR {cap:,}'


def draft(kind, contact, note, when, years):
    count = years or 0
    return TEMPLATES[kind].format(
        first=first_name(contact['name']),
        subject=note.get('subject') or 'it',
        detail=note.get('detail', ''),
        weekday=when.strftime('%A'),
        long_date=when.strftime('%A %d %B'),
        pet_line=f"{note.get('subject')} turns {years}" if years else f"it is {note.get('subject')}'s birthday",
        years=f'{count} year' + ('' if count == 1 else 's'),
        hook=note.get('hook', ''),
        sign=first_name(contact['account_owner']),
    )


def label(note):
    subject, detail = note.get('subject', ''), note.get('detail', '')
    if note['kind'] == 'pet_birthday':
        return f"{subject}'s birthday ({detail})" if detail else f"{subject}'s birthday"
    if note['kind'] == 'birthday':
        return 'birthday'
    if note['kind'] == 'handover':
        return f'handover anniversary: {subject}'
    return f'{subject}: {detail}' if subject else detail


def reminder_day(when, kind, start):
    remind = when - timedelta(days=LEAD_DAYS.get(kind, 3))
    while remind.weekday() >= 5:
        remind -= timedelta(days=1)
    return max(start, remind)


def plan(contacts, notes, start, days, cap, quiet_after):
    end = start + timedelta(days=days)
    rows = []
    for note in notes:
        if note['kind'] not in DATED:
            continue
        contact = contacts[note['contact_id']]
        for when, years in occurrences(note, start, end):
            rows.append(touchpoint(contact, notes, note['kind'], reminder_day(when, note['kind'], start), when, label(note),
                                   note['source'], draft(note['kind'], contact, note, when, years), cap))
    for contact in contacts.values():
        last = date.fromisoformat(contact['last_contact'])
        if (start - last).days >= quiet_after:
            interest = next((n for n in notes if n['contact_id'] == contact['contact_id'] and n['kind'] == 'interest'), None)
            hook = f"Last time you mentioned {interest['detail']}, and we have a few things to show you on that. " if interest else ''
            rows.append(touchpoint(contact, notes, 'quiet', start, start, f'no contact for {(start - last).days} days',
                                   f'last contact {last:%d %b %Y}', draft('quiet', contact, {'hook': hook}, start, None), cap))
    return sorted(rows, key=lambda r: (r['remind_on'], r['contact']))


def touchpoint(contact, notes, kind, remind, when, what, source, message, cap):
    how = channel(notes, contact['contact_id'])
    action = ACTIONS.get(kind, 'Send a short personal note')
    return {
        'remind_on': remind.isoformat(),
        'event_date': when.isoformat(),
        'account_owner': contact['account_owner'],
        'contact': contact['name'],
        'organisation': contact['organisation'],
        'sector': contact['sector'],
        'kind': kind,
        'what': what,
        'action': action + (f' ({how})' if how else ''),
        'gift': gift_rule(contact, kind, cap),
        'draft': message,
        'source': source,
    }


def ics_text(value):
    return value.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def fold(line):
    parts = [line[i:i + 73] for i in range(0, len(line), 73)]
    return '\r\n '.join(parts)


def write_ics(rows, path):
    stamp = datetime.now().strftime('%Y%m%dT%H%M%S')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Task 5//KDM touchpoints//EN', 'CALSCALE:GREGORIAN']
    for i, r in enumerate(rows):
        day = date.fromisoformat(r['remind_on'])
        body = f"{r['action']}\nGift: {r['gift']}\n\nDraft:\n{r['draft']}\n\nEvent date: {r['event_date']}\nSource: {r['source']}"
        lines += [
            'BEGIN:VEVENT',
            f'UID:{day:%Y%m%d}-{i}-kdm-touchpoint',
            f'DTSTAMP:{stamp}',
            f'DTSTART;VALUE=DATE:{day:%Y%m%d}',
            f'DTEND;VALUE=DATE:{day + timedelta(days=1):%Y%m%d}',
            fold('SUMMARY:' + ics_text(f"{r['contact']} ({r['organisation']}): {r['what']}")),
            fold('DESCRIPTION:' + ics_text(body)),
            'END:VEVENT',
        ]
    lines.append('END:VCALENDAR')
    Path(path).write_text('\r\n'.join(lines) + '\r\n', encoding='utf-8')


def write_csv(rows, path):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['remind_on'])
        w.writeheader()
        w.writerows(rows)


def brief(contact_id, contacts, notes, start, cap):
    c = contacts[contact_id]
    mine = [n for n in notes if n['contact_id'] == contact_id]
    last = date.fromisoformat(c['last_contact'])
    out = [f"{c['name']}, {c['role']}, {c['organisation']} ({c['sector']} sector)",
           f"Account owner: {c['account_owner']}; last contact {last:%d %b %Y} ({(start - last).days} days ago)"]
    if c.get('opportunity'):
        value = f", MUR {int(c['opportunity_value_mur']):,}" if c.get('opportunity_value_mur') else ''
        out.append(f"Open opportunity: {c['opportunity']}{value}. Next step: {c['next_step']} by {c['next_step_date']}")
    sections = [('Preferences', 'preference'), ('Interests', 'interest')]
    for title, kind in sections:
        items = [n for n in mine if n['kind'] == kind]
        if items:
            out.append(f'{title}:')
            out += [f"  - {n['detail']} [{n['source']}]" for n in items]
    upcoming = sorted(((when, n) for n in mine if n['kind'] in DATED for when, _ in occurrences(n, start, start + timedelta(days=90))),
                      key=lambda x: x[0])
    if upcoming:
        out.append('Coming up in the next 90 days:')
        out += [f"  - {when:%a %d %b}: {label(n)} [{n['source']}]" for when, n in upcoming]
    interest = next((n['detail'] for n in mine if n['kind'] == 'interest'), None)
    personal = next(((when, n) for when, n in upcoming if n['kind'] in PERSONAL), None)
    points = [f"Move the deal on: {c['next_step']} by {c['next_step_date']}." if c.get('next_step') else None,
              f'Open with what they care about: {interest}.' if interest else None,
              f"If the moment is right, mention {label(personal[1])} on {personal[0]:%d %b}." if personal else None]
    out.append('Talking points:')
    out += [f'  {i}. {p}' for i, p in enumerate([p for p in points if p], 1)]
    out.append(f"Gifts: {gift_rule(c, 'birthday', cap)}")
    return '\n'.join(out)


def forget(contact_id, contacts_path, notes_path):
    for path in (contacts_path, notes_path):
        rows = read(path)
        kept = [r for r in rows if r['contact_id'] != contact_id]
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(kept)
        print(f'{Path(path).name}: removed {len(rows) - len(kept)} row(s) for {contact_id}')


def main():
    p = argparse.ArgumentParser(description='Personal and business touchpoints for key decision makers')
    p.add_argument('--contacts', default=HERE / 'kdm_contacts.csv', help='CSV of key decision makers')
    p.add_argument('--notes', default=HERE / 'kdm_notes.csv', help='CSV of notes from meetings')
    p.add_argument('--start', default=date.today().isoformat(), help='first day of the plan (YYYY-MM-DD)')
    p.add_argument('--days', type=int, default=60, help='how many days ahead to plan')
    p.add_argument('--quiet-after', type=int, default=60, help='flag contacts not reached for this many days')
    p.add_argument('--gift-cap', type=int, default=2000, help='largest gift allowed for private-sector contacts, in MUR')
    p.add_argument('--brief', metavar='CONTACT_ID', help='print a pre-meeting brief for one contact')
    p.add_argument('--forget', metavar='CONTACT_ID', help='delete a contact and all their notes')
    p.add_argument('--out', default='touchpoints', help='name for the .ics and .csv files written')
    a = p.parse_args()
    if a.forget:
        forget(a.forget, a.contacts, a.notes)
        return
    start = date.fromisoformat(a.start)
    contacts, notes = load(a.contacts, a.notes)
    if a.brief:
        print(brief(a.brief, contacts, notes, start, a.gift_cap))
        return
    rows = plan(contacts, notes, start, a.days, a.gift_cap, a.quiet_after)
    write_ics(rows, f'{a.out}.ics')
    write_csv(rows, f'{a.out}.csv')
    print(f'{len(rows)} touchpoints from {start:%d %b} to {start + timedelta(days=a.days):%d %b %Y}\n')
    for r in rows:
        print(f"{r['remind_on']}  {r['account_owner']:<12} {r['contact']} ({r['organisation']}): {r['what']}")
        print(f"            {r['action']}. {r['gift']}.")
    print(f'\nCalendar: {a.out}.ics (import into Outlook or Google Calendar). Drafts and sources: {a.out}.csv')


if __name__ == '__main__':
    main()
