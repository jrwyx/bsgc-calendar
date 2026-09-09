# 📅 BSGC School Calendar ICS Feed

An automated Python scraper that extracts school events from the British School of Gran Canaria (BSGC) website. 
It generates an RFC 5545-compliant `.ics` calendar feed, and publishes it via GitHub Pages for easy subscription in Google Calendar, Apple Calendar, and Outlook.

---

✨ FEATURES

- **Emoji Categorization:** Prefixes event summaries with intuitive emojis based on event types (e.g., 🌴 Festivos, 📝 Exámenes, 🚌 Excursiones).
- **Time Transparency:** Configured with `TRANSP:TRANSPARENT` so all-day events do not block off user availability as "Busy".
- **RFC 5545 Compliant:**
  - Correct plural `CATEGORIES` property handling.
  - Formatted `ORGANIZER` properties using `vCalAddress` mailto URIs.
  - Dynamic `URL` properties pointing directly to event details on the school site.
- **Hidden Email Parsing:** Automatically decodes Joomla's obfuscated `<joomla-hidden-mail>` tags to extract contact emails.
- **Cross-Platform Compatibility:** Embeds full links and details in the `DESCRIPTION` field to ensure visibility in Google Calendar (which often ignores raw URL tags).
- **Automated Updates:** Powered by GitHub Actions to scrape and refresh the feed every 6 hours with a randomized execution delay.


⚙️ HOW AUTOMATION WORKS

The workflow (.github/workflows/update_calendar.yml) executes automatically:

    - Every 6 hours via GitHub Actions cron.
    - Applies a randomized delay (0 to 30 minutes) before requesting data to avoid predictable server hits.
    - Commits and pushes changes to bsgc_calendar.ics only if new or updated events are found.

---

🔗 HOW TO SUBSCRIBE

To add this calendar to your calendar app:

1. Copy the raw `.ics` URL from GitHub Pages:   
    http://jrwyx.github.io/bsgc-calendar/bsgc_calendar.ics

2. Apple Calendar / iOS:
    Go to Settings -> Calendar -> Accounts -> Add Account -> Other -> Add Subscribed Calendar.
    Paste the link (you can change https:// to webcal:// if prompted).

3. Google Calendar:
    Go to Other calendars (+) -> From URL.
    Paste the link above and click Add calendar (webcal://jrwyx.github.io/bsgc-calendar/bsgc_calendar.ics).

    Note on Google Calendar Sync: Google Calendar caches external .ics feeds aggressively and refreshes them every 12–24 hours.
   
