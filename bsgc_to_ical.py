import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from icalendar import Calendar, Event

# Mapeo de categorías con emojis para visualización clara en móviles
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

BASE_URL = "https://bs-gc.com/wp-admin/admin-ajax.php"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
}

def fetch_events_for_month(year, month):
    """
    Realiza la petición AJAX al backend de WordPress del colegio para un mes concreto.
    """
    data = {
        'action': 'tribe_calendar',
        'eventDate': f"{year}-{month:02d}",
        'mode': 'month'
    }
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(BASE_URL, data=encoded_data, headers=HEADERS)
    
    events = []
    try:
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            if 'events' in res_json:
                events = res_json['events']
    except Exception as e:
        print(f"[-] Error obteniendo eventos para {year}-{month:02d}: {e}")
    
    return events

def parse_and_build_ical(academic_start_year=2026):
    """
    Recorre los 12 meses del curso académico (Sep X - Ago X+1) y construye el .ics
    """
    cal = Calendar()
    cal.add('prodid', '-//British School of Gran Canaria//School Calendar//ES')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'BSGC - Calendario Escolar')
    cal.add('x-wr-timezone', 'Atlantic/Canary')

    months = []
    # De Septiembre del año inicial a Diciembre
    for m in range(9, 13):
        months.append((academic_start_year, m))
    # De Enero a Agosto del año siguiente
    for m in range(1, 9):
        months.append((academic_start_year + 1, m))

    total_events = 0

    for year, month in months:
        print(f"[+] Procesando {year}-{month:02d}...")
        raw_events = fetch_events_for_month(year, month)
        
        for ev in raw_events:
            event = Event()
            
            title = ev.get('title', 'Evento BSGC')
            start_str = ev.get('start_date')  # Formato 'YYYY-MM-DD HH:MM:SS'
            end_str = ev.get('end_date')
            category = ev.get('category', 'Default')
            description = ev.get('description', '')

            # Limpiar etiquetas HTML de la descripción si existen
            clean_desc = re.sub(r'<[^>]+>', '', description).strip()

            emoji = CATEGORY_EMOJIS.get(category, CATEGORY_EMOJIS['Default'])
            summary = f"{emoji} {title}"

            event.add('summary', summary)
            
            # Parsear fechas
            if start_str:
                dt_start = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                event.add('dtstart', dt_start.date() if '00:00:00' in start_str else dt_start)
            
            if end_str:
                dt_end = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')
                event.add('dtend', dt_end.date() if '00:00:00' in end_str else dt_end)

            if clean_desc:
                event.add('description', clean_desc)

            event.add('categories', [category])
            
            # UID determinista único basado en ID de evento o fecha/título para actualización limpia
            event_id = ev.get('eventId', f"{start_str}-{hash(title)}")
            event.add('uid', f"bsgc-event-{event_id}@bs-gc.com")

            cal.add_component(event)
            total_events += 1

    output_filename = "bsgc_calendar.ics"
    with open(output_filename, "wb") as f:
        f.write(cal.to_ical())
        
    print(f"\n[✓] Completado: {total_events} eventos guardados en '{output_filename}'")

if __name__ == "__main__":
    parse_and_build_ical(2026)
  
