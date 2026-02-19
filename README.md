# Oppskriftsapp med forholdstall (Windows-vennlig)

En enkel desktop-app i Python/Tkinter der du kan:

- Registrere oppskrifter med ingredienser, mengde, enhet og instruksjoner.
- Lagre oppskrifter lokalt i `recipes.json`.
- Velge en ingrediens som referanse og angi ny mengde.
- Få alle øvrige ingredienser automatisk skalert i samme forhold.
- Eksportere oppskrift som `.txt` eller `.pdf`.
- Skrive ut oppskrift direkte i Windows.

## Kom i gang (for nybegynnere på Windows)

Du trenger **ikke** kunne Git eller GitHub for å kjøre appen.

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

## Redigere tidligere lagrede oppskrifter

1. Velg oppskriften i listen til høyre.
2. Klikk **Rediger valgt oppskrift**.
3. Nå fylles feltene på venstre side inn automatisk.
4. Endre navn, ingredienser eller instruksjoner.
5. Klikk **Oppdater oppskrift** for å lagre endringene.

## Utskrift og deling

Når du har valgt eller skalert en oppskrift i appen:

- Klikk **Lagre som .txt** for å dele som tekstfil.
- Klikk **Lagre som .pdf** for å dele som PDF.
- Klikk **Skriv ut** for å sende til standardskriver i Windows.

## Desktop-ikon på Windows

For å lage et ikon på skrivebordet:

1. Åpne prosjektmappen.
2. Dobbeltklikk `create_desktop_icon.bat`.
3. Du får en snarvei på skrivebordet som heter **Oppskriftsapp**.

## Vanlige problemer

- **"python is not recognized"**
  - Python er ikke installert riktig i PATH. Installer på nytt og huk av for **Add Python to PATH**.

- **Ingenting skjer når du dobbeltklikker filen**
  - Bruk kommandoene over i terminal i stedet for dobbeltklikk.

## Tester (valgfritt)

Hvis du vil sjekke at beregningslogikken virker:

```bash
python -m unittest discover -s tests
```

## Eksempel på bruk

Hvis en oppskrift er lagret med:

- Mel: 500 g
- Vann: 300 ml
- Salt: 10 g

...og du setter mel til 750 g ved anvendelse, blir resten:

- Vann: 450 ml
- Salt: 15 g

Dette gjør det enkelt å skalere opp/ned oppskrifter uten å regne manuelt.
