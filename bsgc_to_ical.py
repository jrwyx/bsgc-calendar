import re
import urllib.parse
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
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


def scrape_bsgc_calendar(start_year=2026):
    cal = Calendar()
    cal.add('prodid', '-//British School of Gran Canaria//School Calendar//ES')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'BSGC - Calendario Escolar')
    cal.add('x-wr-timezone', 'Atlantic/Canary')

    session = requests.Session()
    session.headers.update(HEADERS)

    # 12 meses del curso académico (Sep 2026 - Ago 2027)
    months = []
    for m in range(9, 13):
        months.append((start_year, m))
    for m in range(1, 9):
        months.append((start_year + 1, m))

    total_events = 0
    seen_uids = set()

    for year, month in months:
        # URL oficial del componente JEvents del BSGC
        url = f'https://bs-gc.com/es/vida-escolar/calendar-2/monthcalendar/{year}/{month}/-'
        print(f'[+] Consultando: {year}-{month:02d} -> {url}')

        try:
            res = session.get(url, timeout=15)
            if res.status_code != 200:
                print(
                    f'[-] Error HTTP {res.status_code} al acceder a {year}-{month:02d}'
                )
                continue

            soup = BeautifulSoup(res.text, 'html.parser')

            # Buscar celdas o filas de días en el calendario
            # En JEvents los eventos suelen cargarse en enlaces 'ev_link_row' o con clase 'mod_events_latest_content'
            event_elements = soup.find_all('a', class_=re.compile(r'ev_link_row|glink|mod_events_latest_content'))

            # Fallback: si la clase específica cambia, buscar enlaces que apunten a /icalrepeat.detail/ o /day.listevents/
            if not event_elements:
                event_elements = soup.find_all(
                    'a',
                    href=re.compile(
                        r'icalrepeat\.detail|day\.listevents|ev_id'
                    ),
                )

            month_events = 0

            for elem in event_elements:
                title = clean_text(elem.get_text())
                if not title or len(title) < 2:
                    continue

                # Extraer la fecha desde el atributo o el contexto de la celda padre
                day = None
                parent_td = elem.find_parent(['td', 'div', 'li'])

                # Intentar deducir el día del mes analizando el contenido o cabecera
                if parent_td:
                    day_match = re.search(
                        r'\b([1-9]|[12][0-9]|3[01])\b', parent_td.get_text()
                    )
                    if day_match:
                        day = int(day_match.group(1))

                if not day:
                    # Intento secundario: buscar en el atributo href (ej: /2026/09/15/)
                    href = elem.get('href', '')
                    href_date_match = re.search(
                        rf'/{year}/{month:02d}/(\d{{1,2}})', href
                    )
                    if href_date_match:
                        day = int(href_date_match.group(1))

                if not day:
                    day = 1  # Asignar por defecto al día 1 del mes si no se puede precisar

                try:
                    event_date = datetime(year, month, day)
                except ValueError:
                    event_date = datetime(year, month, 1)

                uid_key = f'{year}-{month:02d}-{day}-{title}'
                if uid_key in seen_uids:
                    continue
                seen_uids.add(uid_key)

                event = Event()
                event.add('summary', f'{CATEGORY_EMOJIS["Default"]} {title}')
                event.add('dtstart', event_date.date())
                event.add('dtend', event_date.date() + timedelta(days=1))
                event.add('uid', f'bsgc-{abs(hash(uid_key))}@bs-gc.com')

                cal.add_component(event)
                month_events += 1
                total_events += 1

            print(f'    -> {month_events} eventos encontrados.')

        except Exception as e:
            print(f'[-] Excepción procesando {year}-{month:02d}: {e}')

    output_filename = 'bsgc_calendar.ics'
    with open(output_filename, 'wb') as f:
        f.write(cal.to_ical())

    print(
        f"\n[✓] Proceso completado: {total_events} eventos guardados en '{output_filename}'."
    )


if __name__ == '__main__':
    scrape_bsgc_calendar(2026)
