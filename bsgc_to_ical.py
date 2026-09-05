import asyncio
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from playwright.async_api import async_playwright

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

async def scrape_bsgc_calendar():
    cal = Calendar()
    cal.add('prodid', '-//British School of Gran Canaria//School Calendar//ES')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'BSGC - Calendario Escolar')
    cal.add('x-wr-timezone', 'Atlantic/Canary')

    collected_events = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("[+] Cargando la web del BSGC...")
        await page.goto("https://bs-gc.com/es/vida-escolar/calendar-2", wait_until="networkidle", timeout=60000)
        
        # Esperar a que el contenedor principal del calendario esté en pantalla
        await page.wait_for_selector("body", timeout=10000)

        # Capturar el HTML renderizado
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')

        # Buscar celdas, filas o tarjetas de eventos renderizadas por el widget
        # Extraer elementos de eventos por texto/patrones de fecha
        text_lines = [line.strip() for line in soup.get_text().split('\n') if line.strip()]
        
        current_year = 2026
        current_month = 9

        for i, line in enumerate(text_lines):
            # Detectar mención de días y eventos asociados
            match_date = re.search(r'(\d{1,2})\s+(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre|January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', line, re.IGNORECASE)
            
            if match_date:
                day = int(match_date.group(1))
                month_name = match_date.group(2).lower()
                year = int(match_date.group(3))
                month = MESES.get(month_name, 9)
                
                # Obtener el título del evento asociado (líneas siguientes)
                event_title = ""
                if i + 1 < len(text_lines):
                    next_line = text_lines[i+1]
                    if not re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}', next_line) and len(next_line) > 2:
                        event_title = next_line

                if event_title:
                    collected_events.append({
                        'date': datetime(year, month, day),
                        'title': event_title,
                        'category': 'Default'
                    })

        await browser.close()

    total_events = 0
    seen = set()

    for item in collected_events:
        uid_key = f"{item['date'].strftime('%Y%m%d')}-{item['title']}"
        if uid_key in seen:
            continue
        seen.add(uid_key)

        event = Event()
        emoji = CATEGORY_EMOJIS.get(item['category'], CATEGORY_EMOJIS['Default'])
        event.add('summary', f"{emoji} {item['title']}")
        event.add('dtstart', item['date'].date())
        event.add('dtend', item['date'].date() + timedelta(days=1))
        event.add('uid', f"bsgc-{hash(uid_key)}@bs-gc.com")

        cal.add_component(event)
        total_events += 1

    with open("bsgc_calendar.ics", "wb") as f:
        f.write(cal.to_ical())

    print(f"\n[✓] Extracción completada: {total_events} eventos guardados en 'bsgc_calendar.ics'")

if __name__ == "__main__":
    asyncio.run(scrape_bsgc_calendar())
