import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

st.set_page_config(page_title="Painel Diário de Cargas", layout="wide")

# =========================
# ESTILO POWER BI DARK
# =========================
st.markdown("""
<style>
html, body, [class*="css"]  {
    background-color: #0e1117;
    color: white;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

.metric-card {
    background: linear-gradient(135deg, #1f2937, #111827);
    padding: 18px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

.metric-value {
    font-size: 28px;
    font-weight: 700;
}

.metric-label {
    font-size: 13px;
    color: #9ca3af;
}

.section-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 5px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# GOOGLE SHEETS
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

info = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
client = gspread.authorize(creds)

SHEET_ID = "1-rcw838y84sDORYXdNtvBCFg_8oKeBFJ8IgOcnj3qcg"
sheet = client.open_by_key(SHEET_ID).get_worksheet(0)

dados = sheet.get_all_values()
df = pd.DataFrame(dados[1:], columns=dados[0])
df.columns = df.columns.str.strip()

# =========================
# PDF (INALTERADO)
# =========================
def gerar_pdf(bloco):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=5, leftMargin=5,
                            topMargin=5, bottomMargin=5)
    elements = []
    styles = getSampleStyleSheet()
    style_small = ParagraphStyle('small', parent=styles['Normal'], fontSize=6, leading=6)

    primeira = bloco.iloc[0]
    cubagem_total = 0
    peso_total = 0

    for _, row in bloco.iterrows():
        try:
            cubagem_total += float(str(row["CUBAGEM FINAL"]).replace(",", "."))
        except:
            pass
        try:
            peso_total += float(str(row["PESO Kg"]).replace(",", "."))
        except:
            pass

    header = [
        ["Motorista", primeira["MOTORISTA"]],
        ["Placa", primeira["PLACA"]],
        ["Destino", primeira["DESTINO"]],
        ["Data", primeira["DATA"]],
        ["GW", primeira["COLETA GW"]],
        ["Cubagem Total", f"{cubagem_total:.2f}"],
        ["Peso Total (Kg)", f"{peso_total:.2f}"],
    ]

    header_table = Table(header, colWidths=[110, 250])
    header_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('FONTSIZE', (0,0), (-1,-1), 6),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1,4))
    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================
# ABAS
# =========================
aba_dashboard, aba_pendentes, aba_finalizados = st.tabs(
    ["Dashboard Diário", "Pendentes", "Finalizados"]
)

# =========================
# DASHBOARD PROFISSIONAL TV
# =========================
with aba_dashboard:

    df_dash = df[df["CARREGAMENTO CONCLUIDO"].str.upper() != "SIM"].copy()

    if not df_dash.empty:

        df_dash["CUBAGEM FINAL"] = pd.to_numeric(
            df_dash["CUBAGEM FINAL"].str.replace(",", ".", regex=False),
            errors="coerce").fillna(0)

        df_dash["VOLUMES"] = pd.to_numeric(
            df_dash["VOLUMES"], errors="coerce").fillna(0)

        df_dash["PESO Kg"] = pd.to_numeric(
            df_dash["PESO Kg"].str.replace(",", ".", regex=False),
            errors="coerce").fillna(0)

        def tipo(row):
            destino = str(row["DESTINO"]).upper()
            if "CD " in destino:
                return destino
            redesp = str(row["REDESPACHO"]).strip().upper()
            if redesp:
                return "REDESPACHO"
            return "DIRETO CLIENTE"

        df_dash["TIPO"] = df_dash.apply(tipo, axis=1)

        total_cub = df_dash["CUBAGEM FINAL"].sum()
        total_peso = df_dash["PESO Kg"].sum()
        total_vol = df_dash["VOLUMES"].sum()

        col1, col2, col3 = st.columns(3)

        col1.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_cub:.1f}</div>
            <div class="metric-label">CUBAGEM TOTAL</div>
        </div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_peso:.0f} kg</div>
            <div class="metric-label">PESO TOTAL</div>
        </div>
        """, unsafe_allow_html=True)

        col3.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_vol:.0f}</div>
            <div class="metric-label">VOLUMES</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")

        resumo = df_dash.groupby("TIPO")["CUBAGEM FINAL"].sum().sort_values()

        st.markdown('<div class="section-title">CUBAGEM POR TIPO DE CARGA</div>', unsafe_allow_html=True)
        st.bar_chart(resumo)

    else:
        st.info("Nenhuma carga pendente hoje.")

# =========================
# PENDENTES E FINALIZADOS
# (SEU CÓDIGO ORIGINAL MANTIDO)
# =========================
