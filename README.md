# My FootDr archive scraper

## Overview

This tool crawls archived versions of the My FootDr "Our Clinics" pages on the Internet Archive's Wayback Machine and extracts structured information about each clinic.

It can:

- discover and print all `/our-clinics/` URLs from a given Wayback snapshot
- extract clinic records (name, address, email, phone, services)
- export clinic records to CSV or JSON, with simple validation and an optional report of incomplete records

## Installation

1. Ensure Python 3.11 or later is available.
2. Install dependencies in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

## Command-line usage

The main entry point is the `scrape_myfootdr_clinics.py` script in the project root.

```bash
python scrape_myfootdr_clinics.py [OPTIONS]
```

### Common options

* `--base-url URL`
  Wayback URL to start from. Defaults to the July 2025 snapshot of the "Our Clinics" landing page.

* `--limit N`
  Optional maximum number of pages to visit. Useful for debugging small runs.

* `--debug`
  Enable verbose logging.

### Modes

The `--mode` flag controls what the CLI outputs:

#### 1. URL discovery (default)

Prints all discovered `/our-clinics/…` URLs.

```bash
python scrape_myfootdr_clinics.py --mode urls
```

Save the URLs to a text file:

```bash
python scrape_myfootdr_clinics.py \
  --mode urls \
  --out data/our_clinics_urls.txt
```

#### 2. Clinics as JSON

Extracts clinic records and prints JSON to stdout:

```bash
python scrape_myfootdr_clinics.py --mode clinics-json
```

Write the JSON to a file instead:

```bash
python scrape_myfootdr_clinics.py \
  --mode clinics-json \
  --out data/clinics.json
```

#### 3. Clinics as CSV

Writes clinic records to a CSV file with the exact columns:

1. `Name of Clinic`
2. `Address`
3. `Email`
4. `Phone`
5. `Services` (semicolon-separated list)

```bash
python scrape_myfootdr_clinics.py \
  --mode clinics-csv \
  --out data/clinics.csv
```

If `--out` is not provided in `clinics-csv` mode, the CSV is written to `clinics.csv` in the current directory.

The CSV writer joins the `services` list into a single string:

```text
General podiatry; Ingrown toenail treatment; Custom orthotics
```

### Incomplete clinics report

When exporting to CSV you can optionally write a separate CSV containing only clinics that are missing **critical** fields (name, address, or phone):

```bash
python scrape_myfootdr_clinics.py \
  --mode clinics-csv \
  --out data/clinics.csv \
  --incomplete-out data/clinics_incomplete.csv
```

If no clinics are incomplete the file is not created and the CLI will log that nothing was written.

### Validation

After writing the CSV, the CLI logs a short summary, including:

* total number of clinics extracted
* number of complete vs incomplete clinics (based on critical fields)
* per-column counts of missing values (name, address, email, phone, services)

Use `--debug` for more detailed crawl logging.

## Running with Docker

A simple Dockerfile is provided.

Build the image:

```bash
docker build -t myfootdr-scraper .
```

Run the scraper (CSV mode) inside a container:

```bash
docker run --rm -v "$(pwd)/data:/app/data" myfootdr-scraper \
  --mode clinics-csv \
  --out data/clinics.csv \
  --incomplete-out data/clinics_incomplete.csv
```

The `-v` flag mounts a host `data/` directory into the container so that the CSV files are written to your local filesystem.

You can pass any CLI flags after the image name; they are forwarded to `scrape_myfootdr_clinics.py`.

## Limitations

* The scraper relies on heuristics tailored to the archived My FootDr clinic pages; it may not cope well with substantial layout changes.
* The Wayback Machine can occasionally rate-limit or error on requests; the crawler retries a small number of times but does not currently implement backoff or sophisticated rate-limiting.
* Service lists and some contact details may be missing or incomplete for clinics whose HTML structure deviates significantly from the examples used during development.
