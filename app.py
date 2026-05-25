import streamlit as st
import pandas as pd
import plotly.express as px
from pytrends.request import TrendReq
import yfinance as yf
import time

st.set_page_config(page_title="Fashion Resale Intelligence", layout="wide")

st.title("👗 Fashion Resale Market Intelligence")
st.subheader("Real-time trends, brand rankings & investment signals")

# --- GOOGLE TRENDS DATA ---
st.header("🔍 Most Searched Luxury Brands Right Now")

brands = ["Ema Savahl", "John Galliano", "Roberto Cavalli",
          "Jean Paul Gaultier", "Galliano Dior", "Tom Ford Gucci",
          "Vivienne Westwood", "Thierry Mugler", "Versace Vintage", "Giuseppe Zanotti"]

@st.cache_data(ttl=3600)
def get_trends(brands):
    pytrends = TrendReq(hl='en-US', tz=360)
    chunk1 = brands[:5]
    chunk2 = brands[5:]
    pytrends.build_payload(chunk1, timeframe='today 3-m')
    df1 = pytrends.interest_over_time()
    time.sleep(2)
    pytrends.build_payload(chunk2, timeframe='today 3-m')
    df2 = pytrends.interest_over_time()
    if 'isPartial' in df1.columns:
        df1 = df1.drop(columns=['isPartial'])
    if 'isPartial' in df2.columns:
        df2 = df2.drop(columns=['isPartial'])
    return pd.concat([df1, df2], axis=1)

with st.spinner("Fetching live Google Trends data..."):
    try:
        df_trends = get_trends(brands)
        avg_interest = df_trends.mean().sort_values(ascending=False).reset_index()
        avg_interest.columns = ["Brand", "Search Interest Score"]

        col1, col2 = st.columns(2)
        with col1:
            fig_bar = px.bar(avg_interest, x="Brand", y="Search Interest Score",
                             title="Brand Search Interest (Last 3 Months)",
                             color="Search Interest Score",
                             color_continuous_scale="purples")
            st.plotly_chart(fig_bar, use_container_width=True)
        with col2:
            fig_line = px.line(df_trends, title="Search Trends Over Time")
            st.plotly_chart(fig_line, use_container_width=True)

        st.header("💡 Investment Signals")
        st.markdown("Based on search trend momentum over the last 3 months:")

        recent = df_trends.tail(4).mean()
        older = df_trends.head(4).mean()
        momentum = ((recent - older) / older * 100).sort_values(ascending=False)
        momentum = momentum.dropna()

        col3, col4, col5 = st.columns(3)
        with col3:
            st.success(f"🟢 **BUY** — {momentum.index[0]}\nMomentum: +{momentum.iloc[0]:.1f}%")
        with col4:
            st.warning(f"🟡 **WATCH** — {momentum.index[1]}\nMomentum: +{momentum.iloc[1]:.1f}%")
        with col5:
            st.error(f"🔴 **AVOID** — {momentum.index[-1]}\nMomentum: {momentum.iloc[-1]:.1f}%")

    except Exception as e:
        st.error(f"Could not fetch live data: {e}")
        st.info("Try again in a few minutes — Google Trends may be rate limiting.")
        # --- MARKET SIZE CHART ---
st.header("📈 Resale vs Fast Fashion Market Growth")

data = {
    "Year": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027],
    "Resale Market (USD Billions)": [24, 28, 31, 36, 43, 52, 61, 70, 82, 95],
    "Fast Fashion Market (USD Billions)": [35, 38, 34, 40, 43, 45, 46, 47, 48, 49]
}
df_market = pd.DataFrame(data)
fig_market = px.line(df_market, x="Year",
                     y=["Resale Market (USD Billions)", "Fast Fashion Market (USD Billions)"],
                     title="Market Size Comparison (2018-2027)",
                     markers=True)
st.plotly_chart(fig_market, use_container_width=True)
st.caption("Source: ThredUp Annual Resale Report 2024 | 2025-2027 projected")

# --- BRAND SEARCH TOOL ---
st.header("🔎 Search Any Brand")
st.markdown("Enter any designer or brand to see its resale momentum:")

user_brand = st.text_input("Brand name", placeholder="e.g. Alexander McQueen")

if user_brand:
    with st.spinner(f"Fetching trends for {user_brand}..."):
        try:
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload([user_brand], timeframe='today 3-m')
            df_search = pytrends.interest_over_time()

            if df_search.empty:
                st.warning(f"No trend data found for '{user_brand}'. Try a different search term.")
            else:
                if 'isPartial' in df_search.columns:
                    df_search = df_search.drop(columns=['isPartial'])

                recent = df_search[user_brand].tail(4).mean()
                older = df_search[user_brand].head(4).mean()
                momentum = ((recent - older) / older) * 100 if older > 0 else 0

                fig_search = px.line(df_search, y=user_brand,
                                     title=f"{user_brand} Search Interest (Last 3 Months)",
                                     labels={user_brand: "Search Interest"})
                st.plotly_chart(fig_search, use_container_width=True)

                if momentum > 10:
                    st.success(f"🟢 BUY SIGNAL — {user_brand} is trending up {momentum:.1f}% — strong resale demand momentum.")
                elif momentum > 0:
                    st.warning(f"🟡 WATCH — {user_brand} showing mild momentum of +{momentum:.1f}%. Monitor before buying.")
                else:
                    st.error(f"🔴 AVOID — {user_brand} search interest down {momentum:.1f}%. Resale demand may be cooling.")
        except Exception as e:
            st.error(f"Could not fetch data: {e}. Try again in a moment.")
            # --- VALUE RETENTION CALCULATOR ---
st.header("💰 Resale Value Retention Calculator")
st.markdown("Estimate how much your piece is worth now and in the future:")

col_a, col_b = st.columns(2)

with col_a:
    calc_brand = st.selectbox("Brand", [
        "Vivienne Westwood", "Jean Paul Gaultier", "Roberto Cavalli",
        "John Galliano", "Galliano Dior", "Tom Ford Gucci",
        "Thierry Mugler", "Versace", "Alexander McQueen", "Chanel",
        "Hermes", "Louis Vuitton", "Prada", "Gucci", "Other"
    ])
    category = st.selectbox("Category", [
        "Bag", "Dress", "Jacket", "Shoes", "Accessory", "Suit", "Coat"
    ])

with col_b:
    purchase_price = st.number_input("Purchase Price (USD)", min_value=50, max_value=50000, value=500, step=50)
    condition = st.selectbox("Condition", ["New with tags", "Excellent", "Good", "Fair"])
    years_owned = st.slider("Years owned", 0, 20, 1)

brand_retention = {
    "Hermes": 1.15, "Chanel": 1.10, "Louis Vuitton": 1.05,
    "Galliano Dior": 1.08, "Tom Ford Gucci": 1.06,
    "Vivienne Westwood": 0.95, "Jean Paul Gaultier": 0.97,
    "Thierry Mugler": 1.02, "Roberto Cavalli": 0.85,
    "John Galliano": 0.90, "Versace": 0.88,
    "Alexander McQueen": 0.92, "Prada": 0.95, "Gucci": 0.90,
    "Other": 0.75
}

category_multiplier = {
    "Bag": 1.2, "Jacket": 1.1, "Coat": 1.05,
    "Dress": 0.95, "Suit": 1.0, "Shoes": 0.85, "Accessory": 0.90
}

condition_multiplier = {
    "New with tags": 1.0, "Excellent": 0.85, "Good": 0.70, "Fair": 0.50
}

if st.button("Calculate Resale Value"):
    base_rate = brand_retention.get(calc_brand, 0.75)
    cat_mult = category_multiplier.get(category, 1.0)
    cond_mult = condition_multiplier.get(condition, 0.85)

    current_value = purchase_price * cond_mult * (base_rate ** years_owned) * cat_mult
    value_1yr = current_value * base_rate
    value_2yr = current_value * (base_rate ** 2)
    value_3yr = current_value * (base_rate ** 3)

    st.subheader("📊 Results")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Value", f"${current_value:,.0f}", f"{((current_value/purchase_price)-1)*100:.1f}% vs paid")
    col2.metric("In 1 Year", f"${value_1yr:,.0f}", f"{((value_1yr/purchase_price)-1)*100:.1f}% vs paid")
    col3.metric("In 2 Years", f"${value_2yr:,.0f}", f"{((value_2yr/purchase_price)-1)*100:.1f}% vs paid")
    col4.metric("In 3 Years", f"${value_3yr:,.0f}", f"{((value_3yr/purchase_price)-1)*100:.1f}% vs paid")

    projection_df = pd.DataFrame({
        "Year": ["Now", "1 Year", "2 Years", "3 Years"],
        "Estimated Value (USD)": [current_value, value_1yr, value_2yr, value_3yr]
    })

    fig_proj = px.bar(projection_df, x="Year", y="Estimated Value (USD)",
                      title=f"{calc_brand} {category} Value Projection",
                      color="Estimated Value (USD)",
                      color_continuous_scale="purples")
    st.plotly_chart(fig_proj, use_container_width=True)

    if base_rate >= 1.0:
        st.success(f"✅ **Worth buying** — {calc_brand} {category.lower()}s tend to appreciate or hold value well on the resale market.")
    elif base_rate >= 0.90:
        st.warning(f"⚠️ **Moderate hold** — {calc_brand} retains decent value but expect some depreciation.")
    else:
        st.error(f"❌ **Buy for love, not investment** — {calc_brand} depreciates faster on the resale market.")

    st.caption("⚠️ Estimates based on average market trends. Actual resale value varies by specific piece, rarity, and market conditions.")
    # --- RESALE MARKET STOCK TRACKER ---
st.header("📊 Resale Market Health — Stock Tracker")
st.markdown("Tracking publicly traded resale companies as a proxy for market health:")

@st.cache_data(ttl=3600)
def get_stock_data(ticker, period="3mo"):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    return hist

col_s1, col_s2 = st.columns(2)

with col_s1:
    st.subheader("The RealReal (REAL)")
    try:
        hist_real = get_stock_data("REAL")
        current_price = hist_real['Close'].iloc[-1]
        start_price = hist_real['Close'].iloc[0]
        change = ((current_price - start_price) / start_price) * 100
        st.metric("Current Price", f"${current_price:.2f}", f"{change:.1f}% (3 months)")
        fig_real = px.line(hist_real, y="Close",
                           title="The RealReal Stock (3 Months)",
                           labels={"Close": "Price (USD)"})
        st.plotly_chart(fig_real, use_container_width=True)
    except Exception as e:
        st.error(f"Could not fetch REAL data: {e}")

with col_s2:
    st.subheader("ThredUp (TDUP)")
    try:
        hist_tdup = get_stock_data("TDUP")
        current_price = hist_tdup['Close'].iloc[-1]
        start_price = hist_tdup['Close'].iloc[0]
        change = ((current_price - start_price) / start_price) * 100
        st.metric("Current Price", f"${current_price:.2f}", f"{change:.1f}% (3 months)")
        fig_tdup = px.line(hist_tdup, y="Close",
                           title="ThredUp Stock (3 Months)",
                           labels={"Close": "Price (USD)"})
        st.plotly_chart(fig_tdup, use_container_width=True)
    except Exception as e:
        st.error(f"Could not fetch TDUP data: {e}")

st.subheader("📰 Market Sentiment")
try:
    real_change = ((hist_real['Close'].iloc[-1] - hist_real['Close'].iloc[0]) / hist_real['Close'].iloc[0]) * 100
    tdup_change = ((hist_tdup['Close'].iloc[-1] - hist_tdup['Close'].iloc[0]) / hist_tdup['Close'].iloc[0]) * 100
    avg_change = (real_change + tdup_change) / 2

    if avg_change > 5:
        st.success(f"🟢 Resale market is **bullish** — both major platforms up an average of {avg_change:.1f}% over 3 months. Good time to buy inventory.")
    elif avg_change > 0:
        st.warning(f"🟡 Resale market is **neutral** — modest average gain of {avg_change:.1f}%. Proceed with caution.")
    else:
        st.error(f"🔴 Resale market is **bearish** — platforms down an average of {avg_change:.1f}%. Consider holding off on large purchases.")
except:
    st.info("Could not calculate market sentiment.")
    # --- PRICE COMPARISON TOOL ---
st.header("🖼️ Price Comparison Tool")
st.markdown("Upload a photo of your piece and get estimated prices across resale platforms:")

uploaded_image = st.file_uploader("Upload an image of your piece", type=["jpg", "jpeg", "png", "webp"])

col_p1, col_p2 = st.columns(2)

with col_p1:
    comp_brand = st.selectbox("Brand", [
        "Vivienne Westwood", "Jean Paul Gaultier", "Roberto Cavalli",
        "John Galliano", "Galliano Dior", "Tom Ford Gucci",
        "Thierry Mugler", "Versace", "Alexander McQueen", "Chanel",
        "Hermes", "Louis Vuitton", "Prada", "Gucci", "Balenciaga",
        "Saint Laurent", "Bottega Veneta", "Dior", "Fendi", "Giuseppe Zanotti", "Other"
    ], key="comp_brand")
    comp_category = st.selectbox("Category", [
        "Bag", "Dress", "Jacket", "Shoes", "Accessory", "Suit", "Coat", "Top", "Pants"
    ], key="comp_category")

with col_p2:
    comp_condition = st.selectbox("Condition", [
        "New with tags", "Excellent", "Good", "Fair"
    ], key="comp_condition")
    comp_size = st.selectbox("Size", [
        "XXS", "XS", "S", "M", "L", "XL", "XXL", "One Size", "N/A"
    ], key="comp_size")

if uploaded_image:
    st.image(uploaded_image, caption="Your piece", width=300)

# Price estimation logic
platform_multipliers = {
    "The RealReal": {"New with tags": 0.65, "Excellent": 0.50, "Good": 0.38, "Fair": 0.25},
    "Poshmark":     {"New with tags": 0.55, "Excellent": 0.42, "Good": 0.30, "Fair": 0.18},
    "eBay":         {"New with tags": 0.60, "Excellent": 0.45, "Good": 0.33, "Fair": 0.20},
}

brand_base_price = {
    "Hermes": 4000, "Chanel": 3000, "Louis Vuitton": 1500,
    "Galliano Dior": 1200, "Tom Ford Gucci": 1000,
    "Vivienne Westwood": 600, "Jean Paul Gaultier": 700,
    "Thierry Mugler": 800, "Roberto Cavalli": 500,
    "John Galliano": 600, "Versace": 700,
    "Alexander McQueen": 900, "Prada": 1000, "Gucci": 900,
    "Balenciaga": 800, "Saint Laurent": 900, "Bottega Veneta": 1200,
    "Dior": 1500, "Fendi": 1100, "Other": 300
}

category_price_mult = {
    "Bag": 1.5, "Jacket": 1.1, "Coat": 1.2,
    "Dress": 0.9, "Suit": 1.1, "Shoes": 0.8,
    "Accessory": 0.6, "Top": 0.7, "Pants": 0.8
}

if st.button("Compare Prices"):
    base = brand_base_price.get(comp_brand, 300)
    cat_m = category_price_mult.get(comp_category, 1.0)
    estimated_retail = base * cat_m

    st.subheader(f"💲 Estimated Resale Prices — {comp_brand} {comp_category}")
    st.caption(f"Based on estimated retail value of ${estimated_retail:,.0f}")

    col_r, col_po, col_e = st.columns(3)

    rr_price = estimated_retail * platform_multipliers["The RealReal"][comp_condition]
    po_price = estimated_retail * platform_multipliers["Poshmark"][comp_condition]
    eb_price = estimated_retail * platform_multipliers["eBay"][comp_condition]

    with col_r:
        st.metric("🔴 The RealReal", f"${rr_price:,.0f}")
        st.caption("Authenticated luxury. Higher buyer trust, lower seller payout.")

    with col_po:
        st.metric("🔵 Poshmark", f"${po_price:,.0f}")
        st.caption("Peer-to-peer. Set your own price, wider audience.")

    with col_e:
        st.metric("🟡 eBay", f"${eb_price:,.0f}")
        st.caption("Largest marketplace. Best for rare/archive pieces.")

    best_platform = max(
        [("The RealReal", rr_price), ("Poshmark", po_price), ("eBay", eb_price)],
        key=lambda x: x[1]
    )

    st.success(f"💡 **Best platform to sell:** {best_platform[0]} — estimated ${best_platform[1]:,.0f} for your {comp_condition.lower()} {comp_brand} {comp_category.lower()} (Size: {comp_size}).")
    # Price comparison chart
    comparison_df = pd.DataFrame({
        "Platform": ["The RealReal", "Poshmark", "eBay"],
        "Estimated Price (USD)": [rr_price, po_price, eb_price],
        "Color": ["#E63946", "#457B9D", "#F4A261"]
    })

    fig_comp = px.bar(comparison_df, x="Platform", y="Estimated Price (USD)",
                      title="Price Comparison Across Platforms",
                      color="Platform",
                      color_discrete_map={
                          "The RealReal": "#E63946",
                          "Poshmark": "#457B9D",
                          "eBay": "#F4A261"
                      })
    st.plotly_chart(fig_comp, use_container_width=True)



