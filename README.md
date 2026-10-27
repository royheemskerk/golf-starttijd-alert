# golf-starttijd-alert

Kijkt elke ~5 minuten (GitHub Actions) of er bij Golfbaan Delfland een nieuwe starttijd vrijkomt
en stuurt dan een pushmelding via [ntfy](https://ntfy.sh).

- Bron: de IntoGolf-API achter https://www.delflandgolf.nl/reserveer-starttijd/reserveren-starttijd/
- Zoekt elke week automatisch de eerstvolgende zaterdag (na 13:45 op zaterdag schuift hij door naar de week erna)
- Instellingen (dag, tijdvenster, lussen, aantal spelers, of vaste `DATES`): `env` in `.github/workflows/check.yml`
- Secret `NTFY_TOPIC`: het ntfy-onderwerp waarop je in de app geabonneerd bent
- Handmatig starten: tab **Actions → starttijd-check → Run workflow**
- `keepalive.yml` maakt elke maand een kleine commit, zodat GitHub de geplande check niet uitzet na 60 dagen zonder activiteit.
