import pandas as pd
import streamlit as st

from database.storage import load_results


def render_search_bar() -> tuple[str, bool]:
    st.title("🏆 Competitors Dashboard")
    st.markdown("Search a product to compare prices across Amazon and Daraz.")

    col1, col2 = st.columns([4, 1])
    with col1:
        keyword = st.text_input(
            label="Product",
            placeholder="e.g. apple ipad air M2",
            label_visibility="collapsed"
        )
    with col2:
        searched = st.button("Search", use_container_width=True)

    return keyword.strip(), searched


def render_market_overview(df: pd.DataFrame):
    st.subheader("Market Overview")

    amazon = df[df["platform"] == "amazon"]
    daraz  = df[df["platform"] == "daraz"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        val = amazon[amazon["price"] > 0]["price"].min()
        st.metric("Lowest Amazon", f"USD {val:,.2f}" if val else "N/A")

    with col2:
        val = daraz[daraz["price"] > 0]["price"].min()
        st.metric("Lowest Daraz", f"LKR {val:,.2f}" if val else "N/A")

    with col3:
        val = amazon[amazon["price"] > 0]["price"].mean()
        st.metric("Avg Amazon", f"USD {val:,.2f}" if val else "N/A")

    with col4:
        val = daraz[daraz["price"] > 0]["price"].mean()
        st.metric("Avg Daraz", f"LKR {val:,.2f}" if val else "N/A")


def render_comparison_table(df: pd.DataFrame):
    st.subheader("Product Comparison")

    display = df[[
        "platform", "product_name", "price",
        "currency", "rating", "discount_pct", "url"
    ]].copy()

    display.columns = [
        "Platform", "Product", "Price",
        "Currency", "Rating", "Discount %", "URL"
    ]

    display["Price"] = display["Price"].apply(
        lambda x: f"{x:,.2f}" if x > 0 else "N/A"
    )
    display["Discount %"] = display["Discount %"].apply(
        lambda x: f"{x:.0f}%" if x > 0 else "-"
    )
    display["URL"] = display["URL"].apply(
        lambda x: f'<a href="{x}" target="_blank">View</a>' if x else "-"
    )

    st.write(
        display.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )


def render_price_distribution(df: pd.DataFrame):
    st.subheader("Price Distribution")

    amazon = df[(df["platform"] == "amazon") & (df["price"] > 0)][["product_name", "price"]].copy()
    daraz  = df[(df["platform"] == "daraz")  & (df["price"] > 0)][["product_name", "price"]].copy()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Amazon (USD)**")
        if not amazon.empty:
            st.bar_chart(amazon.set_index("product_name")["price"])
        else:
            st.info("No Amazon data")

    with col2:
        st.markdown("**Daraz (LKR)**")
        if not daraz.empty:
            st.bar_chart(daraz.set_index("product_name")["price"])
        else:
            st.info("No Daraz data")


def render_best_deals(df: pd.DataFrame):
    st.subheader("Best Deals")

    deals = df[df["discount_pct"] > 0].sort_values(
        "discount_pct", ascending=False
    ).head(5)

    if deals.empty:
        st.info("No discounts found for this search.")
        return

    for _, row in deals.iterrows():
        st.markdown(
            f"**{row['product_name'][:80]}...** — "
            f"{row['discount_pct']:.0f}% off — "
            f"{row['currency']} {row['price']:,.2f} "
            f"([{row['platform']}]({row['url']}))"
        )


def render_price_history(keyword: str):
    st.subheader("Price History")

    df = load_results(keyword)

    if df.empty:
        st.info("No history yet. Search more times to build price trend.")
        return

    products = df["product_name"].unique().tolist()
    selected = st.selectbox("Select product to track", products)

    history = df[df["product_name"] == selected].sort_values("scraped_at")

    if len(history) < 2:
        st.info("Search this keyword again later to see price trend.")
        return

    st.line_chart(history.set_index("scraped_at")["price"])