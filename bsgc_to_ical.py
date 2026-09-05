import json
import re
import urllib.parse
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
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
}

def clean_html(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()

def try_direct_ics():
    """
    Intenta descargar el feed de exportación iCal nativo del plugin de la web.
    """
    candidate_urls = [
        "https://bs-gc.com/es/vida-escolar/calendar-2/?ical=1",
        "https://bs-gc.com/?stec_export_ical=1",
        "https://bs-gc.com/wp-admin/admin-ajax.php?action=stec_export_ical",
        "https://bs-gc.com/events/?ical=1"
    ]
    
    for url in candidate_urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200 and "BEGIN:VCALENDAR" in res.text:
                print(f"[✓] Encontrado feed .ics nativo en: {url}")
                return res.content
        except Exception:
            pass
    return None

def fetch_events_via_ajax(session, year, month):
    """
    Consulta el endpoint interno de AJAX mandando la acción del plugin de calendario.
    """
    ajax_url = "https://bs-gc.com/wp-admin/admin-ajax.php"
    
    # Parámetros habituales para Stachethemes / EventOn / WP Calendar
    payloads = [
        {
            'action': 'stec_get_events',
            'start': f"{year}-{month:02d}-01",
            'end': f"{year}-{month:02d}-31"
        },
        {
            'action': 'evcal_ajax_init',
            'current_month': str(month),
            'current_year': str(year)
        }
    ]
    
    events = []
    for payload in payloads:
        try:
            res = session.post(ajax_url, data=payload, timeout=10)
            if res.status_code == 200:
                try:
                    data = res.json()
                    if isinstance(data, list):
                        events.extend(data)
                    elif isinstance(data, dict) and 'events' in data:
                        events.extend(data['events'])
                except Exception:
                    pass
        except Exception:
            pass
            
    return events

def build_calendar_from_scratch(start_year=2026):
    # 1. Probar descarga directa del .ics oficial
    direct_ics_data = try_direct_ics()
    if direct_ics_data:
        with open("bsgc_calendar.ics", "wb") as f:
            f.write(direct_ics_data)
        print("[✓] Descargado y guardado 'bsgc_calendar.ics' desde el feed nativo.")
        return

    # 2. Si no hay feed directo, raspar vía AJAX/HTML
    print("[+] Extrayendo eventos mes a mes desde el backend...")
    cal = Calendar()
    cal.add('prodid', '-//British School of Gran Canaria//School Calendar//ES')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'BSGC - Calendario Escolar')
    cal.add('x-wr-timezone', 'Atlantic/Canary')

    session = requests.Session()
    session.headers.update(HEADERS)

    # Cargar la página inicial para establecer cookies y sesión de WordPress
    try:
        init_res = session.get("https://bs-gc.com/es/vida-escolar/calendar-2", timeout=15)
        html_content = init_res.text
    except Exception as e:
        print(f"[-] Error cargando página principal: {e}")
        html_content = ""

    months = []
    for m in range(9, 13):
        months.append((start_year, m))
    for m in range(1, 9):
        months.append((start_year + 1, m))

    total_events = 0
    seen = set()

    # Extraer eventos incrustados en la carga inicial (JSON global en JavaScript)
    js_events_match = re.findall(r'var\s+stec_events\s*=\s*(\[.*?\]);', html_content, re.DOTALL)
    if not js_events_match:
        js_events_match = re.findall(r'["\']events["\']\s*:\s*(\[.*?\])', html_content, re.DOTALL)

    embedded_events = []
    for match in js_events_match:
        try:
            embedded_events.extend(json.loads(match))
        except Exception:
            pass

    # Si encontramos eventos en el JS embebido
    for ev in embedded_events:
        title = ev.get('title') or ev.get('summary')
        start_str = ev.get('start') or ev.get('start_date')
        if title and start_str:
            uid_key = f"{start_str[:10]}-{title}"
            if uid_key not in seen:
                seen.add(uid_key)
                
                event = Event()
                event.add('summary', f"📅 {clean_html(title)}")
                try:
                    dt = datetime.strptime(start_str[:10], '%Y-%m-%d')
                    event.add('dtstart', dt.date())
                    event.add('dtend', dt.date() + timedelta(days=1))
                except Exception:
                    continue
                
                event.add('uid', f"bsgc-{abs(hash(uid_key))}@bs-gc.com")
                cal.add_component(event)
                total_events += 1

    # Si el JS no tenía todo el año, consultar los meses vía AJAX
    for year, month in months:
        raw_events = fetch_events_via_ajax(session, year, month)
        for ev in raw_events:
            title = ev.get('title')
            start_str = ev.get('start')
            if title and start_str:
                uid_key = f"{start_str[:10]}-{title}"
                if uid_key not in seen:
                    seen.add(uid_key)
                    
                    event = Event()
                    event.add('summary', f"📅 {clean_html(title)}")
                    try:
                        dt = datetime.strptime(start_str[:10], '%Y-%m-%d')
                        event.add('dtstart', dt.date())
                        event.add('dtend', dt.date() + timedelta(days=1))
                    except Exception:
                        continue

                    event.add('uid', f"bsgc-{abs(hash(uid_key))}@bs-gc.com")
                    cal.add_component(event)
                    total_events += 1

    with open("bsgc_calendar.ics", "wb") as f:
        f.write(cal.to_ical())

    print(f"\n[✓] Proceso finalizado: {total_events} eventos guardados en 'bsgc_calendar.ics'.")

if __name__ == "__main__":
    build_calendar_from_scratch(2026)
