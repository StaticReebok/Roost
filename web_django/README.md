# Roost — Django + HTMX Web App

The Roost app is **solely Django-based**. This is the only UI: server-rendered HTML with Django templates; CSS/JS are only for the frontend within Django (Tailwind CDN, HTMX). There is no separate JS/HTML/CSS website.

## Stack

- **Django 5** — server-side views, forms, templates
- **django-htmx** — partial updates and dynamic UI without a JS framework
- **Tailwind CSS** (CDN) — styling
- **Same SQLite DB** (`roost.db` in project root) — unmanaged Django models mirror existing tables
- **Reuses `core/`** — scoring, Victoria boundary (run from project root so `core` is on path)

## Setup

From the **project root** (parent of `web_django/`):

```bash
cd "Roost - Inspire hackathon"
pip install -r web_django/requirements.txt
```

Ensure the DB is seeded: `python -m db.seed`

## Run

From the **project root**:

```bash
cd web_django
python manage.py runserver 8501
```

Open **http://localhost:8501**

## Pages

- **/** — Home (CTA to onboarding / matches)
- **/onboarding/** — Create profile, see Ladder Snapshot
- **/matches/** — Browse match cards (HTMX load + Like/Pass)
- **/reality-check/** — Monthly cost and commute sanity check
- **/insights/** — Neighborhood table (CMHC data)

## Project structure

```
web_django/
├── manage.py
├── requirements.txt
├── README.md
├── roost_web/          # Django project
│   ├── settings.py     # DB path = ../roost.db, sys.path += project root
│   └── urls.py
└── roost_app/          # Django app
    ├── models.py       # Unmanaged Profile, Swipe, Match
    ├── views.py
    ├── forms.py
    ├── services.py     # Calls core scoring
    ├── urls.py
    └── templates/roost_app/
        ├── base.html
        ├── home.html
        ├── onboarding.html
        ├── onboarding_result.html
        ├── matches.html
        ├── reality_check.html
        ├── insights.html
        └── partials/
            ├── match_cards.html
            └── reality_check_result.html
```
