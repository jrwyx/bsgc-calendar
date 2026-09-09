📅 <ins>**BSGC School Calendar ICS Feed**</ins>

An automated Python scraper that extracts school events from the British School of Gran Canaria (BSGC) **CALENDAR** [website](https://bs-gc.com/en/school-life/calendar).

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
- Every 5-6 hours via GitHub Actions cron.
- Applies a randomized delay (0 to 30 minutes) before requesting data to avoid predictable server hits.
- Commits and pushes changes to bsgc_calendar.ics only if new or updated events are found.


🔗 <ins>**HOW TO SUBSCRIBE**</ins>

To add this calendar to your calendar app:

**1. Apple Calendar / iOS 18+:**
- Open Calendar → tap Calendars (bottom of screen)
- Tap Add Calendar → Add Subscription Calendar.
- Paste the following URL link:
  - webcal://jrwyx.github.io/bsgc-calendar/bsgc_calendar.ics
- Tap Subscribe (or Find on iOS 26)
- Set a name, color, and choose iCloud as the account so it syncs across your Apple devices.
- Tap Add.
- **Quick shortcut:** Just tap the webcal:// link in Safari or Mail — iOS will automatically prompt you to add it to Calendar. 
  
**2. Google Calendar Desktop Website:**

- Open and log into your Google Calendar account in a web browser on a computer.
- On the left sidebar, under Other calendars, click the + icon and select From URL.
- Paste the link shown below and click 'Add calendar'.
  - webcal://jrwyx.github.io/bsgc-calendar/bsgc_calendar.ics
 
**3. Sync to Android:**

The  Google Calendar app for Android does not natively support directly subscribing to webcal:// links or adding calendar URLs from within the mobile interface.  To add a webcal feed to an Android device, you must subscribe via the Google Calendar desktop website first, then sync it to your phone, tablet, etc.
- Open the Google Calendar app on your Android device.
- Tap the Menu icon (three lines) and go to Settings.
- Find the newly added calendar in the list (you may need to tap Show more).
- Tap the calendar name and ensure the Sync toggle is turned On.
- The events will then populate on your phone.

Note on Google Calendar Sync:
- Google Calendar caches external .ics feeds aggressively and refreshes them every 12–24 hours :cry:

:wrench: <ins>**Workarounds for Faster Google Calendar Updates**</ins>
- Use an alternative calendar app:
    - Switch to apps like Apple Calendar or Microsoft Outlook, which support much more frequent or user-adjustable refresh intervals (ranging from 5 minutes to a few hours) for subscribed feeds.
- Using the open-sorce tool GAS-ICS-Sync on GitHub is the best programmatic way to bypass Google’s 12–24 hour caching rule.
    -  https://github.com/derekantrican/GAS-ICS-Sync
    -  Instead of treating the link as an external subscription feed, the script downloads the .ics file directly, parses the events, and injects them directly into your Google Calendar via the API.
    -  Because it creates native events, your calendar updates as frequently as you schedule the script to run.
   
