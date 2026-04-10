# Audio Analysis Backend

A FastAPI backend for analyzing, tagging, and cataloging audio files using PostgreSQL.

This project was built to process a large library of instrumentals, extract useful metadata, and make the catalog searchable through API endpoints and a marketplace-style interface.

## Features

- Analyze audio files and extract metadata such as BPM, key, and energy
- Store structured beat data in PostgreSQL
- Tag beats by mood, artist reference, and sync target
- Search and filter beats through backend routes
- Import and catalog large audio libraries with a dedicated script
- Serve a marketplace-style frontend using FastAPI templates

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Jinja2
- HTML/CSS
- JavaScript

## Project Structure

```bash
audio-analysis-backend/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   │   └── beats.py
│   └── services/
│       └── audio_analysis.py
├── scripts/
│   └── analyze_and_import_beats.py
├── static/
├── templates/
├── uploads/
├── requirements.txt
└── .env.example