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


def fix_encoding(text):
  """Fixes double-encoded UTF-8 (mojibake) strings."""
  if not text:
    return ''
  try:
    # Re-encode latin1 misinterpretations back to raw bytes and decode properly as UTF-8
    return text.encode('latin1').decode('utf-8')
  except (UnicodeEncodeError, UnicodeDecodeError):
    return text


def clean_text(text):
  if not text:
    return ''
  text = fix_encoding(text)
  return re.sub(r'\s+', ' ', text).strip()


def scrape_bsgc_month(session, year, month):
  url = f'https://bs-gc.com/es/vida-escolar/calendar-2/monthcalendar/{year}/{month}/-'
  print(f'[+] Extrayendo eventos de: {year}-{month:02d} -> {url}')

  events = []
  try:
    res = session.get(url, timeout=20)
    if res.status_code != 200:
      print(f'[-] Error HTTP {res.status_code} al acceder a {year}-{month:02d}')
      return events

    # Parse using raw bytes and force utf-8 decoding in BeautifulSoup
    soup = BeautifulSoup(res.content, 'html.parser', from_encoding='utf-8')

    # Buscar celdas de días o contenedores de eventos de JEvents
    cells = soup.find_all(
        ['td', 'div'],
        class_=re.compile(
            r'mod_events_latest_content|cal_day|ev_td|jev_day|mday', re.I
        ),
    )
    if not cells:
      cells = soup.find_all('td')

    for cell in cells:
      links = cell.find_all(
          'a',
          href=re.compile(
              r'icalrepeat\.detail|eventsbyday|day\.listevents|cat.listevents'
          ),
      )

      for link in links:
        title = clean_text(link.get_text())
        href = link.get('href', '')

        if (
            not title
            or len(title) < 2
            or 'monthcalendar' in href
            or 'eventsbyyear' in href
        ):
          continue

        day = None
        date_match = re.search(rf'/{year}/{month:02d}/(\d{{1,2}})', href)
        if date_match:
          day = int(date_match.group(1))

        if not day:
          day_elem = cell.find(
              ['a', 'span', 'div'], class_=re.compile(r'day|date', re.I)
          )
          if day_elem:
            d_match = re.search(r'\b([1-9]|[12][0-9]|3[01])\b', day_elem.text)
            if d_match:
              day = int(d_match.group(1))

        if not day:
          cell_text = clean_text(cell.text)
          d_match = re.search(r'\b([1-9]|[12][0-9]|3[01])\b', cell_text)
          if d_match:
            day = int(d_match.group(1))

        if day:
          try:
            event_date = datetime(year, month, day)
            events.append({'title': title, 'date': event_date})
          except ValueError:
            pass

  except Exception as e:
    print(f'[-] Excepción consultando {year}-{month:02d}: {e}')

  return events


def generate_full_ics(start_year=2026):
  cal = Calendar()
  cal.add('prodid', '-//British School of Gran Canaria//School Calendar//ES')
  cal.add('version', '2.0')
  cal.add('x-wr-calname', 'BSGC - Calendario Escolar')
  cal.add('x-wr-timezone', 'Atlantic/Canary')

  session = requests.Session()
  session.headers.update(HEADERS)

  months = []
  for m in range(9, 13):
    months.append((start_year, m))
  for m in range(1, 9):
    months.append((start_year + 1, m))

  total_events = 0
  seen_uids = set()

  for year, month in months:
    month_events = scrape_bsgc_month(session, year, month)

    for item in month_events:
      title = item['title']
      event_date = item['date']

      uid_key = f"{event_date.strftime('%Y-%m-%d')}-{title}"
      if uid_key in seen_uids:
        continue
      seen_uids.add(uid_key)

      event = Event()
      # Construct clean text string
      summary_text = f"{CATEGORY_EMOJIS['Default']} {title}"
      event.add('summary', summary_text)
      event.add('dtstart', event_date.date())
      event.add('dtend', event_date.date() + timedelta(days=1))
      event.add('uid', f'bsgc-{abs(hash(uid_key))}@bs-gc.com')

      cal.add_component(event)
      total_events += 1

  output_filename = 'bsgc_calendar.ics'

  # Generate ics bytes and write directly without further string conversions
  ics_bytes = cal.to_ical()

  with open(output_filename, 'wb') as f:
    f.write(ics_bytes)

  print(
      f"\n[✓] Proceso completado: {total_events} eventos guardados en"
      f" '{output_filename}'."
  )


if __name__ == '__main__':
  generate_full_ics(2026)
