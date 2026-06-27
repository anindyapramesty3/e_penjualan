import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

sns.set_style("whitegrid")

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Penjualan, Pembelian & Penerimaan",
    page_icon="📊",
    layout="wide"
)

# ── Load Data ─────────────────────────────────────────────────
@st.cache_data
def load_penjualan():
    df = pd.read_csv("data_penjualan_bersih.csv")
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])
    return df

@st.cache_data
def load_pembelian():
    df = pd.read_csv("data_pembelian_bersih.csv")
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])
    return df

@st.cache_data
def load_penerimaan():
    df = pd.read_csv("data_penerimaan_bersih.csv")
    df["Tanggal Penerimaan"] = pd.to_datetime(df["Tanggal Penerimaan"])
    return df

df_penjualan = load_penjualan()
df_pembelian = load_pembelian()
df_penerimaan = load_penerimaan()

# ── Sidebar Filter ────────────────────────────────────────────
st.sidebar.title("🔎 Filter Data")

min_date = min(
    df_penjualan["Tanggal"].min(),
    df_pembelian["Tanggal"].min(),
    df_penerimaan["Tanggal Penerimaan"].min()
)
max_date = max(
    df_penjualan["Tanggal"].max(),
    df_pembelian["Tanggal"].max(),
    df_penerimaan["Tanggal Penerimaan"].max()
)

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

df_jual = df_penjualan[
    (df_penjualan["Tanggal"] >= start_date) &
    (df_penjualan["Tanggal"] <= end_date)
].copy()

df_beli = df_pembelian[
    (df_pembelian["Tanggal"] >= start_date) &
    (df_pembelian["Tanggal"] <= end_date)
].copy()

df_terima = df_penerimaan[
    (df_penerimaan["Tanggal Penerimaan"] >= start_date) &
    (df_penerimaan["Tanggal Penerimaan"] <= end_date)
].copy()

# ── Header ────────────────────────────────────────────────────
st.title("📊 Dashboard Penjualan, Pembelian & Penerimaan")
st.caption(f"Periode: {start_date.date()} — {end_date.date()}")

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 E-Penjualan", "🛒 E-Pembelian", "📦 E-Penerimaan"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — PENJUALAN
# ══════════════════════════════════════════════════════════════
with tab1:

    # KPI
    st.subheader("📋 Ringkasan Penjualan")
    total_transaksi_jual = df_jual["No SO"].nunique()
    total_omzet          = df_jual["Total Tagihan"].sum()
    rata_omzet           = total_omzet / total_transaksi_jual if total_transaksi_jual > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transaksi", f"{total_transaksi_jual:,}")
    col2.metric("Total Omzet", f"Rp {total_omzet:,.0f}")
    col3.metric("Rata-rata per Transaksi", f"Rp {rata_omzet:,.0f}")
    st.divider()

    # 1. Tren Penjualan per Bulan
    st.subheader("📈 Tren Penjualan per Bulan")
    df_jual["Bulan"] = df_jual["Tanggal"].dt.to_period("M")
    tren_jual = df_jual.groupby("Bulan").agg(
        total_transaksi=("Total Tagihan", "count"),
        total_pendapatan=("Total Tagihan", "sum")
    ).reset_index()
    tren_jual["Bulan"] = tren_jual["Bulan"].astype(str)

    fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(12, 8))
    ax[0].plot(tren_jual["Bulan"], tren_jual["total_transaksi"],
               marker="o", linewidth=2, color="#72BCD4")
    ax[0].set_title("Jumlah Transaksi per Bulan", fontsize=14)
    ax[0].set_ylabel("Jumlah Transaksi")
    ax[0].tick_params(axis="x", rotation=45)

    ax[1].plot(tren_jual["Bulan"], tren_jual["total_pendapatan"],
               marker="o", linewidth=2, color="#F4A460")
    ax[1].set_title("Total Pendapatan per Bulan", fontsize=14)
    ax[1].set_ylabel("Total Pendapatan (Rp)")
    ax[1].tick_params(axis="x", rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

    bulan_omzet_tertinggi     = tren_jual.loc[tren_jual["total_pendapatan"].idxmax()]
    bulan_transaksi_tertinggi = tren_jual.loc[tren_jual["total_transaksi"].idxmax()]
    st.caption(
        f"💡 Pendapatan tertinggi pada bulan **{bulan_omzet_tertinggi['Bulan']}** "
        f"sebesar **Rp {bulan_omzet_tertinggi['total_pendapatan']:,.0f}**. "
        f"Transaksi terbanyak pada bulan **{bulan_transaksi_tertinggi['Bulan']}** "
        f"dengan **{bulan_transaksi_tertinggi['total_transaksi']} transaksi**."
    )
    st.divider()

    # 2. Top 10 Produk Terlaris
    st.subheader("🏆 Top 10 Produk Terlaris")
    top_produk_jual = df_jual.groupby("Nama Produk").agg(
        total_qty=("Qty", "sum")
    ).sort_values("total_qty", ascending=False).head(10).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#72BCD4"] + ["#D3D3D3"] * 9
    sns.barplot(x="total_qty", y="Nama Produk", data=top_produk_jual,
                palette=colors, hue="Nama Produk", legend=False, ax=ax)
    ax.set_title("Top 10 Produk Terlaris (by Qty)", fontsize=14)
    ax.set_xlabel("Total Qty")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption(
        f"💡 Produk terlaris adalah **{top_produk_jual.iloc[0]['Nama Produk']}** "
        f"dengan **{top_produk_jual.iloc[0]['total_qty']:,.0f} qty** terjual."
    )
    st.divider()

    # 3. Omzet per Sales
    st.subheader("👨‍💼 Omzet per Sales")
    omzet_sales = df_jual.groupby("Nama Sales").agg(
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
                    palette=colors, hue="Nama Sales", legend=False, ax=ax)
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
                    palette=colors2, hue="Nama Sales", legend=False, ax=ax)
        ax.set_title("Rata-rata Omzet per Transaksi", fontsize=13)
        ax.set_xlabel("Rata-rata (Rp)")
        ax.set_ylabel(None)
        plt.tight_layout()
        st.pyplot(fig)

    st.caption(
        f"💡 Sales dengan omzet tertinggi adalah **{omzet_sales.iloc[0]['Nama Sales']}** "
        f"sebesar **Rp {omzet_sales.iloc[0]['total_omzet']:,.0f}**. "
        f"Sales paling efisien per transaksi adalah **{omzet_sales_rata.iloc[0]['Nama Sales']}** "
        f"dengan rata-rata **Rp {omzet_sales_rata.iloc[0]['rata_per_transaksi']:,.0f} per transaksi**."
    )
    st.divider()

    # 4. Omzet per Kategori
    st.subheader("📊 Omzet per Kategori Produk")
    omzet_kategori_jual = df_jual.groupby("Kategori Produk").agg(
        total_omzet=("Total Tagihan", "sum")
    ).sort_values("total_omzet", ascending=False).reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(omzet_kategori_jual) - 1)
    sns.barplot(x="total_omzet", y="Kategori Produk", data=omzet_kategori_jual,
                palette=colors, hue="Kategori Produk", legend=False, ax=ax)
    ax.set_title("Omzet per Kategori Produk", fontsize=14)
    ax.set_xlabel("Total Omzet (Rp)")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)

    pct = omzet_kategori_jual.iloc[0]["total_omzet"] / omzet_kategori_jual["total_omzet"].sum() * 100
    st.caption(
        f"💡 Kategori **{omzet_kategori_jual.iloc[0]['Kategori Produk']}** mendominasi "
        f"sebesar **Rp {omzet_kategori_jual.iloc[0]['total_omzet']:,.0f}** "
        f"({pct:.1f}% dari total omzet)."
    )
    st.divider()

    # 5. Status Pengiriman Penjualan
    st.subheader("🚚 Status Pengiriman")
    status_jual = df_jual["Status Pengiriman"].value_counts().reset_index()
    status_jual.columns = ["status", "jumlah"]

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(status_jual) - 1)
    sns.barplot(x="jumlah", y="status", data=status_jual,
                palette=colors, hue="status", legend=False, ax=ax)
    ax.set_title("Status Pengiriman Penjualan", fontsize=14)
    ax.set_xlabel("Jumlah Transaksi")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)

    belum = status_jual[status_jual["status"] == "Belum Terkirim"]["jumlah"].values
    belum_n = int(belum[0]) if len(belum) > 0 else 0
    pct_belum = belum_n / status_jual["jumlah"].sum() * 100
    st.caption(
        f"💡 Sebanyak **{belum_n} transaksi ({pct_belum:.1f}%) belum terkirim** "
        f"— perlu segera ditindaklanjuti!"
    )
    st.divider()

    # 6. Omzet per Provinsi
    st.subheader("🗺️ Omzet per Provinsi")
    omzet_provinsi_jual = df_jual.groupby("Provinsi").agg(
        total_omzet=("Total Tagihan", "sum")
    ).sort_values("total_omzet", ascending=False).reset_index()

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(omzet_provinsi_jual) - 1)
    sns.barplot(x="total_omzet", y="Provinsi", data=omzet_provinsi_jual,
                palette=colors, hue="Provinsi", legend=False, ax=ax)
    ax.set_title("Omzet per Provinsi", fontsize=14)
    ax.set_xlabel("Total Omzet (Rp)")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption(
        f"💡 Provinsi dengan omzet tertinggi adalah **{omzet_provinsi_jual.iloc[0]['Provinsi']}** "
        f"sebesar **Rp {omzet_provinsi_jual.iloc[0]['total_omzet']:,.0f}**."
    )

# ══════════════════════════════════════════════════════════════
# TAB 2 — PEMBELIAN
# ══════════════════════════════════════════════════════════════
with tab2:

    # KPI
    st.subheader("📋 Ringkasan Pembelian")
    total_transaksi_beli = len(df_beli)
    total_pembelian      = df_beli["Jumlah Harga"].sum()
    total_hutang         = df_beli["Hutang Vendor"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transaksi", f"{total_transaksi_beli:,}")
    col2.metric("Total Pembelian", f"Rp {total_pembelian:,.0f}")
    col3.metric("Total Hutang Vendor", f"Rp {total_hutang:,.0f}")
    st.divider()

    # 1. Tren Pembelian per Bulan
    st.subheader("📈 Tren Pembelian per Bulan")
    df_beli["Bulan"] = df_beli["Tanggal"].dt.to_period("M")
    tren_beli = df_beli.groupby("Bulan").agg(
        total_transaksi=("Jumlah Harga", "count"),
        total_pembelian=("Jumlah Harga", "sum")
    ).reset_index()
    tren_beli["Bulan"] = tren_beli["Bulan"].astype(str)

    fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(12, 8))
    ax[0].plot(tren_beli["Bulan"], tren_beli["total_transaksi"],
               marker="o", linewidth=2, color="#72BCD4")
    ax[0].set_title("Jumlah Transaksi Pembelian per Bulan", fontsize=14)
    ax[0].set_ylabel("Jumlah Transaksi")
    ax[0].tick_params(axis="x", rotation=45)

    ax[1].plot(tren_beli["Bulan"], tren_beli["total_pembelian"],
               marker="o", linewidth=2, color="#F4A460")
    ax[1].set_title("Total Pembelian per Bulan", fontsize=14)
    ax[1].set_ylabel("Total Pembelian (Rp)")
    ax[1].tick_params(axis="x", rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

    bulan_beli_tertinggi = tren_beli.loc[tren_beli["total_pembelian"].idxmax()]
    st.caption(
        f"💡 Pembelian tertinggi pada bulan **{bulan_beli_tertinggi['Bulan']}** "
        f"sebesar **Rp {bulan_beli_tertinggi['total_pembelian']:,.0f}**."
    )
    st.divider()

    # 2. Top 10 Vendor
    st.subheader("🏪 Top 10 Vendor Pembelian Terbesar")
    top_vendor = df_beli.groupby("Nama Vendor (PIC)").agg(
        total_pembelian=("Jumlah Harga", "sum"),
        total_transaksi=("Jumlah Harga", "count")
    ).sort_values("total_pembelian", ascending=False).head(10).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#72BCD4"] + ["#D3D3D3"] * 9
    sns.barplot(x="total_pembelian", y="Nama Vendor (PIC)", data=top_vendor,
                palette=colors, hue="Nama Vendor (PIC)", legend=False, ax=ax)
    ax.set_title("Top 10 Vendor Pembelian Terbesar", fontsize=14)
    ax.set_xlabel("Total Pembelian (Rp)")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption(
        f"💡 Vendor dengan pembelian terbesar adalah **{top_vendor.iloc[0]['Nama Vendor (PIC)']}** "
        f"sebesar **Rp {top_vendor.iloc[0]['total_pembelian']:,.0f}**."
    )
    st.divider()

    # 3. Pembelian per Kategori
    st.subheader("📊 Pembelian per Kategori Produk")
    pembelian_kategori = df_beli.groupby("Kategori Produk").agg(
        total_pembelian=("Jumlah Harga", "sum")
    ).sort_values("total_pembelian", ascending=False).reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(pembelian_kategori) - 1)
    sns.barplot(x="total_pembelian", y="Kategori Produk", data=pembelian_kategori,
                palette=colors, hue="Kategori Produk", legend=False, ax=ax)
    ax.set_title("Pembelian per Kategori Produk", fontsize=14)
    ax.set_xlabel("Total Pembelian (Rp)")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)

    pct_beli = pembelian_kategori.iloc[0]["total_pembelian"] / pembelian_kategori["total_pembelian"].sum() * 100
    st.caption(
        f"💡 Kategori **{pembelian_kategori.iloc[0]['Kategori Produk']}** mendominasi pembelian "
        f"sebesar **Rp {pembelian_kategori.iloc[0]['total_pembelian']:,.0f}** "
        f"({pct_beli:.1f}% dari total pembelian)."
    )
    st.divider()

    # 4. Status Pengiriman Pembelian
    st.subheader("🚚 Status Pengiriman Pembelian")
    status_beli = df_beli["Status Pengiriman"].value_counts().reset_index()
    status_beli.columns = ["status", "jumlah"]

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(status_beli) - 1)
    sns.barplot(x="jumlah", y="status", data=status_beli,
                palette=colors, hue="status", legend=False, ax=ax)
    ax.set_title("Status Pengiriman Pembelian", fontsize=14)
    ax.set_xlabel("Jumlah Transaksi")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)

    belum_beli = status_beli[status_beli["status"] == "Belum Diterima Futake"]["jumlah"].values
    belum_beli_n = int(belum_beli[0]) if len(belum_beli) > 0 else 0
    pct_belum_beli = belum_beli_n / status_beli["jumlah"].sum() * 100
    st.caption(
        f"💡 Sebanyak **{belum_beli_n} transaksi ({pct_belum_beli:.1f}%) belum diterima** "
        f"— perlu segera ditindaklanjuti!"
    )
    st.divider()

    # 5. Hutang Vendor Outstanding
    st.subheader("💰 Hutang Vendor Outstanding")
    hutang_vendor = df_beli.groupby("Nama Vendor (PIC)").agg(
        total_hutang=("Hutang Vendor", "sum")
    ).sort_values("total_hutang", ascending=False).reset_index()
    hutang_vendor = hutang_vendor[hutang_vendor["total_hutang"] > 0]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(hutang_vendor) - 1)
    sns.barplot(x="total_hutang", y="Nama Vendor (PIC)", data=hutang_vendor,
                palette=colors, hue="Nama Vendor (PIC)", legend=False, ax=ax)
    ax.set_title("Hutang Vendor Outstanding", fontsize=14)
    ax.set_xlabel("Total Hutang (Rp)")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption(
        f"💡 Vendor dengan hutang terbesar adalah **{hutang_vendor.iloc[0]['Nama Vendor (PIC)']}** "
        f"sebesar **Rp {hutang_vendor.iloc[0]['total_hutang']:,.0f}**."
    )
    st.divider()

    # 6. Top 10 Produk Terbanyak Dibeli
    st.subheader("🏆 Top 10 Produk Terbanyak Dibeli")
    top_produk_beli = df_beli.groupby("Nama Produk").agg(
        total_qty=("Qty", "sum")
    ).sort_values("total_qty", ascending=False).head(10).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#72BCD4"] + ["#D3D3D3"] * 9
    sns.barplot(x="total_qty", y="Nama Produk", data=top_produk_beli,
                palette=colors, hue="Nama Produk", legend=False, ax=ax)
    ax.set_title("Top 10 Produk Terbanyak Dibeli (by Qty)", fontsize=14)
    ax.set_xlabel("Total Qty")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption(
        f"💡 Produk yang paling banyak dibeli adalah **{top_produk_beli.iloc[0]['Nama Produk']}** "
        f"dengan **{top_produk_beli.iloc[0]['total_qty']:,.0f} qty**."
    )
    st.divider()

    # 7. Pembelian per Sales
    st.subheader("👨‍💼 Pembelian per Sales")
    pembelian_sales = df_beli.groupby("Nama Sales").agg(
        total_pembelian=("Jumlah Harga", "sum"),
        total_transaksi=("Jumlah Harga", "count")
    ).sort_values("total_pembelian", ascending=False).reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(pembelian_sales) - 1)
    sns.barplot(x="total_pembelian", y="Nama Sales", data=pembelian_sales,
                palette=colors, hue="Nama Sales", legend=False, ax=ax)
    ax.set_title("Total Pembelian per Sales", fontsize=14)
    ax.set_xlabel("Total Pembelian (Rp)")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption(
        f"💡 Sales dengan pembelian terbesar adalah **{pembelian_sales.iloc[0]['Nama Sales']}** "
        f"sebesar **Rp {pembelian_sales.iloc[0]['total_pembelian']:,.0f}**."
    )
    st.divider()

    # 8. Metode Pembayaran
    st.subheader("💳 Metode Pembayaran")
    metode_bayar = df_beli["Metode Pembayaran"].value_counts().reset_index()
    metode_bayar.columns = ["metode", "jumlah"]

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(metode_bayar) - 1)
    sns.barplot(x="jumlah", y="metode", data=metode_bayar,
                palette=colors, hue="metode", legend=False, ax=ax)
    ax.set_title("Metode Pembayaran", fontsize=14)
    ax.set_xlabel("Jumlah Transaksi")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption(
        f"💡 Metode pembayaran yang paling banyak digunakan adalah "
        f"**{metode_bayar.iloc[0]['metode']}** "
        f"dengan **{metode_bayar.iloc[0]['jumlah']} transaksi**."
    )

# ══════════════════════════════════════════════════════════════
# TAB 3 — PENERIMAAN
# ══════════════════════════════════════════════════════════════
with tab3:

    # KPI
    st.subheader("📋 Ringkasan Penerimaan")
    total_transaksi_terima = len(df_terima)
    total_qty_terima       = df_terima["Qty"].sum()
    pct_lolos_qc            = (df_terima["Kondisi Produk"] == "Lolos").mean() * 100 if total_transaksi_terima > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transaksi", f"{total_transaksi_terima:,}")
    col2.metric("Total Qty Diterima", f"{total_qty_terima:,.0f}")
    col3.metric("Persentase Lolos QC", f"{pct_lolos_qc:.1f}%")
    st.divider()

    # 1. Tren Penerimaan per Bulan
    st.subheader("📈 Tren Penerimaan per Bulan")
    df_terima["Bulan"] = df_terima["Tanggal Penerimaan"].dt.to_period("M")
    tren_terima = df_terima.groupby("Bulan").agg(
        total_transaksi=("Qty", "count"),
        total_qty=("Qty", "sum")
    ).reset_index()
    tren_terima["Bulan"] = tren_terima["Bulan"].astype(str)

    fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(12, 8))
    ax[0].plot(tren_terima["Bulan"], tren_terima["total_transaksi"],
               marker="o", linewidth=2, color="#72BCD4")
    ax[0].set_title("Jumlah Transaksi Penerimaan per Bulan", fontsize=14)
    ax[0].set_ylabel("Jumlah Transaksi")
    ax[0].tick_params(axis="x", rotation=45)

    ax[1].plot(tren_terima["Bulan"], tren_terima["total_qty"],
               marker="o", linewidth=2, color="#F4A460")
    ax[1].set_title("Total Qty Diterima per Bulan", fontsize=14)
    ax[1].set_ylabel("Total Qty")
    ax[1].tick_params(axis="x", rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

    bulan_qty_tertinggi = tren_terima.loc[tren_terima["total_qty"].idxmax()]
    st.caption(
        f"💡 Qty penerimaan tertinggi pada bulan **{bulan_qty_tertinggi['Bulan']}** "
        f"sebesar **{bulan_qty_tertinggi['total_qty']:,.0f} unit**."
    )
    st.divider()

    # 2. Top 10 Vendor Penerimaan Terbesar
    st.subheader("🏪 Top 10 Vendor Penerimaan Terbesar")
    top_vendor_terima = df_terima.groupby("Nama Vendor").agg(
        total_qty=("Qty", "sum"),
        total_transaksi=("Qty", "count")
    ).sort_values("total_qty", ascending=False).head(10).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(top_vendor_terima) - 1)
    sns.barplot(x="total_qty", y="Nama Vendor", data=top_vendor_terima,
                palette=colors, hue="Nama Vendor", legend=False, ax=ax)
    ax.set_title("Top 10 Vendor Penerimaan Terbesar (by Qty)", fontsize=14)
    ax.set_xlabel("Total Qty")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption(
        f"💡 Vendor dengan penerimaan terbesar adalah **{top_vendor_terima.iloc[0]['Nama Vendor']}** "
        f"dengan **{top_vendor_terima.iloc[0]['total_qty']:,.0f} unit**."
    )
    st.divider()

    # 3. Penerimaan per Kategori Produk
    st.subheader("📊 Penerimaan per Kategori Produk")
    kategori_terima = df_terima.groupby("Kategori Produk").agg(
        total_qty=("Qty", "sum")
    ).sort_values("total_qty", ascending=False).reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(kategori_terima) - 1)
    sns.barplot(x="total_qty", y="Kategori Produk", data=kategori_terima,
                palette=colors, hue="Kategori Produk", legend=False, ax=ax)
    ax.set_title("Penerimaan per Kategori Produk", fontsize=14)
    ax.set_xlabel("Total Qty")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)

    pct_kategori = kategori_terima.iloc[0]["total_qty"] / kategori_terima["total_qty"].sum() * 100
    st.caption(
        f"💡 Kategori **{kategori_terima.iloc[0]['Kategori Produk']}** mendominasi penerimaan "
        f"sebesar **{kategori_terima.iloc[0]['total_qty']:,.0f} unit** "
        f"({pct_kategori:.1f}% dari total qty diterima)."
    )
    st.divider()

    # 4. Status Kondisi Produk (QC)
    st.subheader("✅ Status Kondisi Produk (QC)")
    qc_terima = df_terima["Kondisi Produk"].value_counts().reset_index()
    qc_terima.columns = ["status", "jumlah"]

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(6, 5))
        colors = ["#72BCD4"] + ["#D3D3D3"] * (len(qc_terima) - 1)
        ax.pie(qc_terima["jumlah"], labels=qc_terima["status"], autopct="%1.1f%%", colors=colors)
        ax.set_title("Persentase Status QC", fontsize=13)
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots(figsize=(6, 5))
        colors = ["#72BCD4"] + ["#D3D3D3"] * (len(qc_terima) - 1)
        sns.barplot(x="jumlah", y="status", data=qc_terima,
                    palette=colors, hue="status", legend=False, ax=ax)
        ax.set_title("Jumlah Produk per Status QC", fontsize=13)
        ax.set_xlabel("Jumlah Produk")
        ax.set_ylabel(None)
        plt.tight_layout()
        st.pyplot(fig)

    tidak_lolos = qc_terima[qc_terima["status"] == "Tidak Lolos"]["jumlah"].values
    tidak_lolos_n = int(tidak_lolos[0]) if len(tidak_lolos) > 0 else 0
    st.caption(
        f"💡 Sebanyak **{tidak_lolos_n} produk tidak lolos QC** dari total "
        f"**{qc_terima['jumlah'].sum()} produk** yang diperiksa."
    )
    st.divider()

    # 5. Status Checklist Keuangan
    st.subheader("💰 Status Checklist Keuangan")
    checklist_terima = df_terima["Checklist Keuangan"].value_counts().reset_index()
    checklist_terima.columns = ["status", "jumlah"]

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#72BCD4"] + ["#D3D3D3"] * (len(checklist_terima) - 1)
    sns.barplot(x="jumlah", y="status", data=checklist_terima,
                palette=colors, hue="status", legend=False, ax=ax)
    ax.set_title("Status Checklist Keuangan", fontsize=14)
    ax.set_xlabel("Jumlah Transaksi")
    ax.set_ylabel(None)
    plt.tight_layout()
    st.pyplot(fig)

    belum_checklist = checklist_terima[checklist_terima["status"] == False]["jumlah"].values
    belum_checklist_n = int(belum_checklist[0]) if len(belum_checklist) > 0 else 0
    pct_belum_checklist = belum_checklist_n / checklist_terima["jumlah"].sum() * 100
    st.caption(
        f"💡 Sebanyak **{belum_checklist_n} transaksi ({pct_belum_checklist:.1f}%) belum "
        f"diverifikasi keuangan** — perlu segera ditindaklanjuti!"
    )

st.divider()
st.caption("© Dashboard Penjualan, Pembelian & Penerimaan 2026")
