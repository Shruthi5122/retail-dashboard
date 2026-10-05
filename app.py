import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Retail KPI Dashboard",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

DATA_PATH = "data/retail-orders-clean.csv"

df = pd.read_csv(DATA_PATH)

# Convert date column
df["order_date"] = pd.to_datetime(
    df["order_date"],
    errors="coerce"
)

# Make sure numeric columns are numeric
numeric_columns = [
    "quantity",
    "unit_price",
    "discount_pct",
    "gross_sales",
    "sales_after_discount"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("📊 Retail Business KPI Dashboard")

st.markdown(
    "Interactive dashboard for monitoring retail sales, "
    "orders, customer segments, categories and payment status."
)

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("🔎 Dashboard Filters")

# Customer Segment
segment_options = sorted(
    df["customer_segment"].dropna().unique()
)

selected_segments = st.sidebar.multiselect(
    "Customer Segment",
    options=segment_options,
    default=segment_options
)

# Category
category_options = sorted(
    df["category"].dropna().unique()
)

selected_categories = st.sidebar.multiselect(
    "Category",
    options=category_options,
    default=category_options
)

# City
city_options = sorted(
    df["city"].dropna().unique()
)

selected_cities = st.sidebar.multiselect(
    "City",
    options=city_options,
    default=city_options
)

# Payment Status
payment_options = sorted(
    df["payment_status"].dropna().unique()
)

selected_payments = st.sidebar.multiselect(
    "Payment Status",
    options=payment_options,
    default=payment_options
)

# --------------------------------------------------
# DATE FILTER
# --------------------------------------------------

valid_dates = df["order_date"].dropna()

if not valid_dates.empty:

    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    selected_dates = st.sidebar.date_input(
        "Order Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(selected_dates) == 2:
        start_date = pd.Timestamp(selected_dates[0])
        end_date = pd.Timestamp(selected_dates[1])

        date_filter = (
            (df["order_date"] >= start_date)
            & (df["order_date"] <= end_date)
        )

    else:
        date_filter = pd.Series(
            True,
            index=df.index
        )

else:

    date_filter = pd.Series(
        True,
        index=df.index
    )

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------

filtered_df = df[
    df["customer_segment"].isin(selected_segments)
    & df["category"].isin(selected_categories)
    & df["city"].isin(selected_cities)
    & df["payment_status"].isin(selected_payments)
    & date_filter
].copy()

# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------

total_revenue = filtered_df[
    "sales_after_discount"
].sum()

total_orders = filtered_df[
    "order_id"
].nunique()

total_quantity = filtered_df[
    "quantity"
].sum()

average_order_value = (
    total_revenue / total_orders
    if total_orders > 0
    else 0
)

paid_orders = (
    filtered_df["payment_status"]
    .eq("Paid")
    .sum()
)

paid_order_rate = (
    paid_orders / total_orders * 100
    if total_orders > 0
    else 0
)

refunded_orders = (
    filtered_df["payment_status"]
    .eq("Refunded")
    .sum()
)

refund_rate = (
    refunded_orders / total_orders * 100
    if total_orders > 0
    else 0
)

# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

st.subheader("Executive KPIs")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "💰 Total Revenue",
    f"₹{total_revenue:,.2f}"
)

col2.metric(
    "🛒 Total Orders",
    f"{total_orders:,}"
)

col3.metric(
    "📦 Quantity Sold",
    f"{total_quantity:,.0f}"
)

col4.metric(
    "💳 Average Order Value",
    f"₹{average_order_value:,.2f}"
)

# --------------------------------------------------
# SECOND KPI ROW
# --------------------------------------------------

col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "✅ Paid Order Rate",
    f"{paid_order_rate:.2f}%"
)

col6.metric(
    "↩️ Refund Rate",
    f"{refund_rate:.2f}%"
)

col7.metric(
    "🏷️ Avg Discount",
    f"{filtered_df['discount_pct'].mean():.2f}%"
    if not filtered_df.empty
    else "0.00%"
)

col8.metric(
    "📊 Filtered Records",
    f"{len(filtered_df):,}"
)

# --------------------------------------------------
# REVENUE TREND
# --------------------------------------------------

st.subheader("📈 Revenue Trend")

daily_revenue = (
    filtered_df
    .dropna(subset=["order_date"])
    .groupby("order_date")["sales_after_discount"]
    .sum()
    .reset_index()
)

if not daily_revenue.empty:

    fig_revenue = px.area(
        daily_revenue,
        x="order_date",
        y="sales_after_discount",
        title="Sales After Discount Over Time",
        labels={
            "order_date": "Order Date",
            "sales_after_discount": "Revenue (₹)"
        }
    )

    st.plotly_chart(
        fig_revenue,
        use_container_width=True
    )

else:

    st.info("No valid dates available for the selected filters.")

# --------------------------------------------------
# CATEGORY + SEGMENT
# --------------------------------------------------

col1, col2 = st.columns(2)

# Revenue by Category
with col1:

    st.subheader("📦 Revenue by Category")

    category_sales = (
        filtered_df
        .groupby("category")["sales_after_discount"]
        .sum()
        .reset_index()
        .sort_values(
            "sales_after_discount",
            ascending=False
        )
    )

    if not category_sales.empty:

        fig_category = px.bar(
            category_sales,
            x="category",
            y="sales_after_discount",
            title="Revenue by Category",
            labels={
                "category": "Category",
                "sales_after_discount": "Revenue (₹)"
            }
        )

        st.plotly_chart(
            fig_category,
            use_container_width=True
        )

# Revenue by Customer Segment
with col2:

    st.subheader("👥 Revenue by Customer Segment")

    segment_sales = (
        filtered_df
        .groupby("customer_segment")[
            "sales_after_discount"
        ]
        .sum()
        .reset_index()
    )

    if not segment_sales.empty:

        fig_segment = px.pie(
            segment_sales,
            names="customer_segment",
            values="sales_after_discount",
            title="Revenue by Customer Segment"
        )

        st.plotly_chart(
            fig_segment,
            use_container_width=True
        )

# --------------------------------------------------
# CITY + PAYMENT STATUS
# --------------------------------------------------

col1, col2 = st.columns(2)

# Revenue by City
with col1:

    st.subheader("📍 Revenue by City")

    city_sales = (
        filtered_df
        .groupby("city")["sales_after_discount"]
        .sum()
        .reset_index()
        .sort_values(
            "sales_after_discount",
            ascending=False
        )
    )

    if not city_sales.empty:

        fig_city = px.bar(
            city_sales,
            x="city",
            y="sales_after_discount",
            title="Revenue by City",
            labels={
                "city": "City",
                "sales_after_discount": "Revenue (₹)"
            }
        )

        st.plotly_chart(
            fig_city,
            use_container_width=True
        )

# Payment Status
with col2:

    st.subheader("💳 Payment Status")

    payment_summary = (
        filtered_df["payment_status"]
        .value_counts()
        .reset_index()
    )

    payment_summary.columns = [
        "payment_status",
        "orders"
    ]

    if not payment_summary.empty:

        fig_payment = px.bar(
            payment_summary,
            x="payment_status",
            y="orders",
            title="Orders by Payment Status",
            labels={
                "payment_status": "Payment Status",
                "orders": "Number of Orders"
            }
        )

        st.plotly_chart(
            fig_payment,
            use_container_width=True
        )

# --------------------------------------------------
# DATA TABLE
# --------------------------------------------------

st.subheader("📋 Filtered Order Data")

st.dataframe(
    filtered_df,
    use_container_width=True
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Retail Business KPI Dashboard | "
    "Built with Python, Streamlit, Pandas and Plotly"
)