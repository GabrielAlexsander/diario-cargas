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

# 🔐 GOOGLE SHEETS
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

st.markdown("## Painel Diário de Cargas - Porcelana/Tramontina")

# =========================
# SEPARAR BLOCOS
# =========================
blocos = []
bloco_atual = []

for _, row in df.iterrows():
    if (row == "").all():
        if bloco_atual:
            blocos.append(pd.DataFrame(bloco_atual))
            bloco_atual = []
    else:
        bloco_atual.append(row)

if bloco_atual:
    blocos.append(pd.DataFrame(bloco_atual))

# =========================
# ESTILO EXECUTIVO
# =========================
st.markdown("""
<style>
.metric-card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    text-align: center;
}
.metric-value {
    font-size: 32px;
    font-weight: 700;
}
.metric-label {
    font-size: 14px;
    color: gray;
}
.section-title {
    font-size:18px;
    font-weight:600;
    margin-top:10px;
}
</style>
""", unsafe_allow_html=True)

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
    style_small = ParagraphStyle(
        'small',
        parent=styles['Normal'],
        fontSize=6,
        leading=6
    )

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
# DASHBOARD EXECUTIVO
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
                return "CD"
            redesp = str(row["REDESPACHO"]).strip().upper()
            if redesp:
                return "REDESPACHO"
            return "DIRETO CLIENTE"

        df_dash["TIPO"] = df_dash.apply(tipo, axis=1)

        total_cub = df_dash["CUBAGEM FINAL"].sum()
        total_peso = df_dash["PESO Kg"].sum()
        total_vol = df_dash["VOLUMES"].sum()

        cub_cd = df_dash[df_dash["TIPO"]=="CD"]["CUBAGEM FINAL"].sum()
        cub_direto = df_dash[df_dash["TIPO"]=="DIRETO CLIENTE"]["CUBAGEM FINAL"].sum()
        cub_redesp = df_dash[df_dash["TIPO"]=="REDESPACHO"]["CUBAGEM FINAL"].sum()

        # CARDS SUPERIORES
        col1,col2,col3,col4 = st.columns(4)

        col1.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_cub:.1f}</div>
            <div class="metric-label">Cubagem Total</div>
        </div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_peso:.0f} kg</div>
            <div class="metric-label">Peso Total</div>
        </div>
        """, unsafe_allow_html=True)

        col3.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_vol:.0f}</div>
            <div class="metric-label">Volumes Totais</div>
        </div>
        """, unsafe_allow_html=True)

        col4.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df_dash)}</div>
            <div class="metric-label">Notas Pendentes</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # GRÁFICO CD / DIRETO / REDESPACHO
        resumo = df_dash.groupby("TIPO")["CUBAGEM FINAL"].sum()

        st.markdown("### Distribuição de Cubagem")
        st.bar_chart(resumo)

    else:
        st.info("Nenhuma carga pendente hoje.")

# =========================
# PENDENTES (INALTERADO)
# =========================
with aba_pendentes:
    cols = st.columns(3)
    contador = 0

    for bloco in blocos:
        primeira = bloco.iloc[0]
        status = str(primeira["CARREGAMENTO CONCLUIDO"]).strip().upper()

        if status != "SIM":
            col = cols[contador % 3]
            contador += 1
            with col:
                motorista = primeira["MOTORISTA"]
                placa = primeira["PLACA"]
                destino = primeira["DESTINO"]
                data = primeira["DATA"]
                gw = primeira["COLETA GW"]

                pdf = gerar_pdf(bloco)

                st.markdown(f"""
                <div style="background:#fff5f5;padding:14px;border-radius:12px;margin-bottom:10px;">
                <b>{motorista}</b><br>
                Placa: {placa}<br>
                Destino: {destino}<br>
                Data: {data}<br>
                GW: {gw}
                </div>
                """, unsafe_allow_html=True)

                st.download_button("🖨️ Gerar Conferência",
                                   data=pdf,
                                   file_name=f"Carga_{motorista}_{gw}.pdf",
                                   mime="application/pdf")

# =========================
# FINALIZADOS (INALTERADO)
# =========================
with aba_finalizados:
    cols = st.columns(3)
    contador = 0

    for bloco in blocos:
        primeira = bloco.iloc[0]
        status = str(primeira["CARREGAMENTO CONCLUIDO"]).strip().upper()

        if status == "SIM":
            col = cols[contador % 3]
            contador += 1
            with col:
                motorista = primeira["MOTORISTA"]
                placa = primeira["PLACA"]
                destino = primeira["DESTINO"]
                data = primeira["DATA"]
                gw = primeira["COLETA GW"]

                pdf = gerar_pdf(bloco)

                st.markdown(f"""
                <div style="background:#e9f9ee;padding:14px;border-radius:12px;margin-bottom:10px;">
                <b>{motorista}</b><br>
                Placa: {placa}<br>
                Destino: {destino}<br>
                Data: {data}<br>
                GW: {gw}
                </div>
                """, unsafe_allow_html=True)

                st.download_button("🖨️ Gerar Conferência",
                                   data=pdf,
                                   file_name=f"Carga_{motorista}_{gw}.pdf",
                                   mime="application/pdf")
