# Oppskriftsapp med forholdstall (Windows-vennlig)

En enkel desktop-app i Python/Tkinter der du kan:

- Registrere oppskrifter med ingredienser, mengde, enhet og instruksjoner.
- Lagre oppskrifter lokalt i `recipes.json`.
- Velge en ingrediens som referanse og angi ny mengde.
- Få alle øvrige ingredienser automatisk skalert i samme forhold.
- Enheter som **knep** og **dæsj** skaleres ikke automatisk når oppskriften justeres.
- Skrive ut oppskrift direkte i Windows.
- Egen modul **Innstillinger** i programvinduet.
- Definere enheter som ikke skal skaleres og mappe for lagrede oppskrifter.

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

## Innstillinger (i programvinduet)

Klikk **Innstillinger**-knappen i høyre del av appen for å åpne innstillingsvinduet. Der kan du:

1. Definere enheter som ikke skal skaleres (kommaseparert, f.eks. `knep, dæsj`).
2. Velge mappe (path) der `recipes.json` lagres.
3. Trykke **Lagre innstillinger** for å aktivere endringene.

## Redigere tidligere lagrede oppskrifter

- Tips: Etter "Legg til ingrediens" (eller Enter/Numpad-Enter i ingrediensfeltene) hopper markøren tilbake til **Ingrediens** og feltet markeres, slik at du kan skrive direkte.
- Feltet **Enhet** beholdes mellom ingredienser og markeres automatisk når feltet får fokus, så du enkelt kan overskrive.
- I appen fungerer **Enter** som klikk for knappen som har fokus (unntatt i fritekstfeltet for instruksjoner).

1. Velg oppskriften i listen til høyre.
2. Klikk **Rediger valgt oppskrift**.
3. Nå fylles feltene på venstre side inn automatisk.
4. Endre navn, ingredienser eller instruksjoner.
5. Klikk **Oppdater oppskrift** for å lagre endringene.

## Utskrift

Når du har valgt eller skalert en oppskrift i appen:

- Klikk **Skriv ut** for å åpne Windows sitt utskriftsvindu (som i nettleser) for aktuell oppskrift, velg skriver og trykk **Skriv ut**.

## Vanlige problemer

- **"python is not recognized"**
  - Python er ikke installert riktig i PATH. Installer på nytt og huk av for **Add Python to PATH**.

- **Ingenting skjer når du dobbeltklikker filen**
  - Bruk kommandoene over i terminal i stedet for dobbeltklikk.

- **Appen krasjer ved oppstart pga. lagret datafil**
  - Ny versjon tåler ødelagt `recipes.json` bedre og viser advarsel. Du kan også slette `recipes.json` i prosjektmappen og starte appen på nytt.

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
