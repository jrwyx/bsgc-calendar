📅 <ins>**BSGC School Calendar ICS Feed**</ins>

An automated Python scraper that extracts school events from the British School of Gran Canaria (BSGC) **CALENDAR** [website.](https://bs-gc.com/en/school-life/calendar)
It generates an RFC 5545-compliant `.ics` calendar feed, and publishes it via GitHub Pages for easy subscription in Google Calendar, Apple Calendar, and Outlook.

<ins>**DISCLAIMER**</ins>
- No Guarantee of Stability: This project is experimental and APIs are not considered stable.
- Educational Use: This software is provided for educational or demonstration purposes only.
- No Support: The author provides no warranty or support for this code.
- Read the file [LICENSE.txt](https://github.com/jrwyx/bsgc-calendar/edit/main/LICENSE.txt)

✨ <ins>**FEATURES**</ins>

- **Emoji Categorization:** Prefixes event summaries with intuitive emojis based on event types (e.g., 🌴 Festivos, 📝 Exámenes, 🚌 Excursiones).
- **Time Transparency:** Configured with `TRANSP:TRANSPARENT` so all-day events do not block off user availability as "Busy".
- **RFC 5545 Compliant:**
  - Correct plural `CATEGORIES` property handling.
  - Formatted `ORGANIZER` properties using `vCalAddress` mailto URIs.
  - Dynamic `URL` properties pointing directly to event details on the school site.
- **Hidden Email Parsing:** Automatically decodes Joomla's obfuscated `<joomla-hidden-mail>` tags to extract contact emails.
- **Cross-Platform Compatibility:** Embeds full links and details in the `DESCRIPTION` field to ensure visibility in Google Calendar (which often ignores raw URL tags).
- **Automated Updates:** Powered by GitHub Actions to scrape and refresh the feed every 5-6 hours, with a randomized execution delay.


⚙️ <ins>**HOW AUTOMATION WORKS**</ins>

The workflow (.github/workflows/update_calendar.yml) executes automatically:
- Every 6 hours via GitHub Actions cron.
- Applies a randomized delay (0 to 30 minutes) before requesting data to avoid predictable server hits.
- Commits and pushes changes to bsgc_calendar.ics only if new or updated events are found.


🔗 <ins>**HOW TO SUBSCRIBE**</ins>

To add this calendar to your calendar app:

1. Copy the raw `.ics` URL link from GitHub Pages:   
    - http://jrwyx.github.io/bsgc-calendar/bsgc_calendar.ics

2. Apple Calendar / iOS:
- Go to Settings -> Calendar -> Accounts -> Add Account -> Other -> Add Subscribed Calendar.
- Paste the link copied in step 1, above (you can change https:// to webcal:// if prompted).

3. Google Calendar:
- Go to Other calendars (+) -> From URL.
- Paste the link shown below and click 'Add calendar'
  - webcal://jrwyx.github.io/bsgc-calendar/bsgc_calendar.ics

Note on Google Calendar Sync:
- Google Calendar caches external .ics feeds aggressively and refreshes them every 12–24 hours :cry:

:wrench: <ins>**Workarounds for Faster Google Calendar Updates**</ins>
- Use an alternative calendar app:
    - Switch to apps like Apple Calendar or Microsoft Outlook, which support much more frequent or user-adjustable refresh intervals (ranging from 5 minutes to a few hours) for subscribed feeds.
- Using the open-source tool GAS-ICS-Sync on GitHub is the best programmatic way to bypass Google’s 12–24 hour caching rule.
    -  https://github.com/derekantrican/GAS-ICS-Sync
    -  Instead of treating the link as an external subscription feed, the script downloads the .ics file directly, parses the events, and injects them directly into your Google Calendar via the API.
    -  Because it creates native events, your calendar updates as frequently as you schedule the script to run.
   
