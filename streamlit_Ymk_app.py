import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import date

st.set_page_config(page_title="WEB GACOR EDU", page_icon="🔥", layout="wide")

st.markdown("""
<style>
.block-container{padding-top:2.2rem;padding-bottom:2rem}

/* header bar */
.topbar{
  border-radius:18px;
  padding:14px 16px;
  margin-bottom:16px;
  background:linear-gradient(135deg,rgba(99,102,241,.22),rgba(34,197,94,.18));
  border:1px solid rgba(255,255,255,.10);
}
.brand{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.logo{
  width:42px;height:42px;border-radius:14px;
  display:flex;align-items:center;justify-content:center;
  font-weight:900;font-size:20px;
  background:linear-gradient(135deg,#6366f1,#22c55e);
  border:1px solid rgba(255,255,255,.14);
}
.badge{
  display:inline-block;margin-left:6px;
  padding:3px 10px;border-radius:999px;
  background:rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.12);
  font-size:.75rem;opacity:.95;
}
.small{font-size:.9rem;opacity:.88}

/* KPI */
.kpi{
  border-radius:16px;
  padding:14px 16px;
  background:rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.09);
}
.kpi-t{font-size:.85rem;opacity:.85}
.kpi-v{font-size:1.65rem;font-weight:850;margin-top:2px}
.kpi-d{font-size:.9rem;opacity:.85}
</style>
""", unsafe_allow_html=True)

np.random.seed(12)
nama = ["Alya","Bima","Citra","Dimas","Eka","Fahri","Gita","Hana","Indra","Jihan","Kevin","Laras","Miko","Nadia","Oka","Putri","Raka","Salsa","Tegar","Vina"]
jurusan = ["RPL","TKJ","AKL"]
bulan = ["Jan","Feb","Mar","Apr","Mei","Jun"]

df = pd.DataFrame({
    "Nama": np.random.choice(nama, 240),
    "Jurusan": np.random.choice(jurusan, 240, p=[0.42,0.35,0.23]),
    "Bulan": np.random.choice(bulan, 240),
    "Nilai_Ujian": np.random.normal(79,7.5,240).clip(40,100).round().astype(int),
    "Kehadiran_%": np.random.normal(92,4.2,240).clip(70,100).round().astype(int),
})

st.sidebar.header("⚙️ Filter")
pj = st.sidebar.multiselect("Jurusan", jurusan, jurusan)
pb = st.sidebar.multiselect("Bulan", bulan, bulan)
nilai = st.sidebar.slider("Nilai", 40, 100, (60, 95))
hadir = st.sidebar.slider("Kehadiran (%)", 70, 100, (85, 100))
hide_outlier = st.sidebar.toggle("Sembunyikan Outlier (nilai < 50)", value=False)

data = df[
    (df["Jurusan"].isin(pj)) &
    (df["Bulan"].isin(pb)) &
    (df["Nilai_Ujian"].between(*nilai)) &
    (df["Kehadiran_%"].between(*hadir))
].copy()
if hide_outlier:
    data = data[data["Nilai_Ujian"] >= 50].copy()

st.sidebar.divider()
st.sidebar.download_button(
    "⬇️ Download CSV",
    data=data.to_csv(index=False).encode("utf-8"),
    file_name="web_gacor_edu.csv",
    mime="text/csv"
)

st.markdown(f"""
<div class="topbar">
  <div class="brand">
    <div class="logo">🔥</div>
    <div>
      <div style="font-weight:900;letter-spacing:.3px;">WEB GACOR EDU
        <span class="badge">Streamlit</span>
        <span class="badge">Pendidikan</span>
      </div>
      <div class="small">{date.today().strftime("%d %b %Y")} • Baris: <b>{len(data):,}</b> • Jurusan aktif: <b>{data["Jurusan"].nunique()}</b></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# i. TITLE
st.title("🎓 EduStat — Dashboard Pendidikan")

# ii. HEADER
st.header("Ringkasan Data Siswa & Program Sekolah")

# iii. SUBHEADER
st.subheader("Tujuan")

# vi. TEXT (paragraf)
st.write("Halaman ini menampilkan komponen Streamlit lengkap dengan data pendidikan simulasi yang dapat difilter melalui sidebar.")

# iv. CAPTION
st.caption("Tugas Pertemuan 12 — Title, Header, Subheader, Caption, Code, Text, DataFrame, Chart.")

st.divider()

# v. CODE
st.subheader("Potongan Kode")
st.code(
"""import streamlit as st
import pandas as pd
import altair as alt

st.title("Title")
st.header("Header")
st.subheader("Subheader")
st.caption("Caption")

st.dataframe(df)
st.altair_chart(chart, use_container_width=True)
""",
language="python"
)

st.divider()

# vii. DATA DISPLAY (tabel/dataframe)
st.subheader("Tabel / DataFrame")
st.dataframe(
    data.sort_values(["Jurusan","Bulan","Nilai_Ujian"], ascending=[True, True, False]),
    use_container_width=True,
    height=360
)

st.divider()

# vii. DATA DISPLAY (chart)
st.subheader("Chart")

if len(data) == 0:
    st.warning("Data kosong setelah filter.")
else:
    agg = (data.groupby("Bulan", as_index=False)
           .agg(Rata2_Nilai=("Nilai_Ujian","mean"),
                Jumlah=("Nilai_Ujian","size")))
    agg["Bulan"] = pd.Categorical(agg["Bulan"], categories=bulan, ordered=True)
    agg = agg.sort_values("Bulan")

    line = alt.Chart(agg).mark_line(point=True).encode(
        x=alt.X("Bulan:N", sort=bulan, title="Bulan"),
        y=alt.Y("Rata2_Nilai:Q", title="Rata-rata Nilai"),
        tooltip=["Bulan:N", alt.Tooltip("Rata2_Nilai:Q", format=".2f"), "Jumlah:Q"]
    ).properties(height=280)

    bar = alt.Chart(agg).mark_bar().encode(
        x=alt.X("Bulan:N", sort=bulan, title="Bulan"),
        y=alt.Y("Jumlah:Q", title="Jumlah Data"),
        tooltip=["Bulan:N", "Jumlah:Q"]
    ).properties(height=280)

    c1, c2 = st.columns(2)
    with c1:
        st.altair_chart(line, use_container_width=True)
    with c2:
        st.altair_chart(bar, use_container_width=True)
