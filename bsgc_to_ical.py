import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from icalendar import Calendar, Event

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
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
}

def scrape_bsgc():
    cal = Calendar()
    cal.add('prodid', '-//British School of Gran Canaria//School Calendar//ES')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'BSGC - Calendario Escolar')
    cal.add('x-wr-timezone', 'Atlantic/Canary')

    collected_events = []
    
    # Recorrer los meses del curso académico (2026-2027)
    months = [
        (2026, 9), (2026, 10), (2026, 11), (2026, 12),
        (2027, 1), (2027, 2), (2027, 3), (2027, 4), (2027, 5), (2027, 6), (2027, 7), (2027, 8)
    ]

    session = requests.Session()
    session.headers.update(HEADERS)

    for year, month in months:
        url = f"https://bs-gc.com/es/vida-escolar/calendar-2?tribe-bar-date={year}-{month:02d}-01"
        print(f"[+] Consultando {year}-{month:02d}...")
        
        try:
            res = session.get(url, timeout=15)
            if res.status_code != 200:
                continue

            soup = BeautifulSoup(res.text, 'html.parser')

            # Buscar bloques de eventos en el calendario
            events_blocks = soup.find_all(class_=re.compile(r'(type-tribe_events|tribe-events-calendar|event)'))
            
            for block in events_blocks:
                title_elem = block.find(class_=re.compile(r'(title|summary|heading)')) or block.find(['h3', 'h4', 'a'])
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                if not title or len(title) < 3:
                    continue

                # Intentar localizar fecha en el bloque
                time_elem = block.find('time')
                date_str = time_elem.get('datetime') if time_elem and time_elem.has_attr('datetime') else None
                
                if date_str:
                    try:
                        ev_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                    except ValueError:
                        ev_date = datetime(year, month, 1)
                else:
                    ev_date = datetime(year, month, 1)

                collected_events.append({
                    'title': title,
                    'date': ev_date
                })

        except Exception as e:
            print(f"[-] Error obteniendo {year}-{month:02d}: {e}")

    # Generar iCal deduplicando
    seen = set()
    total_events = 0

    for item in collected_events:
        uid_key = f"{item['date'].strftime('%Y%m%d')}-{item['title']}"
        if uid_key in seen:
            continue
        seen.add(uid_key)

        event = Event()
        emoji = CATEGORY_EMOJIS['Default']
        event.add('summary', f"{emoji} {item['title']}")
        event.add('dtstart', item['date'].date())
        event.add('dtend', item['date'].date() + timedelta(days=1))
        event.add('uid', f"bsgc-{abs(hash(uid_key))}@bs-gc.com")

        cal.add_component(event)
        total_events += 1

    with open("bsgc_calendar.ics", "wb") as f:
        f.write(cal.to_ical())

    print(f"\n[✓] Completado: {total_events} eventos guardados en 'bsgc_calendar.ics'")

if __name__ == "__main__":
    scrape_bsgc()
