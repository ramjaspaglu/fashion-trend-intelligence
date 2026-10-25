import os
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Fashion Trend Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_TITLE = "Fashion Trend Intelligence"
TREND_COLUMNS = {
    "baggy jeans": "baggy jeans men",
    "cargo pants": "cargo pants men",
    "oversized t-shirt": "oversized t shirt men",
    "polo shirt": "polo shirt men",
}
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def normalize_text(value):
    value = str(value or "").lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_price(value):
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)
    cleaned = re.sub(r"[^0-9.]", "", str(value).replace(",", ""))
    try:
        return float(cleaned) if cleaned else np.nan
    except ValueError:
        return np.nan


def read_csv_upload(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read {uploaded_file.name}: {exc}")
        return None


def get_demo_trends():
    # Illustrative data only. Replace with a real export/API result for analysis.
    rows = [
        ("Aug 23â€“29, 2026", 20, 67, 5, 50),
        ("Aug 30â€“Sep 5, 2026", 20, 63, 5, 46),
        ("Sep 6â€“12, 2026", 20, 61, 5, 44),
        ("Sep 13â€“19, 2026", 19, 64, 5, 46),
        ("Sep 20â€“26, 2026", 22, 67, 4, 42),
        ("Sep 27â€“Oct 3, 2026", 22, 71, 4, 46),
        ("Oct 4â€“10, 2026", 22, 76, 4, 49),
        ("Oct 11â€“17, 2026", 23, 89, 4, 47),
        ("Oct 18â€“24, 2026", 22, 78, 4, 44),
        ("Oct 25â€“31, 2026", 22, 85, 4, 42),
    ]
    return pd.DataFrame(
        rows,
        columns=["date", "cargo pants", "baggy jeans", "oversized t-shirt", "polo shirt"],
    )


def get_demo_competitors():
    # Illustrative seed rows only; not a verified current market dataset.
    return pd.DataFrame([
        {"keyword": "baggy jeans men", "product_name": "Example relaxed fit jeans", "brand_or_seller": "Example Marketplace", "price": 999, "rating": 4.1, "review_count": 120, "product_url": ""},
        {"keyword": "cargo pants men", "product_name": "Example utility cargo pants", "brand_or_seller": "Example Marketplace", "price": 1199, "rating": 4.0, "review_count": 85, "product_url": ""},
        {"keyword": "oversized t shirt men", "product_name": "Example oversized tee", "brand_or_seller": "Example Marketplace", "price": 499, "rating": 4.2, "review_count": 240, "product_url": ""},
        {"keyword": "polo shirt men", "product_name": "Example polo shirt", "brand_or_seller": "Example Marketplace", "price": 799, "rating": 3.9, "review_count": 70, "product_url": ""},
    ])


def fetch_google_shopping(api_key, keywords, max_per_keyword=20):
    products = []
    errors = []
    for keyword in keywords:
        params = {
            "engine": "google_shopping",
            "q": keyword,
            "gl": "in",
            "hl": "en",
            "api_key": api_key,
        }
        try:
            response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=45)
            response.raise_for_status()
            payload = response.json()
            if payload.get("error"):
                errors.append(f"{keyword}: {payload['error']}")
                continue
            for item in payload.get("shopping_results", [])[:max_per_keyword]:
                products.append({
                    "keyword": keyword,
                    "product_name": item.get("title"),
                    "brand_or_seller": item.get("source"),
                    "price_text": item.get("price"),
                    "price": item.get("extracted_price", parse_price(item.get("price"))),
                    "rating": item.get("rating"),
                    "review_count": item.get("reviews"),
                    "product_url": item.get("product_link"),
                    "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                })
        except requests.RequestException as exc:
            errors.append(f"{keyword}: request failed ({exc})")
        except ValueError:
            errors.append(f"{keyword}: API did not return valid JSON")
    return pd.DataFrame(products), errors


def clean_competitors(df):
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    aliases = {
        "keyword": ["keyword", "category", "search_term"],
        "product_name": ["product_name", "title", "product", "name"],
        "brand_or_seller": ["brand_or_seller", "source", "seller", "brand", "merchant"],
        "price": ["price", "extracted_price", "price_inr"],
        "price_text": ["price_text", "display_price"],
        "rating": ["rating", "stars"],
        "review_count": ["review_count", "reviews", "number_of_reviews"],
        "product_url": ["product_url", "product_link", "url"],
        "collected_at_utc": ["collected_at_utc", "collected_at", "timestamp"],
    }
    lower_lookup = {str(c).lower().strip(): c for c in out.columns}
    rename = {}
    for canonical, candidates in aliases.items():
        if canonical not in out.columns:
            for candidate in candidates:
                if candidate in lower_lookup:
                    rename[lower_lookup[candidate]] = canonical
                    break
    out = out.rename(columns=rename)
    for col in ["keyword", "product_name", "brand_or_seller", "product_url", "price_text"]:
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].fillna("").astype(str).str.strip()
    if "price" not in out.columns:
        out["price"] = out["price_text"].apply(parse_price)
    else:
        out["price"] = out["price"].apply(parse_price)
    for col in ["rating", "review_count"]:
        if col not in out.columns:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if "collected_at_utc" not in out.columns:
        out["collected_at_utc"] = ""
    out["normalized_name"] = out["product_name"].apply(normalize_text)
    out["valid_price"] = out["price"].gt(0)
    out["valid_rating"] = out["rating"].between(0, 5)
    out["price_outlier"] = False
    for keyword, idx in out.groupby("keyword").groups.items():
        prices = out.loc[idx, "price"].where(out.loc[idx, "price"].gt(0))
        if prices.notna().sum() >= 4:
            q1, q3 = prices.quantile(.25), prices.quantile(.75)
            iqr = q3 - q1
            if iqr > 0:
                out.loc[idx, "price_outlier"] = (
                    (prices < q1 - 1.5 * iqr) | (prices > q3 + 1.5 * iqr)
                ).fillna(False)
    out = out.sort_values(["rating", "review_count"], ascending=False, na_position="last")
    out = out.drop_duplicates(
        subset=["keyword", "normalized_name", "brand_or_seller", "price"],
        keep="first",
    ).reset_index(drop=True)
    return out


def trend_analysis(trends):
    if trends is None or trends.empty:
        return pd.DataFrame()
    df = trends.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "date" not in df.columns:
        df = df.rename(columns={df.columns[0]: "date"})
    rows = []
    for keyword in [c for c in df.columns if c != "date"]:
        values = pd.to_numeric(df[keyword], errors="coerce").dropna()
        if len(values) < 2:
            continue
        recent = values.iloc[-4:].mean()
        previous = values.iloc[-8:-4].mean() if len(values) >= 8 else np.nan
        momentum = ((recent - previous) / previous * 100) if pd.notna(previous) and previous != 0 else np.nan
        rows.append({
            "category": keyword,
            "latest_score": values.iloc[-1],
            "recent_4w_avg": recent,
            "previous_4w_avg": previous,
            "momentum_pct": momentum,
            "observations": len(values),
        })
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["trend_score"] = result["recent_4w_avg"].rank(pct=True) * 100
    result["momentum_score"] = result["momentum_pct"].rank(pct=True) * 100
    result["opportunity_score"] = (
        .60 * result["trend_score"] + .40 * result["momentum_score"]
    ).round(1)
    return result.sort_values("opportunity_score", ascending=False, na_position="last")


def competitor_analysis(cleaned):
    if cleaned is None or cleaned.empty:
        return pd.DataFrame()
    df = cleaned.copy()
    df["keyword_norm"] = df["keyword"].apply(normalize_text)
    rows = []
    for category, search_term in TREND_COLUMNS.items():
        target = normalize_text(search_term)
        # Exact normalized match avoids mixing categories too aggressively.
        subset = df[(df["keyword_norm"] == target) & df["price"].gt(0)]
        rows.append({
            "category": category,
            "competitor_listings": len(subset),
            "median_price_inr": subset["price"].median(),
            "min_price_inr": subset["price"].min(),
            "max_price_inr": subset["price"].max(),
            "median_rating": subset.loc[subset["rating"].between(0, 5), "rating"].median(),
            "rated_listings": int(subset["rating"].between(0, 5).sum()),
            "outlier_listings": int(subset["price_outlier"].sum()) if "price_outlier" in subset else 0,
        })
    return pd.DataFrame(rows)


def review_intelligence(reviews):
    if reviews is None or reviews.empty:
        return pd.DataFrame(), pd.DataFrame()
    df = reviews.copy()
    lower_lookup = {str(c).lower().strip(): c for c in df.columns}
    text_col = next((lower_lookup[c] for c in ["review", "review_text", "text", "comment", "content"] if c in lower_lookup), None)
    rating_col = next((lower_lookup[c] for c in ["rating", "stars", "score"] if c in lower_lookup), None)
    if text_col is None:
        return pd.DataFrame(), pd.DataFrame()
    df["review_text_clean"] = df[text_col].fillna("").astype(str)
    if rating_col:
        df["review_rating"] = pd.to_numeric(df[rating_col], errors="coerce")
    else:
        df["review_rating"] = np.nan
    topics = {
        "Fit / sizing": ["size", "sizing", "fit", "tight", "loose", "length"],
        "Fabric / quality": ["fabric", "quality", "material", "thin", "thick", "stitch", "tear"],
        "Price / value": ["price", "cost", "expensive", "cheap", "value", "money"],
        "Comfort": ["comfort", "comfortable", "itch", "soft", "rough"],
        "Delivery / packaging": ["delivery", "late", "package", "packaging", "shipping"],
        "Colour / appearance": ["color", "colour", "fade", "look", "photo", "picture"],
    }
    topic_rows = []
    text_series = df["review_text_clean"].str.lower()
    for topic, words in topics.items():
        mask = text_series.apply(lambda t: any(re.search(r"\b" + re.escape(w) + r"\b", t) for w in words))
        matching = df[mask]
        topic_rows.append({
            "topic": topic,
            "mention_count": int(mask.sum()),
            "share_of_reviews_pct": round(mask.mean() * 100, 1) if len(mask) else 0,
            "average_rating": matching["review_rating"].mean(),
        })
    # Simple rating-based sentiment proxy, not an ML sentiment model.
    def sentiment(row):
        rating = row["review_rating"]
        if pd.notna(rating):
            if rating >= 4:
                return "Positive (rating proxy)"
            if rating <= 2:
                return "Negative (rating proxy)"
            return "Neutral (rating proxy)"
        return "Unrated"
    df["sentiment_proxy"] = df.apply(sentiment, axis=1)
    sentiment_summary = df["sentiment_proxy"].value_counts().rename_axis("sentiment").reset_index(name="reviews")
    return pd.DataFrame(topic_rows).sort_values("mention_count", ascending=False), sentiment_summary


st.title(APP_TITLE)
st.caption("A portfolio project for fashion trend discovery, competitor pricing, and review signals in India.")
st.info("Decision-support prototype. Search-interest scores are relative; shopping results are snapshots, not a complete market census. Review topic detection uses a transparent keyword heuristic, not a trained AI model.")

with st.sidebar:
    st.header("Data sources")
    st.write("Upload your own CSV files or use the optional live shopping search.")
    trends_upload = st.file_uploader("Google Trends CSV", type=["csv"], key="trends")
    competitors_upload = st.file_uploader("Competitor products CSV", type=["csv"], key="competitors")
    reviews_upload = st.file_uploader("Customer reviews CSV (optional)", type=["csv"], key="reviews")
    st.divider()
    st.subheader("Optional live data")
    api_key_input = st.text_input("SerpApi key", type="password", value=os.getenv("SERPAPI_KEY", ""))
    fetch_live = st.button("Fetch Google Shopping results", width="stretch")
    st.caption("API costs/quotas may apply. The key is used only for this session and is not saved by this app.")

trends_df = read_csv_upload(trends_upload) if trends_upload else None
if trends_df is None:
    trends_df = get_demo_trends()

competitors_raw = read_csv_upload(competitors_upload) if competitors_upload else None
live_errors = []
if fetch_live:
    if not api_key_input:
        st.sidebar.error("Enter a SerpApi key first.")
    else:
        with st.spinner("Fetching shopping results..."):
            live_df, live_errors = fetch_google_shopping(api_key_input, list(TREND_COLUMNS.values()))
        if not live_df.empty:
            competitors_raw = live_df
            st.sidebar.success(f"Fetched {len(live_df)} listings for this session.")
        else:
            st.sidebar.error("No listings returned. Check API quota and key.")
        for error in live_errors:
            st.warning(error)

if competitors_raw is None:
    competitors_raw = get_demo_competitors()

cleaned = clean_competitors(competitors_raw)
trend_summary = trend_analysis(trends_df)
market_summary = competitor_analysis(cleaned)
reviews_df = read_csv_upload(reviews_upload) if reviews_upload else None
topic_summary, sentiment_summary = review_intelligence(reviews_df)

tab_overview, tab_trends, tab_market, tab_reviews, tab_quality = st.tabs([
    "Overview", "Trend Explorer", "Competitor Pricing", "Review Intelligence", "Data Quality"
])

with tab_overview:
    st.subheader("Market overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trend categories", len(trend_summary))
    c2.metric("Competitor listings", len(cleaned))
    c3.metric("Listings with prices", int(cleaned["valid_price"].sum()) if not cleaned.empty else 0)
    c4.metric("Reviews loaded", len(reviews_df) if reviews_df is not None else 0)
    st.markdown("### Opportunity ranking")
    if not trend_summary.empty:
        view = trend_summary[["category", "latest_score", "recent_4w_avg", "momentum_pct", "opportunity_score"]].copy()
        view.columns = ["Category", "Latest relative score", "Recent 4-week average", "Momentum (%)", "Provisional opportunity score"]
        st.dataframe(view, width="stretch", hide_index=True)
        st.bar_chart(trend_summary.set_index("category")["opportunity_score"])
    else:
        st.warning("Trend CSV needs a date column and numeric keyword columns.")

with tab_trends:
    st.subheader("Google Trends explorer")
    st.caption("Relative search interest, not absolute search volume or sales.")
    display_trends = trends_df.copy()
    display_trends.columns = [str(c).strip().lower() for c in display_trends.columns]
    if "date" in display_trends.columns:
        st.line_chart(display_trends.set_index("date"))
    else:
        st.warning("No date column found in the trends CSV.")
    if not trend_summary.empty:
        st.dataframe(trend_summary.round(2), width="stretch", hide_index=True)
    st.download_button(
        "Download trend analysis CSV",
        trend_summary.to_csv(index=False).encode("utf-8"),
        file_name="fashion_trend_analysis.csv",
        mime="text/csv",
    )

with tab_market:
    st.subheader("Competitor pricing snapshot")
    if not market_summary.empty:
        st.dataframe(market_summary.round(2), width="stretch", hide_index=True)
    st.markdown("#### Cleaned listings")
    cols = [c for c in ["keyword", "product_name", "brand_or_seller", "price", "rating", "review_count", "price_outlier", "product_url"] if c in cleaned.columns]
    st.dataframe(cleaned[cols], width="stretch", hide_index=True)
    st.download_button(
        "Download cleaned competitor CSV",
        cleaned.to_csv(index=False).encode("utf-8"),
        file_name="competitor_products_cleaned.csv",
        mime="text/csv",
    )

with tab_reviews:
    st.subheader("Review intelligence")
    if reviews_df is None:
        st.info("Upload a customer reviews CSV with a review/text/comment column. A rating column is optional.")
    elif topic_summary.empty:
        st.warning("Could not detect a review text column. Supported names include review, review_text, text, comment, or content.")
    else:
        st.caption("Topic mentions are keyword-based. Sentiment is inferred from ratings when present; this is not a trained sentiment model.")
        st.dataframe(topic_summary.round(2), width="stretch", hide_index=True)
        st.bar_chart(topic_summary.set_index("topic")["mention_count"])
        st.dataframe(sentiment_summary, width="stretch", hide_index=True)
        st.download_button(
            "Download review topic summary",
            topic_summary.to_csv(index=False).encode("utf-8"),
            file_name="review_topic_summary.csv",
            mime="text/csv",
        )

with tab_quality:
    st.subheader("Data quality checks")
    st.write("### Trend data")
    st.write(f"Rows: {len(trends_df)} | Columns: {len(trends_df.columns)}")
    st.dataframe(trends_df.tail(10), width="stretch", hide_index=True)
    st.write("### Competitor data")
    quality = pd.DataFrame([
        {"Check": "Raw rows", "Value": len(competitors_raw)},
        {"Check": "Cleaned unique rows", "Value": len(cleaned)},
        {"Check": "Duplicates removed", "Value": max(0, len(competitors_raw) - len(cleaned))},
        {"Check": "Missing price", "Value": int(cleaned["price"].isna().sum()) if not cleaned.empty else 0},
        {"Check": "Missing rating", "Value": int(cleaned["rating"].isna().sum()) if not cleaned.empty else 0},
        {"Check": "Price outliers flagged", "Value": int(cleaned["price_outlier"].sum()) if not cleaned.empty else 0},
    ])
    st.dataframe(quality, width="stretch", hide_index=True)
    st.caption("Outliers are flagged for review, not automatically deleted. Verify product relevance and direct URLs before business decisions.")

st.divider()
st.caption("Built with Python, Streamlit, pandas, NumPy, and the SerpApi Google Shopping endpoint. Treat all third-party listing data according to source terms and applicable policies.")

