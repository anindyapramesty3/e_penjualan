import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style='whitegrid')

st.set_page_config(page_title="Dashboard Penerimaan", page_icon="📦", layout="wide")

# ============================================
# LOAD DATA
# ============================================
@st.cache_data
def load_data():
    df = pd.read_csv("data_enerimaan_bersih.csv")
    df['Tanggal Penerimaan'] = pd.to_datetime(df['Tanggal Penerimaan'])
    return df

df = load_data()

st.title("📦 Dashboard Penerimaan Barang")
st.markdown("Analisis data penerimaan barang dari vendor")

# ============================================
# SIDEBAR FILTER
# ============================================
st.sidebar.header("Filter Data")

min_date = df['Tanggal Penerimaan'].min()
max_date = df['Tanggal Penerimaan'].max()

date_range = st.sidebar.date_input(
    "Rentang Tanggal Penerimaan",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

vendor_options = ["Semua Vendor"] + sorted(df['Nama Vendor'].unique().tolist())
selected_vendor = st.sidebar.selectbox("Vendor", vendor_options)

kategori_options = ["Semua Kategori"] + sorted(df['Kategori Produk'].unique().tolist())
selected_kategori = st.sidebar.selectbox("Kategori Produk", kategori_options)

# Terapkan filter
df_filtered = df.copy()

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_filtered[
        (df_filtered['Tanggal Penerimaan'] >= pd.Timestamp(start_date)) &
        (df_filtered['Tanggal Penerimaan'] <= pd.Timestamp(end_date))
    ]

if selected_vendor != "Semua Vendor":
    df_filtered = df_filtered[df_filtered['Nama Vendor'] == selected_vendor]

if selected_kategori != "Semua Kategori":
    df_filtered = df_filtered[df_filtered['Kategori Produk'] == selected_kategori]

# ============================================
# KEY METRICS
# ============================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Transaksi", f"{len(df_filtered)}")
with col2:
    st.metric("Total Qty Diterima", f"{df_filtered['Qty'].sum():,.0f}")
with col3:
    st.metric("Jumlah Vendor", f"{df_filtered['Nama Vendor'].nunique()}")
with col4:
    pct_lolos = (df_filtered['Kondisi Produk'] == 'Lolos').mean() * 100 if len(df_filtered) > 0 else 0
    st.metric("Persentase Lolos QC", f"{pct_lolos:.1f}%")

st.divider()

# ============================================
# CHART 1 & 2: Vendor & Kategori (berdampingan)
# ============================================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Total Qty per Vendor")
    vendor_qty = df_filtered.groupby('Nama Vendor')['Qty'].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(x=vendor_qty.values, y=vendor_qty.index, hue=vendor_qty.index,
                palette='Blues_r', legend=False, ax=ax)
    ax.set_xlabel("Total Qty")
    ax.set_ylabel("")
    st.pyplot(fig)

with col_right:
    st.subheader("Total Qty per Kategori Produk")
    kategori_qty = df_filtered.groupby('Kategori Produk')['Qty'].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(x=kategori_qty.index, y=kategori_qty.values, hue=kategori_qty.index,
                palette='Set2', legend=False, ax=ax)
    ax.set_ylabel("Total Qty")
    ax.set_xlabel("")
    plt.xticks(rotation=15)
    st.pyplot(fig)

st.divider()

# ============================================
# CHART 3: Tren Harian
# ============================================
st.subheader("Tren Total Qty Penerimaan Harian")
tren_harian = df_filtered.groupby('Tanggal Penerimaan').agg(
    total_qty=('Qty', 'sum')
).reset_index()

fig, ax = plt.subplots(figsize=(12, 5))
sns.lineplot(data=tren_harian, x='Tanggal Penerimaan', y='total_qty',
             marker='o', color='darkorange', ax=ax)
ax.set_ylabel("Total Qty")
ax.set_xlabel("Tanggal")
plt.xticks(rotation=45)
st.pyplot(fig)

st.divider()

# ============================================
# CHART 4 & 5: QC Status & Checklist Keuangan (berdampingan)
# ============================================
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Status QC Produk")
    qc_counts = df_filtered['Kondisi Produk'].value_counts()
    fig, ax = plt.subplots(figsize=(5, 5))
    colors = sns.color_palette('Set2')[:len(qc_counts)]
    ax.pie(qc_counts.values, labels=qc_counts.index, autopct='%1.1f%%', colors=colors)
    st.pyplot(fig)

with col_right2:
    st.subheader("Status Checklist Keuangan")
    checklist_counts = df_filtered['Checklist Keuangan'].value_counts()
    fig, ax = plt.subplots(figsize=(5, 5))
    colors = sns.color_palette('Pastel1')[:len(checklist_counts)]
    ax.pie(checklist_counts.values, labels=checklist_counts.index, autopct='%1.1f%%', colors=colors)
    st.pyplot(fig)

st.divider()

# ============================================
# DATA TABLE
# ============================================
st.subheader("Detail Data Penerimaan")
st.dataframe(df_filtered, use_container_width=True)