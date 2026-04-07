# Oppskriftsapp med forholdstall (Windows-vennlig)

En enkel desktop-app i Python der du kan:

- Registrere oppskrifter med ingredienser, mengde, enhet og instruksjoner.
- Lagre oppskrifter lokalt i `recipes.json`.
- Velge en ingrediens som referanse og angi ny mengde.
- Få alle ingredienser automatisk skalert i samme forhold.
- Definere enheter som ikke skal skaleres (f.eks. `knep`, `dæsj`).
- Velge path/mappe for oppskriftssamlingen (`recipes.json`).
- Åpne utskriftsdialog med valg av skriver og utskriftsinnstillinger.

## Kom i gang (for nybegynnere på Windows)

### 1) Installer Python

1. Gå til: https://www.python.org/downloads/
2. Last ned nyeste Python for Windows.
3. Under installasjon: huk av for **"Add Python to PATH"**.

### 2) Last ned prosjektet

Hvis du er på GitHub-siden til prosjektet:

1. Trykk den grønne **Code**-knappen.
2. Velg **Download ZIP**.
3. Pakk ut zip-filen til f.eks. `C:\oppskriftsapp`.

### 3) Åpne Terminal i prosjektmappen

1. Åpne mappen du pakket ut.
2. Klikk i adresselinjen i Filutforsker, skriv `cmd`, trykk Enter.
3. Nå åpnes ledetekst i riktig mappe.

### 4) Kjør appen

Skriv denne kommandoen og trykk Enter:

```bash
python recipe_app.py
```

Hvis `python` ikke virker, prøv:

```bash
py recipe_app.py
```
- Tips: Lag en "snarvei" på skrivebordet ditt til recipe_app_start, og du kan bruke det inkluderte kokkehatt-bildet som ikon. 

## Innstillinger

Trykk på **Innstillinger**-knappen (over **Skriv ut**) i høyre del av vinduet.

Her kan du:

1. Definere ikke-skalerbare enheter (kommaseparert).
2. Velge mappe/path for oppskriftssamlingen.
3. Lagre innstillingene.
4. Avslutte appen via **Avslutt What's Cookin'**.

## Redigere tidligere lagrede oppskrifter

1. Velg oppskriften i listen til høyre.
2. Klikk **Rediger valgt oppskrift**.
3. Nå fylles feltene på venstre side inn automatisk.
4. Endre navn, ingredienser eller instruksjoner.
5. Klikk **Oppdater oppskrift** for å lagre endringene.

## Utskrift

Når du har valgt eller skalert en oppskrift i appen:

- Klikk **Skriv ut** for å åpne utskriftsdialogen (med valg av skriver, sider, layout osv.).

## Vanlige problemer

- **"python is not recognized"**
  - Python er ikke installert riktig i PATH. Installer på nytt og huk av for **Add Python to PATH**.

- **Ingenting skjer når du dobbeltklikker filen**
  - Bruk kommandoene over i terminal i stedet for dobbeltklikk.

- **Appen krasjer ved oppstart pga. lagret datafil**
  - Appen viser advarsel ved ødelagt `recipes.json`. Du kan slette `recipes.json` i prosjektmappen og starte appen på nytt.

## Tester (valgfritt)

```bash
python -m unittest discover -s tests
```

