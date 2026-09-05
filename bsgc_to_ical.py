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

MESES_ES = {
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

def scrape_year_view(session, year):
    url = f"https://bs-gc.com/es/vida-escolar/calendar-2/eventsbyyear/{year}/-"
    print(f"[+] Consultando vista anual: {url}")
    
    events = []
    try:
        res = session.get(url, timeout=25)
        if res.status_code != 200:
            print(f"[-] Error HTTP {res.status_code} al consultar el año {year}")
            return events

        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Extraer todos los enlaces de eventos dentro de la vista anual
        # JEvents coloca los eventos en etiquetas <a> con href hacia detalles o dias
        links = soup.find_all('a', href=re.compile(r'icalrepeat\.detail|eventsbyday|day\.listevents'))

        for link in links:
            title = clean_text(link.get_text())
            href = link.get('href', '')

            if not title or len(title) < 2:
                continue

            # Extraer la fecha desde la URL (ej: /2026/09/15/ o /2026/10/01/)
            date_match = re.search(rf'/{year}/(\d{{1,2}})/(\d{{1,2}})', href)
            
            event_date = None
            if date_match:
                m = int(date_match.group(1))
                d = int(date_match.group(2))
                try:
                    event_date = datetime(year, m, d)
                except ValueError:
                    pass

            # Si no está en la URL, extraer del contexto textual padre (ej: "15 Septiembre 2026")
            if not event_date:
                parent_text = clean_text(link.parent.get_text()) if link.parent else ""
                text_match = re.search(r'(\d{1,2})\s+([a-zA-ZáéíóúÁÉÍÓÚ]+)\s+' + str(year), parent_text, re.IGNORECASE)
                if text_match:
                    d = int(text_match.group(1))
                    m_str = text_match.group(2).lower()
                    m = MESES_ES.get(m_str)
                    if m:
                        try:
                            event_date = datetime(year, m, d)
                        except ValueError:
                            pass

            if event_date:
                events.append({
                    'title': title,
                    'date': event_date
                })

    except Exception as e:
        print(f"[-] Error en el scraping del año {year}: {e}")

    return events

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

    # Recorrer los dos años del curso académico (2026 y 2027)
    for y in [start_year, start_year + 1]:
        year_events = scrape_year_view(session, y)
        
        for item in year_events:
            title = item['title']
            event_date = item['date']

            # Filtrar por rango escolar (Septiembre 2026 a Agosto 2027)
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
