"""Configuration values for the My FootDr archive scraper."""

# Default Wayback snapshot of the "Our Clinics" landing page.
DEFAULT_BASE_URL = (
    "https://web.archive.org/web/20250708180027/"
    "https://www.myfootdr.com.au/our-clinics/"
)

# HTTP client defaults.
DEFAULT_USER_AGENT = "myfootdr-archive-scraper/0.1 " "(https://www.myfootdr.com.au/)"
DEFAULT_REQUEST_TIMEOUT = 10.0  # seconds
DEFAULT_MAX_RETRIES = 3
