import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from icalendar import Calendar, Event

# Mapeo de categorías con emojis
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
    'Accept': 'application/json, text/plain, */*'
}

def get_events_from_wp_api(year, month):
    """
    Consulta la API REST oficial de Tribe Events / WordPress en bs-gc.com
    """
    # Rango del mes entero
    start_date = f"{year}-{month:02d}-01 00:00:00"
    if month == 12:
        end_date = f"{year+1}-01-01 00:00:00"
    else:
        end_date = f"{year}-{month+1:02d}-01 00:00:00"

    params = {
        'start_date': start_date,
        'end_date': end_date,
        'per_page': 100
    }
    
    url = f"https://bs-gc.com/wp-json/tribe/events/v1/events?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    
    events_list = []
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if 'events' in res_data:
                events_list = res_data['events']
    except Exception as e:
        print(f"[-] Error en API para {year}-{month:02d}: {e}")
        
    return events_list

def clean_html(text):
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text).strip()

def parse_and_build_ical(academic_start_year=2026):
    cal = Calendar()
    cal.add('prodid', '-//British School of Gran Canaria//School Calendar//ES')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'BSGC - Calendario Escolar')
    cal.add('x-wr-timezone', 'Atlantic/Canary')

    months = []
    # Curso académico: Sep (X) - Ago (X+1)
    for m in range(9, 13):
        months.append((academic_start_year, m))
    for m in range(1, 9):
        months.append((academic_start_year + 1, m))

    total_events = 0
    seen_uids = set()

    for year, month in months:
        print(f"[+] Consultando {year}-{month:02d}...")
        events = get_events_from_wp_api(year, month)
        
        for ev in events:
            ev_id = ev.get('id')
            uid = f"bsgc-event-{ev_id}@bs-gc.com"
            
            if uid in seen_uids:
                continue
            seen_uids.add(uid)

            event = Event()
            
            title = ev.get('title', 'Evento BSGC')
            start_str = ev.get('start_date')  # Formato: 'YYYY-MM-DD HH:MM:SS'
            end_str = ev.get('end_date')
            
            # Obtener categoría si existe
            categories = ev.get('categories', [])
            cat_name = categories[0].get('name') if categories else 'Default'
            
            emoji = CATEGORY_EMOJIS.get(cat_name, CATEGORY_EMOJIS['Default'])
            summary = f"{emoji} {clean_html(title)}"

            event.add('summary', summary)
            
            # Formatear fechas de inicio y fin
            if start_str:
                dt_start = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                # Si el evento dura todo el día o no tiene hora concreta
                if ev.get('all_day', False) or '00:00:00' in start_str:
                    event.add('dtstart', dt_start.date())
                else:
                    event.add('dtstart', dt_start)

            if end_str:
                dt_end = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')
                if ev.get('all_day', False) or '00:00:00' in end_str:
                    # iCal exige que los eventos de día completo terminen al día siguiente
                    event.add('dtend', dt_end.date() + timedelta(days=1))
                else:
                    event.add('dtend', dt_end)

            description = clean_html(ev.get('description', ''))
            if description:
                event.add('description', description)

            event.add('categories', [cat_name])
            event.add('uid', uid)

            cal.add_component(event)
            total_events += 1

    output_filename = "bsgc_calendar.ics"
    with open(output_filename, "wb") as f:
        f.write(cal.to_ical())
        
    print(f"\n[✓] Éxito: {total_events} eventos extraídos e insertados en '{output_filename}'")

if __name__ == "__main__":
    parse_and_build_ical(2026)
