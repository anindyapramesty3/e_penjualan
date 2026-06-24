import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

sns.set_style("whitegrid")

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Penjualan",
    page_icon="📊",
    layout="wide"
)

# ── Load Data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data_penjualan_bersih.csv")
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])
    return df

df = load_data()

# ── Sidebar Filter ────────────────────────────────────────────
st.sidebar.title("🔎 Filter Data")

min_date = df["Tanggal"].min()
max_date = df["Tanggal"].max()

date_input = st.sidebar.date_input(
    "Pilih Rentang Waktu",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_input, (list, tuple)) and len(date_input) == 2:
    start_date, end_date = date_input
else:
    start_date, end_date = min_date, max_date

start_date = pd.to_datetime(start_date)
end_date   = pd.to_datetime(end_date)

df_filtered = df[
    (df["Tanggal"] >= start_date) &
    (df["Tanggal"] <= end_date)
]

# ── Header ────────────────────────────────────────────────────
st.title("📊 Dashboard Penjualan")
st.caption(f"Periode: {start_date.date()} — {end_date.date()}")
st.divider()

# ── KPI Metrik ────────────────────────────────────────────────
st.subheader("📋 Ringkasan")

total_transaksi = df_filtered["No SO"].nunique()
total_omzet     = df_filtered["Total Tagihan"].sum()
rata_omzet      = total_omzet / total_transaksi if total_transaksi > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Transaksi", f"{total_transaksi:,}")
col2.metric("Total Omzet", f"Rp {total_omzet:,.0f}")
col3.metric("Rata-rata per Transaksi", f"Rp {rata_omzet:,.0f}")

st.divider()

# ── 1. Tren Penjualan per Bulan ───────────────────────────────
st.subheader("📈 Tren Penjualan per Bulan")

df_filtered["Bulan"] = df_filtered["Tanggal"].dt.to_period("M")
tren_bulanan = df_filtered.groupby("Bulan").agg(
    total_transaksi=("Total Tagihan", "count"),
    total_pendapatan=("Total Tagihan", "sum")
).reset_index()
tren_bulanan["Bulan"] = tren_bulanan["Bulan"].astype(str)

fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(12, 8))

ax[0].plot(tren_bulanan["Bulan"], tren_bulanan["total_transaksi"],
           marker="o", linewidth=2, color="#72BCD4")
ax[0].set_title("Jumlah Transaksi per Bulan", fontsize=14)
ax[0].set_ylabel("Jumlah Transaksi")
ax[0].tick_params(axis="x", rotation=45)

ax[1].plot(tren_bulanan["Bulan"], tren_bulanan["total_pendapatan"],
           marker="o", linewidth=2, color="#F4A460")
ax[1].set_title("Total Pendapatan per Bulan", fontsize=14)
ax[1].set_ylabel("Total Pendapatan (Rp)")
ax[1].tick_params(axis="x", rotation=45)

plt.tight_layout()
st.pyplot(fig)

# Insight tren bulanan
bulan_omzet_tertinggi     = tren_bulanan.loc[tren_bulanan["total_pendapatan"].idxmax()]
bulan_transaksi_tertinggi = tren_bulanan.loc[tren_bulanan["total_transaksi"].idxmax()]
bulan_omzet_terendah      = tren_bulanan.loc[tren_bulanan["total_pendapatan"].idxmin()]

st.caption(
    f"💡 Pendapatan tertinggi terjadi pada bulan **{bulan_omzet_tertinggi['Bulan']}** "
    f"sebesar **Rp {bulan_omzet_tertinggi['total_pendapatan']:,.0f}**. "
    f"Transaksi terbanyak pada bulan **{bulan_transaksi_tertinggi['Bulan']}** "
    f"dengan **{bulan_transaksi_tertinggi['total_transaksi']} transaksi**. "
    f"Bulan dengan pendapatan terendah adalah **{bulan_omzet_terendah['Bulan']}** "
    f"sebesar **Rp {bulan_omzet_terendah['total_pendapatan']:,.0f}**."
)

st.divider()

# ── 2. Top 10 Produk Terlaris ─────────────────────────────────
st.subheader("🏆 Top 10 Produk Terlaris")

top_produk = df_filtered.groupby("Nama Produk").agg(
    total_qty=("Qty", "sum")
).sort_values("total_qty", ascending=False).head(10).reset_index()

fig, ax = plt.subplots(figsize=(12, 6))
colors = ["#72BCD4"] + ["#D3D3D3"] * 9
sns.barplot(x="total_qty", y="Nama Produk", data=top_produk,
            palette=colors, ax=ax, hue="Nama Produk", legend=False)
ax.set_title("Top 10 Produk Terlaris (by Qty)", fontsize=14)
ax.set_xlabel("Total Qty")
ax.set_ylabel(None)
plt.tight_layout()
st.pyplot(fig)

# Insight produk
produk_terlaris = top_produk.iloc[0]
produk_ke2      = top_produk.iloc[1]

st.caption(
    f"💡 Produk terlaris adalah **{produk_terlaris['Nama Produk']}** "
    f"dengan total **{produk_terlaris['total_qty']:,.0f} qty** terjual. "
    f"Diikuti oleh **{produk_ke2['Nama Produk']}** "
    f"dengan **{produk_ke2['total_qty']:,.0f} qty**."
)

st.divider()

# ── 3. Omzet per Sales ────────────────────────────────────────
st.subheader("👨‍💼 Omzet per Sales")

omzet_sales = df_filtered.groupby("Nama Sales").agg(
    total_omzet=("Total Tagihan", "sum"),
    total_transaksi=("Total Tagihan", "count")
).reset_index()
omzet_sales["rata_per_transaksi"] = omzet_sales["total_omzet"] / omzet_sales["total_transaksi"]
omzet_sales = omzet_sales.sort_values("total_omzet", ascending=False)

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(omzet_sales) - 1)
    sns.barplot(x="total_omzet", y="Nama Sales", data=omzet_sales,
                palette=colors, ax=ax, hue="Nama Sales", legend=False)
    ax.set_title("Total Omzet per Sales", fontsize=13)
    ax.set_xlabel("Total Omzet (Rp)")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    omzet_sales_rata = omzet_sales.sort_values("rata_per_transaksi", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    colors2 = ["#72BCD4"] + ["#D3D3D3"] * (len(omzet_sales_rata) - 1)
    sns.barplot(x="rata_per_transaksi", y="Nama Sales", data=omzet_sales_rata,
                palette=colors2, ax=ax, hue="Nama Sales", legend=False)
    ax.set_title("Rata-rata Omzet per Transaksi", fontsize=13)
    ax.set_xlabel("Rata-rata (Rp)")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)

# Insight sales
sales_omzet_tertinggi = omzet_sales.iloc[0]
sales_omzet_terendah  = omzet_sales.iloc[-1]
sales_rata_tertinggi  = omzet_sales_rata.iloc[0]

st.caption(
    f"💡 Sales dengan omzet tertinggi adalah **{sales_omzet_tertinggi['Nama Sales']}** "
    f"sebesar **Rp {sales_omzet_tertinggi['total_omzet']:,.0f}** "
    f"dari **{sales_omzet_tertinggi['total_transaksi']} transaksi**. "
    f"Sales paling efisien per transaksi adalah **{sales_rata_tertinggi['Nama Sales']}** "
    f"dengan rata-rata **Rp {sales_rata_tertinggi['rata_per_transaksi']:,.0f} per transaksi**. "
    f"Sales dengan omzet terendah adalah **{sales_omzet_terendah['Nama Sales']}** "
    f"sebesar **Rp {sales_omzet_terendah['total_omzet']:,.0f}**."
)

st.divider()

# ── 4. Omzet per Kategori ─────────────────────────────────────
st.subheader("📊 Omzet per Kategori Produk")

omzet_kategori = df_filtered.groupby("Kategori Produk").agg(
    total_omzet=("Total Tagihan", "sum"),
    total_qty=("Qty", "sum")
).sort_values("total_omzet", ascending=False).reset_index()

fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#72BCD4"] + ["#D3D3D3"] * (len(omzet_kategori) - 1)
sns.barplot(x="total_omzet", y="Kategori Produk", data=omzet_kategori,
            palette=colors, ax=ax, hue="Kategori Produk", legend=False)
ax.set_title("Omzet per Kategori Produk", fontsize=14)
ax.set_xlabel("Total Omzet (Rp)")
ax.set_ylabel(None)
plt.tight_layout()
st.pyplot(fig)

# Insight kategori
kategori_tertinggi = omzet_kategori.iloc[0]
kategori_terendah  = omzet_kategori.iloc[-1]
pct_kategori_utama = kategori_tertinggi["total_omzet"] / omzet_kategori["total_omzet"].sum() * 100

st.caption(
    f"💡 Kategori **{kategori_tertinggi['Kategori Produk']}** mendominasi omzet "
    f"sebesar **Rp {kategori_tertinggi['total_omzet']:,.0f}** "
    f"({pct_kategori_utama:.1f}% dari total omzet). "
    f"Kategori dengan omzet terendah adalah **{kategori_terendah['Kategori Produk']}** "
    f"sebesar **Rp {kategori_terendah['total_omzet']:,.0f}**."
)

st.divider()

# ── 5. Status Pengiriman ──────────────────────────────────────
st.subheader("🚚 Status Pengiriman")

status_kirim = df_filtered["Status Pengiriman"].value_counts().reset_index()
status_kirim.columns = ["status", "jumlah"]

fig, ax = plt.subplots(figsize=(8, 4))
colors = ["#72BCD4"] + ["#D3D3D3"] * (len(status_kirim) - 1)
sns.barplot(x="jumlah", y="status", data=status_kirim,
            palette=colors, ax=ax, hue="status", legend=False)
ax.set_title("Status Pengiriman", fontsize=14)
ax.set_xlabel("Jumlah Transaksi")
ax.set_ylabel(None)
plt.tight_layout()
st.pyplot(fig)

# Insight status pengiriman
belum_terkirim   = status_kirim[status_kirim["status"] == "Belum Terkirim"]["jumlah"].values
diterima         = status_kirim[status_kirim["status"] == "Diterima Customer"]["jumlah"].values
total_status     = status_kirim["jumlah"].sum()

belum_terkirim_n = int(belum_terkirim[0]) if len(belum_terkirim) > 0 else 0
diterima_n       = int(diterima[0]) if len(diterima) > 0 else 0
pct_belum        = belum_terkirim_n / total_status * 100
pct_diterima     = diterima_n / total_status * 100

st.caption(
    f"💡 Dari total **{total_status} transaksi**, sebanyak **{belum_terkirim_n} transaksi "
    f"({pct_belum:.1f}%) belum terkirim** — perlu segera ditindaklanjuti! "
    f"Sedangkan **{diterima_n} transaksi ({pct_diterima:.1f}%)** sudah diterima customer."
)

st.divider()

# ── 6. Omzet per Provinsi ─────────────────────────────────────
st.subheader("🗺️ Omzet per Provinsi")

omzet_provinsi = df_filtered.groupby("Provinsi").agg(
    total_omzet=("Total Tagihan", "sum")
).sort_values("total_omzet", ascending=False).reset_index()

fig, ax = plt.subplots(figsize=(10, 8))
colors = ["#72BCD4"] + ["#D3D3D3"] * (len(omzet_provinsi) - 1)
sns.barplot(x="total_omzet", y="Provinsi", data=omzet_provinsi,
            palette=colors, ax=ax, hue="Provinsi", legend=False)
ax.set_title("Omzet per Provinsi", fontsize=14)
ax.set_xlabel("Total Omzet (Rp)")
ax.set_ylabel(None)
plt.tight_layout()
st.pyplot(fig)

# Insight provinsi
provinsi_tertinggi = omzet_provinsi.iloc[0]
provinsi_ke2       = omzet_provinsi.iloc[1]
pct_provinsi_utama = provinsi_tertinggi["total_omzet"] / omzet_provinsi["total_omzet"].sum() * 100

st.caption(
    f"💡 Provinsi dengan omzet tertinggi adalah **{provinsi_tertinggi['Provinsi']}** "
    f"sebesar **Rp {provinsi_tertinggi['total_omzet']:,.0f}** "
    f"({pct_provinsi_utama:.1f}% dari total omzet). "
    f"Diikuti oleh **{provinsi_ke2['Provinsi']}** "
    f"sebesar **Rp {provinsi_ke2['total_omzet']:,.0f}**."
)

st.divider()
st.caption("© Dashboard Penjualan 2026")
