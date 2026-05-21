from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

PARK_ID = 319
PARK_NAME = "Beto Carrero World"
PARK_TIMEZONE = "America/Sao_Paulo"

# Approximate coordinates for Penha/SC region. Adjust later if you want exact park coordinates.
PARK_LATITUDE = -26.8016
PARK_LONGITUDE = -48.6264

QUEUE_TIMES_BASE_URL = "https://queue-times.com"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
