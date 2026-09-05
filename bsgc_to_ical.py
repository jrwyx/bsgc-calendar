import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
}

CATEGORY_EMOJIS = {
    'Holidays': '🌴',
    'Important Dates': '📌',
    'Exams': '📝',
    'Meetings': '👥',
    'School Events': '🎉',
    'Field Trips': '🚌',
    'Sports': '⚽',
    'Default': '📅'
}

MESES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def parse_year_events(session, year):
    # Endpoint por año de JEvents en BSGC
    url = f"https://bs-gc.com/es/vida-escolar/calendar-2/eventsbyyear/{year}/30"
    print(f"[+] Consultado vista anual: {url}")
    
    events_found = []
    try:
        res = session.get(url, timeout=20)
        if res.status_code != 200:
            print(f"[-] HTTP Error {res.status_code} al acceder a {url}")
            return events_found

        soup = BeautifulSoup(res.text, 'html.parser')
        
        # JEvents agrupa por elementos li o divs con enlaces de eventos o filas de día
        # Buscar enlaces a detalles de eventos (con /icalrepeat.detail/ o con clase ev_link_row)
        links = soup.find_all('a', href=re.compile(r'icalrepeat\.detail|eventsbyday|day\.listevents'))
        
        if not links:
            # Búsqueda secundaria por cualquier enlace dentro del contenedor del calendario
            container = soup.find('div', id='jevents_body') or soup
            links = container.find_all('a')

        for a in links:
            title = clean_text(a.get_text())
            href = a.get('href', '')
            
            # Filtrar enlaces vacíos o de navegación (Siguiente año, Mes, etc.)
            if not title or len(title) < 2 or 'eventsbyyear' in href or 'byyear' in href:
                continue

            # Buscar fecha asociada en el atributo href o en los elementos padres
            # Ejemplo de href: /es/vida-escolar/calendar-2/icalrepeat.detail/2026/10/12/...
            date_match = re.search(rf'/{year}/(\d{{1,2}})/(\d{{1,2}})', href)
            
            month, day = None, None
            if date_match:
                month = int(date_match.group(1))
                day = int(date_match.group(2))
            else:
                # Si no está en la URL, buscar en el texto contenedor (ej. "12 October 2026" o "Martes, 1 Septiembre 2026")
                parent_text = clean_text(a.parent.get_text()) if a.parent else ""
                match_text = re.search(r'(\d{1,2})\s+([a-zA-ZáéíóúÁÉÍÓÚ]+)\s+' + str(year), parent_text, re.IGNORECASE)
                if match_text:
                    day = int(match_text.group(1))
                    month_str = match_text.group(2).lower()
                    month = MESES.get(month_str)

            if month and day:
                try:
                    dt = datetime(year, month, day)
                    events_found.append({
                        'title': title,
                        'date': dt
                    })
                except ValueError:
                    pass

    except Exception as e:
        print(f"[-] Error en scraping del año {year}: {e}")

    return events_found

def build_academic_calendar(start_year=2026):
    cal = Calendar()
    cal.add('prodid', '-//British School of Gran Canaria//School Calendar//ES')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'BSGC - Calendario Escolar')
    cal.add('x-wr-timezone', 'Atlantic/Canary')

    session = requests.Session()
    session.headers.update(HEADERS)

    total_events = 0
    seen_uids = set()

    # Procesar tanto el año actual como el siguiente para cubrir el curso académico completo (2026 y 2027)
    for y in [start_year, start_year + 1]:
        year_events = parse_year_events(session, y)
        for item in year_events:
            title = item['title']
            event_date = item['date']

            # Solo procesar fechas dentro del rango del curso escolar (Sep 2026 - Ago 2027)
            if y == start_year and event_date.month < 9:
                continue
            if y == start_year + 1 and event_date.month >= 9:
                continue

            uid_key = f"{event_date.strftime('%Y-%m-%d')}-{title}"
            if uid_key in seen_uids:
                continue
            seen_uids.add(uid_key)

            event = Event()
            event.add('summary', f"{CATEGORY_EMOJIS['Default']} {title}")
            event.add('dtstart', event_date.date())
            event.add('dtend', event_date.date() + timedelta(days=1))
            event.add('uid', f"bsgc-{abs(hash(uid_key))}@bs-gc.com")

            cal.add_component(event)
            total_events += 1

    output_filename = "bsgc_calendar.ics"
    with open(output_filename, "wb") as f:
        f.write(cal.to_ical())

    print(f"\n[✓] Proceso completado: {total_events} eventos guardados en '{output_filename}'.")

if __name__ == "__main__":
    build_academic_calendar(2026)
