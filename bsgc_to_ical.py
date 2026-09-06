import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    ),
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
}

CATEGORY_EMOJIS = {
    'Holidays': '🌴',
    'Important Dates': '📌',
    'Exams': '📝',
    'Meetings': '👥',
    'School Events': '🎉',
    'Field Trips': '🚌',
    'Sports': '⚽',
    'Default': '📅',
}


def clean_text(text):
    if not text:
        return ''
    return re.sub(r'\s+', ' ', text).strip()


def scrape_bsgc_year(session, year):
    url = f'https://bs-gc.com/en/school-life/calendar/eventsbyyear/{year}/-'
    print(f'[+] Fetching annual events from: {url}')

    events = []
    try:
        res = session.get(url, timeout=20)
        if res.status_code != 200:
            print(f'[-] HTTP Error {res.status_code} accessing year {year}')
            return events

        # Parse static HTML response
        html_content = res.content.decode('utf-8', errors='replace')
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find event links containing detailed repeat/day links
        links = soup.find_all(
            'a',
            href=re.compile(
                r'icalrepeat\.detail|eventsbyday|day\.listevents', re.I
            ),
        )

        for link in links:
            title = clean_text(link.get_text())
            href = link.get('href', '')

            # Ignore empty strings or generic navigation links
            if not title or len(title) < 2 or 'eventsbyyear' in href:
                continue

            # Extract date directly from the link URL: /YYYY/MM/DD/ or /YYYY-MM-DD
            date_match = re.search(rf'/{year}/(\d{{1,2}})/(\d{{1,2}})', href)
            if date_match:
                month = int(date_match.group(1))
                day = int(date_match.group(2))
                try:
                    event_date = datetime(year, month, day)
                    events.append({'title': title, 'date': event_date})
                except ValueError:
                    pass

    except Exception as e:
        print(f'[-] Exception scraping year {year}: {e}')

    return events


def generate_full_ics(start_year=2026):
    cal = Calendar()
    cal.add('prodid', '-//British School of Gran Canaria//School Calendar//ES')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'BSGC - Calendario Escolar')
    cal.add('x-wr-timezone', 'Atlantic/Canary')

    session = requests.Session()
    session.headers.update(HEADERS)

    # Scrape both academic school years across the split term
    scraped_events = []
    scraped_events.extend(scrape_bsgc_year(session, start_year))
    scraped_events.extend(scrape_bsgc_year(session, start_year + 1))

    total_events = 0
    seen_uids = set()

    for item in scraped_events:
        title = item['title']
        event_date = item['date']

        print(f'[+] Item Title: {title}')
        
        # Ensure academic range filtering (Sept start_year to Aug start_year + 1)
        if (event_date < datetime(start_year, 9, 1)) or (
            event_date > datetime(start_year + 1, 8, 31)
        ):
            continue

        uid_key = f"{event_date.strftime('%Y-%m-%d')}-{title}"
        if uid_key in seen_uids:
            continue
        seen_uids.add(uid_key)

        event = Event()
        summary_str = f"{CATEGORY_EMOJIS['Default']} {title}"
        event.add('summary', summary_str)
        event.add('dtstart', event_date.date())
        event.add('dtend', event_date.date() + timedelta(days=1))
        event.add('uid', f'bsgc-{abs(hash(uid_key))}@bs-gc.com')

        cal.add_component(event)
        total_events += 1

    output_filename = 'bsgc_calendar.ics'

    with open(output_filename, 'wb') as f:
        f.write(cal.to_ical())

    print(
        f"\n[✓] Finished: {total_events} detailed events saved to"
        f" '{output_filename}'."
    )


if __name__ == '__main__':
    generate_full_ics(2026)
