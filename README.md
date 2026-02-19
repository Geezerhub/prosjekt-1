# Oppskriftsapp med forholdstall (Windows-vennlig)

En enkel desktop-app i Python/Tkinter der du kan:

- Registrere oppskrifter med ingredienser, mengde, enhet og instruksjoner.
- Lagre oppskrifter lokalt i `recipes.json`.
- Velge en ingrediens som referanse og angi ny mengde.
- Få alle øvrige ingredienser automatisk skalert i samme forhold.

## Kjøring

```bash
python3 recipe_app.py
```

## Tester

```bash
python3 -m unittest discover -s tests
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
