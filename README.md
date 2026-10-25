# Fashion Trend Intelligence

A portfolio-ready Streamlit dashboard that combines fashion search-interest trends, competitor listing prices, and optional customer-review signals for the Indian market.

> **Important:** This is a decision-support prototype, not a sales forecasting model. Google Trends values are relative interest scores. Shopping results are point-in-time search snapshots, not a complete market census. Review topic detection uses keyword rules rather than a trained NLP model.

## Features

- **Trend Explorer:** visualizes weekly interest for multiple fashion keywords and calculates recent averages and momentum.
- **Opportunity Ranking:** creates a transparent provisional score from relative trend interest (60%) and recent momentum (40%).
- **Competitor Pricing:** compares observed listing counts, median/min/max prices, ratings, and flagged price outliers.
- **Review Intelligence:** counts review-topic mentions for fit, fabric, value, comfort, delivery, and appearance; uses ratings as a basic sentiment proxy when present.
- **Data Quality:** reports missing prices/ratings, duplicate removal, and possible price outliers.
- **CSV exports:** download trend analysis, cleaned competitor listings, and review-topic summaries.
- **Optional live search:** fetches Google Shopping results through SerpApi.

## Tech stack

- Python
- Streamlit
- pandas / NumPy
- Requests
- SerpApi Google Shopping endpoint (optional)

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/fashion-trend-intelligence.git
cd fashion-trend-intelligence
```

### 2. Create an environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install requirements

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

The app opens in your browser, usually at `http://localhost:8501`.

## Use your own data

Use the sidebar upload fields:

### Google Trends CSV

Expected format: one `date` column and one numeric column per keyword.

```csv
date,cargo pants,baggy jeans,oversized t-shirt,polo shirt
Aug 23–29, 2026,20,67,5,50
Aug 30–Sep 5, 2026,20,63,5,46
```

Use a full exported dataset for meaningful analysis. The built-in demo rows are illustrative examples only.

### Competitor products CSV

The app accepts common aliases, including:

- `keyword` / `category` / `search_term`
- `product_name` / `title` / `product`
- `brand_or_seller` / `source` / `seller`
- `price` / `extracted_price`
- `rating`
- `review_count` / `reviews`
- `product_url` / `product_link`

Missing ratings remain missing, not zero. Outliers are flagged for inspection and not automatically removed.

### Customer reviews CSV (optional)

Include a text column named `review`, `review_text`, `text`, `comment`, or `content`. A numeric `rating` column is optional.

The review module uses simple keyword matching and a rating-based sentiment proxy. It should not be described as AI/NLP sentiment classification unless replaced with a validated model.

## Optional live Google Shopping search with SerpApi

1. Create a SerpApi account and check its current pricing, quota, and terms.
2. Set the environment variable `SERPAPI_KEY`, or paste the key into the app's password field for the current session.
3. Click **Fetch Google Shopping results**.

Linux/macOS:

```bash
export SERPAPI_KEY="YOUR_KEY"
streamlit run app.py
```

PowerShell:

```powershell
$env:SERPAPI_KEY="YOUR_KEY"
streamlit run app.py
```

Do not hard-code API keys or commit `.env` files or secrets to GitHub. The app makes a request per keyword, so usage may consume API credits.

## Scoring methodology

The current provisional opportunity score is:

`0.60 × percentile rank(recent 4-week average) + 0.40 × percentile rank(momentum)`

Momentum compares the latest four available observations with the preceding four observations. If the previous average is zero, percentage momentum is undefined. The score is relative to the categories included in the dataset and should not be interpreted as probability of success, profit, or sales.

For a production deployment, improve the scoring system by adding:
- product relevance validation and direct product URLs
- scheduled, timestamped collection and historical price tracking
- review volume and validated sentiment/topic extraction
- unit economics: landed cost, shipping, return rate, discounts, and contribution margin
- category-specific seasonality and confidence intervals
- persistent storage (e.g., PostgreSQL), caching, retry/backoff, logging, and tests

## Suggested repository structure

```text
fashion-trend-intelligence/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Limitations

- Google Trends reports normalized relative interest, not absolute searches or purchases.
- Google Shopping results vary by query, location, time, and API availability.
- Some listings can be duplicates, irrelevant matches, or have missing ratings/prices.
- A search result's link may not always be a direct product page.
- Keyword-based review themes can miss context, sarcasm, negation, and synonyms.
- Demo rows are not real market evidence; upload verified datasets for analysis.

## Resume / CV description

**Fashion Trend Intelligence Dashboard | Python, Streamlit, pandas, NumPy, REST API**
- Built an interactive dashboard to analyze weekly fashion search-interest trends and compare competitor listing prices across categories.
- Implemented CSV ingestion, duplicate handling, missing-value checks, outlier flags, and category-level price summaries.
- Integrated optional SerpApi Google Shopping retrieval and added a rule-based customer-review topic analysis module.
- Designed a transparent trend-momentum ranking and downloadable analytical outputs.

Only claim API integration, deployment, or review analysis experience that you have personally run and verified.

## License

Choose a license appropriate for your intended use before publishing. Review the data provider's terms before redistributing fetched data.
