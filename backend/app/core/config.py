"""Application settings for ProcureGuard MVP."""
import os

# Swap to PostgreSQL by changing this URL (e.g. postgresql+psycopg://user:pass@host/db)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./procureguard.db")

# Uploads are stored on disk for the MVP; object storage interface can replace this.
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

# Scoring policy (PRD FR-11) — configurable rather than hard-coded.
SCORE_BANDS = {
    "low_max": 100,
    "low_min": 90,
    "medium_min": 75,
    "high_min": 50,
    # below high_min => critical
}

# Weight per requirement state when computing the weighted compliance score.
STATE_SCORES = {
    "VERIFIED": 100.0,
    "REVIEW": 50.0,
    "NON_COMPLIANT": 0.0,
    "UNVERIFIABLE": 40.0,  # uncertainty discount, but NOT treated as compliant
}

# Below this extraction confidence, flag for human review (PRD FR-02, FR-04).
LOW_CONFIDENCE_THRESHOLD = 0.75

# Where on-disk mock adapter fixtures live.
MOCK_DATA_DIR = os.getenv("MOCK_DATA_DIR", "./app/services/adapters/data")
