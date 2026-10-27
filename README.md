# golf-starttijd-alert

Kijkt elke ~5 minuten (GitHub Actions) of er bij Golfbaan Delfland een nieuwe starttijd vrijkomt
en stuurt dan een pushmelding via [ntfy](https://ntfy.sh).

- Bron: de IntoGolf-API achter https://www.delflandgolf.nl/reserveer-starttijd/reserveren-starttijd/
- Instellingen (datum, tijdvenster, lussen, aantal spelers): `env` in `.github/workflows/check.yml`
- Secret `NTFY_TOPIC`: het ntfy-onderwerp waarop je in de app geabonneerd bent
- Handmatig starten: tab **Actions → starttijd-check → Run workflow**
- Na de laatste gezochte datum zet de workflow zichzelf uit. Voor een nieuwe datum: pas `DATES` aan
  en zet de workflow weer aan via **Actions → starttijd-check → Enable workflow**.
