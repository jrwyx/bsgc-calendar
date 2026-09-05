import json
import re
import requests
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest'
}

def clean_html(text):
    if not text:
        return ""
    # Eliminar etiquetas HTML y espacios sobrantes
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()

def fetch_month_events(year, month):
    """
    Realiza la consulta AJAX que usa el calendario web para cargar cada mes dinámicamente.
    """
    url = f"https://bs-gc.com/es/vida-escolar/calendar-2/?ical=1&tribe_event_display=month&eventDate={year}-{month:02d}"
    
    events = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            # Si el endpoint devuelve formato JSON o HTML procesable
            content = res.text
            # Extraer títulos e información de eventos en el bloque devuelto
            matches = re.findall(r'class="[^"]*tribe-events-calendar-[^"]*"[\s\S]*?<a [^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', content)
            
            for href, raw_title in matches:
                title = clean_html(raw_title)
                if title and len(title) > 2:
                    events.append({
                        'title': title,
                        'url': href
                    })
    except Exception as e:
        print(f"[-] Error consultando {year}-{month:02d}: {e}")
        
    return events

def scrape_full_academic_year(start_year=2026):
    cal = Calendar()
    cal.add('prodid', '-//British School of Gran Canaria//School Calendar//ES')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'BSGC - Calendario Escolar')
    cal.add('x-wr-timezone', 'Atlantic/Canary')

    # Recorrer los 12 meses del curso académico (Sep 2026 - Ago 2027)
    months = []
    for m in range(9, 13):
        months.append((start_year, m))
    for m in range(1, 9):
        months.append((start_year + 1, m))

    total_events = 0
    seen = set()

    session = requests.Session()
    session.headers.update(HEADERS)

    for year, month in months:
        print(f"[+] Procesando mes: {year}-{month:02d}...")
        
        # Endpoint de consulta dinámico por fecha
        api_url = f"https://bs-gc.com/wp-admin/admin-ajax.php"
        payload = {
            'action': 'tribe_list',
            'eventDate': f"{year}-{month:02d}-01",
            'mode': 'month'
        }
        
        try:
            # Petición GET directa con el parámetro de fecha que fuerza el cambio de mes
            page_url = f"https://bs-gc.com/es/vida-escolar/calendar-2/{year}-{month:02d}/"
            res = session.get(page_url, timeout=15)
            
            if res.status_code != 200:
                # Fallback a la vista por defecto con parámetro de fecha
                page_url = f"https://bs-gc.com/es/vida-escolar/calendar-2/?eventDate={year}-{month:02d}"
                res = session.get(page_url, timeout=15)

            html = res.text
            
            # Buscar bloques de eventos en el HTML del mes solicitado
            # Extraer bloques con data-event-date o enlaces de eventos de la agenda
            event_matches = re.findall(r'<a\s+[^>]*class="[^"]*tribe-event-url[^"]*"[^>]*title="([^"]+)"[^>]*>', html)
            
            if not event_matches:
                # Búsqueda secundaria por patrón de enlace e innerText
                event_matches = re.findall(r'class="tribe-events-month-event-title[^"]*"[\s\S]*?<a[^>]*>([\s\S]*?)</a>', html)

            for raw_title in event_matches:
                title = clean_html(raw_title)
                if not title or len(title) < 2:
                    continue

                # Estimación de fecha dentro del mes correspondiente
                event_date = datetime(year, month, 1)
                uid_key = f"{year}{month:02d}-{title}"

                if uid_key in seen:
                    continue
                seen.add(uid_key)

                event = Event()
                emoji = CATEGORY_EMOJIS['Default']
                event.add('summary', f"{emoji} {title}")
                event.add('dtstart', event_date.date())
                event.add('dtend', event_date.date() + timedelta(days=1))
                event.add('uid', f"bsgc-{abs(hash(uid_key))}@bs-gc.com")

                cal.add_component(event)
                total_events += 1

        except Exception as e:
            print(f"[-] Error en {year}-{month:02d}: {e}")

    output_filename = "bsgc_calendar.ics"
    with open(output_filename, "wb") as f:
        f.write(cal.to_ical())

    print(f"\n[✓] Completado con éxito: {total_events} eventos guardados en '{output_filename}' para todo el curso escolar.")

if __name__ == "__main__":
    scrape_full_academic_year(2026)
