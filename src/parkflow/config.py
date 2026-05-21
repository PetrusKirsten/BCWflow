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

# Conservative nominal operating-hours window used to avoid interpreting
# after-hours snapshots as true zero-minute queue pressure. Keep raw data, but
# filter queue-pressure charts to this window by default.
NOMINAL_OPEN_HOUR = 10
NOMINAL_CLOSE_HOUR = 20

# Attraction names that should usually be excluded from queue-pressure charts.
# They remain in the dataset and in Data Coverage, but they are not treated as
# regular queue-time attractions by default because they are shows, photo spots,
# walkthroughs, scheduled experiences or non-ride operational records.
QUEUE_ANALYSIS_EXCLUDED_ATTRACTIONS = frozenset(
    {
        "Excalibur",
        "Hot Wheels Epic Show",
        "Madagascar Circus Show",
        "O Sonho do Cowboy!",
        "No Ritmo de Trolls",
        "Fotos com Trolls",
        "Fotos com a Turma do Madagascar",
        "Fotos com Betinho e Lully",
        "Esculturas Romero Britto",
        "Casa do Projeto Tamar",
    }
)

# Keyword fallback used when a new attraction appears and is clearly not a
# normal queue-time ride. Keep this conservative to avoid excluding valid rides.
QUEUE_ANALYSIS_EXCLUDED_KEYWORDS = (
    "show",
    "espetaculo",
    "espetáculo",
    "apresentacao",
    "apresentação",
    "fotos",
    "foto",
    "escultura",
    "teatro",
    "circo",
    "circus",
)

