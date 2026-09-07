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

def parse_date_str(date_str):
    """Converts '01 January 2026' to a datetime object."""
    date_str = date_str.strip()
    return datetime.strptime(date_str, "%d %B %Y").date()

def scrape_bsgc_year(session, year):
    url = f'https://bs-gc.com/en/school-life/calendar/eventsbyyear/{year}/-?limit=all'
    print(f'[+] Fetching annual events from: {url}')

    events = []
    try:
        res = session.get(url, timeout=20)
        if res.status_code != 200:
            print(f'[-] HTTP Error {res.status_code} accessing year {year}')
            return events

        # Parse static HTML response
        html_content = res.content.decode('utf-8', errors='replace')
        #print(f'[+] html_content: {html_content}')
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find event links containing detailed repeat/day links
        links = soup.find_all("li", class_="ev_td_li")

        for link in links:
            # Extract the full text inside the list item
            text = link.get_text(separator="\n", strip=True)

            # 1. Extract Summary & UID / Link
            a_tag = link.find("a", class_="ev_link_row")
            summary = a_tag.get_text(strip=True) if a_tag else ""
            event_url = a_tag["href"] if a_tag and "href" in a_tag.attrs else ""

            # Extract event ID from link (e.g., /eventdetail/712/... -> 712)
            event_id_match = re.search(r"/eventdetail/(\d+)/", event_url)
            event_id = event_id_match.group(1) if event_id_match else ""

            # 2. Extract Category (located after '::')
            category = text.split("::")[-1].strip() if "::" in text else ""

            # 3. Extract Raw Date/Time Line (first line before the anchor or email)
            first_line = text.split("\n")[0].strip()

            # Clean off time components if present (e.g. "08:00am - 05:00pm")
            date_part = re.sub(
                r"\d{2}:\d{2}(?:am|pm)?\s*-\s*\d{2}:\d{2}(?:am|pm)?", "", first_line
            ).strip()

            # Remove weekday names (Saturday, Monday, etc.)
            date_part_no_days = re.sub(
                r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
                "",
                date_part,
            ).strip()

            # Parse Start and End Dates
            if "-" in date_part_no_days:
                # Multi-day event: e.g. "20 December 2025 - 07 January 2026"
                parts = date_part_no_days.split("-")
                start_date = parse_date_str(parts[0])
                end_date = parse_date_str(parts[1])
            else:
                # Single-day event: e.g. "08 January 2026"
                start_date = parse_date_str(date_part_no_days)
                end_date = start_date
                
            events.append(
                    {
                        "id": event_id,
                        "uid": f"bsgc-{event_id}@bs-gc.com" if event_id else "",
                        "summary": summary,
                        "start_date": start_date,
                        "end_date": end_date,
                        "category": category,
                        "url": event_url,
                    }
                )

            # --- Verification Output ---
            for ev in events[:5]:  # Print first 5 events
                print(ev)

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

        summary = item['summary']
        start_date = item['start_date']
        end_date = item['end_date']
        category = item['category']

        #print(f'[+] Item Summary: {summary}')
        
        # Filter out events outside the academic year
        if start_date < academic_start or start_date > academic_end:
            continue

        uid = item['uid'] or f'bsgc-{abs(hash(summary + str(start_date)))}@bs-gc.com'
        if uid in seen_uids:
            continue
        seen_uids.add(uid)

        # Select category emoji
        emoji = CATEGORY_EMOJIS.get(category, CATEGORY_EMOJIS['Default'])
        summary_str = f'{emoji} {summary}'

        event = Event()
        event.add('uid', uid)
        event.add('dtstamp', datetime.now(timezone.utc))
        event.add('summary', summary_str)
        event.add('dtstart', start_date)
        # RFC 5545 end date is exclusive for all-day events
        event.add('dtend', end_date + timedelta(days=1))

        if category:
            event.add('categories', [category])

        cal.add_component(event)
        total_events += 1

    output_filename = 'bsgc_calendar.ics'

    with open(output_filename, 'wb') as f:
        f.write(cal.to_ical())

    print(f"\n[✓] Finished: {total_events} events saved to '{output_filename}'.")


if __name__ == '__main__':
    generate_full_ics(2026)
