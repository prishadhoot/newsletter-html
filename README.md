# newsletter-html

A newsletter HTML generator that **auto-loads tech news using AI**. Fetches structured content from the [Perplexity API](https://www.perplexity.ai/), then fills an HTML template to produce a ready-to-view or send newsletter page.

## Features

- **AI-powered content** — Uses Perplexity’s API to pull recent tech news (past 24 hours, viral stories, company developments).
- **Structured output** — Response is validated and shaped with Pydantic so the HTML template always gets the expected fields.
- **Template-based HTML** — Placeholders in an HTML template are replaced with the fetched data.
- **Dated outputs** — Each run saves a copy under `outputs/` with a date and run number (e.g. `template_today__number_1_14_03_2025.html`).
- **Logging** — Writes logs under `logs/` for debugging and auditing.

## Prerequisites

- **Python 3.x**
- **Perplexity API key** — Get one from [Perplexity](https://www.perplexity.ai/) (used for the “sonar” model).

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/prishadhoot/newsletter-html.git
   cd newsletter-html
   ```

2. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**

   Create a `.env` file in the project root:

   ```env
   PERPLEXITY_API_KEY=your_perplexity_api_key_here
   ```

   Do not commit `.env`; it is listed in `.gitignore`.

## Usage

From the project root, run:

```bash
python main.py
```

This will:

1. Fetch tech news from the Perplexity API using the prompt in `utils/templates/pplx_prompt.txt`.
2. Validate and normalize the response against `utils/templates/response_template.json`.
3. Load the HTML template from `utils/templates/template_placeholder.html`.
4. Replace placeholders (`{24h_1}` … `{24h_6}`, `{viral_1}` … `{viral_3}`, `{company_developments}`) with the API data.
5. Save the result as `utils/templates/template_today.html` and a dated copy in `outputs/`.

Open `main.html` (or the generated HTML files) in a browser to view the newsletter.

## Project structure

| Path | Description |
|------|-------------|
| `main.py` | Entry point: logging, API fetch, data processing, template fill, and file output. |
| `newsletter.py` | Newsletter logic (load data, template, fill, save) — used conceptually; `main.py` embeds this flow. |
| `data_process.py` / `data_query.py` | Logic is inlined in `main.py`: API client, Pydantic models, validation, and template matching. |
| `main.html` | Front-end page that displays or loads the newsletter. |
| `utils/templates/` | `pplx_prompt.txt`, `response_template.json`, `template_placeholder.html`, and generated `template_today.html`. |
| `outputs/` | Dated newsletter HTML files (one per run). |
| `logs/` | Created at runtime; log files for each run. |

## Configuration

- **API key** — Set `PERPLEXITY_API_KEY` in `.env`.
- **Prompt** — Edit `utils/templates/pplx_prompt.txt` to change what kind of tech news is requested.
- **Response shape** — Edit `utils/templates/response_template.json` to match the structure expected by your template and by `main.py`’s validation.
- **Layout** — Edit `utils/templates/template_placeholder.html` and use the same placeholder names so the script can fill them.


