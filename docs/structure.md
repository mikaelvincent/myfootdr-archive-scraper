# DOM structure notes (Sprint 1)

These notes summarise initial observations about the archived My FootDr "Our Clinics" pages on the Wayback Machine and guide the extractor design for later sprints.

## 1. Our Clinics landing page

- URL used for Sprint 1:

  - `https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/`

- General characteristics:

  - Page title refers to "Our Clinics".
  - Main content area lists regions (e.g. Brisbane, Gold Coast, Sunshine Coast).
  - Each region links to a `/our-clinics/<region>/` style URL.
  - Navigation, header, and footer contain non‑clinic links (blog, services, etc.) that should be ignored later.

### Likely selectors

- Main heading:

  - Top‑level `<h1>` inside the main content region (e.g. inside `<main>`, `<article>`, or a `.entry-content` container).

- Region links:

  - Plain `<a>` tags whose `href` values start with `/our-clinics/` when the Wayback wrapper is removed.
  - Some links may be wrapped in cards or lists (`<ul>`, `<li>`, or `<div>` grids).

## 2. Region pages

- Region pages typically show a list of clinics for a city/region.
- Common characteristics:

  - A heading with the region name.
  - A list of clinics, each linking to a specific clinic URL under `/our-clinics/...`.
  - No direct clinic contact details (those live on clinic pages).

### Likely patterns

- Breadcrumb navigation that includes:

  - `Our Clinics > <Region name>`

- Clinic links:

  - Link text is the clinic name (e.g. "Allsports Podiatry Noosa").
  - `href` points to a Wayback URL whose original path is under `/our-clinics/`.

## 3. Clinic pages

Clinic pages are the ultimate target for data extraction in later sprints.

From manual inspection and the project specification:

- Typical content:

  - A main heading, often phrased as "Welcome to <Clinic name>" or similar.
  - A "Call" action with a clinic‑specific phone number.
  - A "Get directions with Google Maps" link where the link text contains the physical address.
  - An email link, likely rendered as `mailto:<address>`.
  - A descriptive section followed by a bullet list of services.

### Elements to look for

These will be used in later sprints:

- **Clinic name**

  - Main `<h1>` in the content area (e.g. `main h1`, `article h1`, `.entry-content h1`).
  - Last breadcrumb item, if present.
  - `<title>` tag as a fallback, with any suffixes stripped.

- **Address**

  - `<a>` tag near text like "Get directions" or "Google Maps".
  - Link text that looks like an Australian street address, containing:

    - A street number.
    - Words such as "Rd", "Road", "St", "Street", "Ave", "Avenue", "Highway".
    - State abbreviations like "QLD", "NSW", "VIC", etc.

- **Email**

  - `<a href="mailto:...">` primarily in the main content area, not in header/footer.
  - If multiple emails exist, prefer the one closest to the clinic name or address.

- **Phone**

  - `<a href="tel:...">` links with local clinic numbers.
  - Avoid generic numbers such as `1800 366 837`, which are likely global contact lines.

- **Services**

  - Bullet lists (`<ul><li>...</li></ul>`) close to phrases like "assist with" or "services include".
  - Each `<li>` is usually a short phrase describing a specific service.

## 4. Wayback considerations

- All page URLs are wrapped by the Wayback Machine, typically as:

  - `https://web.archive.org/web/<timestamp>/https://www.myfootdr.com.au/our-clinics/...`

- For crawling and filtering later:

  - Treat any URL starting with `https://web.archive.org/web/` as already Wayback‑safe.
  - For relative links, rely on `urljoin(current_page_url, href)` so Wayback's rewriting is preserved.
  - When deciding whether to crawl a URL, strip the Wayback prefix and check that the original URL starts with `https://www.myfootdr.com.au/our-clinics/`.

These notes should be refined in later sprints as more clinic pages are explored and concrete HTML fixtures are captured.
