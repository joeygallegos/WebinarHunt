# Webinar Hunt
WebinarHunt is a lightweight tool for prioritizing which SANS webinars to watch instead of letting them pile up into an endless “I’ll get to that later” list. I created this because I am in a crunch to complete all my CEU by year end.

It pulls webinar data from the SANS archive, stores it locally, and gives you a simple dashboard to:
- Sort by duration (quick wins first)
- Flag items as watched or watch later
- Mark favorites
- Filter by CySA+ objectives to align with exam prep
- Focus on content that actually matters to your goals

## Features
- Local state.json storage (no database required)
- Duration-based sorting (1hr → 3hr+)
- Watched / Watch Later / Favorite flags
- CySA+ objective mapping from titles + descriptions
- Tailwind + Alpine UI for fast filtering
- Homelab-friendly Flask app


## Create and activate virtual environment
```python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Fetch webinar data and run the app
```python
python fetch.py
python app.py
OR
gunicorn -b 0.0.0.0:8411 'app:app'
```