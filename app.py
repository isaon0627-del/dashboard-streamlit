from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="購買ダッシュボード",
    page_icon="📊",
    layout="wide",
)

CSV_PATH = Path(__file__).parent / "date" / "sample-data.csv"
REQUIRED_COLUMNS = [
    "顧客ID",
    "年齢",
    "性別",
    "地域",
    "購入カテゴリー",
    "購入金額",
    "購入日",
    "支払方法",
]


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    df["購入日"] = pd.to_datetime(df["購入日"], errors="coerce")
    df["購入金額"] = pd.to_numeric(df["購入金額"], errors="coerce")
    df["年齢"] = pd.to_numeric(df["年齢"], errors="coerce")
    df = df.dropna(subset=["購入日", "購入金額", "年齢"])
    df["年月"] = df["購入日"].dt.to_period("M").astype(str)
    df["年代"] = pd.cut(
        df["年齢"],
        bins=[0, 19, 29, 39, 49, 59, 69, 200],
        labels=["~19", "20代", "30代", "40代", "50代", "60代", "70代+"],
    )
    return df


def format_yen(value: float) -> str:
    return f"¥{value:,.0f}"


st.title("購買ダッシュボード（sample-data.csv）")
st.caption("フィルタを変更しながら、売上構成・時系列・顧客属性を確認できます。")

if not CSV_PATH.exists():
    st.error(f"データファイルが見つかりません: {CSV_PATH}")
    st.stop()

try:
    data = load_data(CSV_PATH)
except Exception as exc:
    st.error(f"データ読み込みに失敗しました: {exc}")
    st.stop()


st.sidebar.header("フィルタ")

min_date = data["購入日"].min().date()
max_date = data["購入日"].max().date()
date_range = st.sidebar.date_input(
    "購入日",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

regions = st.sidebar.multiselect("地域", sorted(data["地域"].dropna().unique().tolist()))
categories = st.sidebar.multiselect(
    "購入カテゴリー", sorted(data["購入カテゴリー"].dropna().unique().tolist())
)
genders = st.sidebar.multiselect("性別", sorted(data["性別"].dropna().unique().tolist()))
payments = st.sidebar.multiselect("支払方法", sorted(data["支払方法"].dropna().unique().tolist()))
age_min, age_max = int(data["年齢"].min()), int(data["年齢"].max())
selected_age = st.sidebar.slider("年齢レンジ", age_min, age_max, (age_min, age_max))

filtered = data[
    (data["購入日"].dt.date >= start_date)
    & (data["購入日"].dt.date <= end_date)
    & (data["年齢"] >= selected_age[0])
    & (data["年齢"] <= selected_age[1])
]
if regions:
    filtered = filtered[filtered["地域"].isin(regions)]
if categories:
    filtered = filtered[filtered["購入カテゴリー"].isin(categories)]
if genders:
    filtered = filtered[filtered["性別"].isin(genders)]
if payments:
    filtered = filtered[filtered["支払方法"].isin(payments)]


if filtered.empty:
    st.warning("条件に一致するデータがありません。フィルタを調整してください。")
    st.stop()

# KPI
total_sales = filtered["購入金額"].sum()
avg_sales = filtered["購入金額"].mean()
txn_count = len(filtered)
monthly_avg = filtered.groupby("年月")["購入金額"].sum().mean()
home_appliance_ratio = (
    filtered.loc[filtered["購入カテゴリー"] == "家電", "購入金額"].sum() / total_sales * 100
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("総売上", format_yen(total_sales))
k2.metric("平均購入単価", format_yen(avg_sales))
k3.metric("取引件数", f"{txn_count:,}件")
k4.metric("月平均売上", format_yen(monthly_avg))
k5.metric("家電カテゴリ比率", f"{home_appliance_ratio:.1f}%")

st.divider()

# 集計
monthly_sales = filtered.groupby("年月", as_index=False)["購入金額"].sum().sort_values("年月")
monthly_count = filtered.groupby("年月", as_index=False)["顧客ID"].count().sort_values("年月")
monthly_count = monthly_count.rename(columns={"顧客ID": "件数"})
cat_sales = (
    filtered.groupby("購入カテゴリー", as_index=False)["購入金額"]
    .sum()
    .sort_values("購入金額", ascending=False)
)
region_sales = (
    filtered.groupby("地域", as_index=False)["購入金額"]
    .sum()
    .sort_values("購入金額", ascending=False)
)
payment_count = (
    filtered.groupby("支払方法", as_index=False)["顧客ID"]
    .count()
    .rename(columns={"顧客ID": "件数"})
)
age_sales = (
    filtered.groupby("年代", as_index=False)["購入金額"]
    .sum()
    .sort_values("購入金額", ascending=False)
)
age_avg = (
    filtered.groupby("年代", as_index=False)["購入金額"]
    .mean()
    .rename(columns={"購入金額": "平均購入金額"})
    .sort_values("平均購入金額", ascending=False)
)
gender_cat = filtered.pivot_table(
    index="性別",
    columns="購入カテゴリー",
    values="購入金額",
    aggfunc="sum",
    fill_value=0,
)


# 1段目
c1, c2 = st.columns(2)
with c1:
    fig_monthly_sales = px.line(
        monthly_sales,
        x="年月",
        y="購入金額",
        markers=True,
        title="月次売上推移",
    )
    st.plotly_chart(fig_monthly_sales, use_container_width=True)
with c2:
    fig_monthly_count = px.bar(monthly_count, x="年月", y="件数", title="月次件数推移")
    st.plotly_chart(fig_monthly_count, use_container_width=True)

# 2段目
c3, c4, c5 = st.columns(3)
with c3:
    fig_cat = px.bar(
        cat_sales,
        x="購入金額",
        y="購入カテゴリー",
        orientation="h",
        title="カテゴリ別売上",
    )
    st.plotly_chart(fig_cat, use_container_width=True)
with c4:
    fig_region = px.bar(region_sales, x="地域", y="購入金額", title="地域別売上")
    st.plotly_chart(fig_region, use_container_width=True)
with c5:
    fig_pay = px.pie(payment_count, values="件数", names="支払方法", hole=0.5, title="支払方法比率")
    st.plotly_chart(fig_pay, use_container_width=True)

# 3段目
c6, c7, c8 = st.columns(3)
with c6:
    fig_age_sales = px.bar(age_sales, x="年代", y="購入金額", title="年代別売上")
    st.plotly_chart(fig_age_sales, use_container_width=True)
with c7:
    fig_age_avg = px.bar(age_avg, x="年代", y="平均購入金額", title="年代別平均購入単価")
    st.plotly_chart(fig_age_avg, use_container_width=True)
with c8:
    fig_gender_cat = px.imshow(
        gender_cat,
        labels=dict(x="購入カテゴリー", y="性別", color="購入金額"),
        title="性別 × カテゴリ（売上）",
        text_auto=True,
        aspect="auto",
    )
    st.plotly_chart(fig_gender_cat, use_container_width=True)

# 4段目
c9, c10 = st.columns(2)
with c9:
    region_cat = filtered.pivot_table(
        index="地域",
        columns="購入カテゴリー",
        values="購入金額",
        aggfunc="sum",
        fill_value=0,
    )
    fig_region_cat = px.imshow(
        region_cat,
        labels=dict(x="購入カテゴリー", y="地域", color="購入金額"),
        title="地域 × カテゴリ（売上）",
        text_auto=True,
        aspect="auto",
    )
    st.plotly_chart(fig_region_cat, use_container_width=True)
with c10:
    fig_scatter = px.scatter(
        filtered,
        x="年齢",
        y="購入金額",
        color="購入カテゴリー",
        title="年齢 × 購入金額",
        opacity=0.7,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.subheader("明細データ")
st.caption(f"表示件数: {len(filtered):,} / {len(data):,}")
st.dataframe(
    filtered[
        ["顧客ID", "購入日", "年齢", "性別", "地域", "購入カテゴリー", "購入金額", "支払方法"]
    ].sort_values("購入日", ascending=False),
    use_container_width=True,
)

csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "フィルタ済みデータをCSVダウンロード",
    data=csv_bytes,
    file_name="filtered_sample_data.csv",
    mime="text/csv",
)
