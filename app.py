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

# 🔐 GOOGLE SHEETS VIA STREAMLIT SECRETS
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

# 🔥 SEPARAR POR LINHA VAZIA
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

# 🎨 ESTILO CARD
st.markdown("""
<style>
.card {
    padding: 14px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 10px;
    font-size: 13px;
    color: #000000 !important;
}
.card b {
    color: #000000 !important;
}
.finalizado {
    background: #e9f9ee;
    border-left: 6px solid #28a745;
}
.pendente {
    background: #fff5f5;
    border-left: 6px solid #dc3545;
}
.badge {
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: bold;
    display: inline-block;
    margin-top: 6px;
}
.badge-ok {
    background: #d4edda;
    color: #155724 !important;
}
.badge-pendente {
    background: #f8d7da;
    color: #721c24 !important;
}
</style>
""", unsafe_allow_html=True)

# 🖨️ PDF (INALTERADO)
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
    for _, row in bloco.iterrows():
        try:
            cubagem_total += float(str(row["CUBAGEM FINAL"]).replace(",", "."))
        except:
            pass

    peso_total = 0
    for _, row in bloco.iterrows():
        try:
            peso_total += float(str(row["PESO Kg"]).replace(",", "."))
        except:
            pass

    cubagem_com_10 = cubagem_total * 1.10
    base_calculo = cubagem_com_10 / 2.5
    resultado_kit = base_calculo / 1.9
    resultado_mix = base_calculo / 1.3

    header = [
        ["Motorista", primeira["MOTORISTA"]],
        ["Placa", primeira["PLACA"]],
        ["Destino", primeira["DESTINO"]],
        ["Data", primeira["DATA"]],
        ["GW", primeira["COLETA GW"]],
        ["Cubagem Total", f"{cubagem_total:.2f}"],
        ["Peso Total (Kg)", f"{peso_total:.2f}"],
        ["Cálculo KIT", f"{resultado_kit:.2f}"],
        ["Cálculo MIX", f"{resultado_mix:.2f}"],
    ]

    header_table = Table(header, colWidths=[110, 250])
    header_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('FONTSIZE', (0,0), (-1,-1), 6),
    ]))

    tabela = [["CLIENTE","DESTINO NF","NF","VOL","PESO","CUB.","REDESP.","CONF."]]

    for _, row in bloco.iterrows():
        redespacho = str(row["REDESPACHO"]).strip().upper()
        destino_nota = redespacho if redespacho else "ENTREGA DIRETA"

        try:
            cubagem_individual = float(str(row["CUBAGEM FINAL"]).replace(",", "."))
            cubagem_formatada = f"{cubagem_individual:.2f}"
        except:
            cubagem_formatada = "0.00"

        tabela.append([
            Paragraph(str(row["CLIENTE"]), style_small),
            Paragraph(str(row["DESTINO"]), style_small),
            Paragraph(str(row["NOTAS FISCAIS"]), style_small),
            Paragraph(str(row["VOLUMES"]), style_small),
            Paragraph(str(row["PESO Kg"]), style_small),
            Paragraph(cubagem_formatada, style_small),
            Paragraph(destino_nota, style_small),
            ""
        ])

    table = Table(tabela, colWidths=[95,70,50,30,40,40,55,25])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
        ('GRID',(0,0),(-1,-1),0.3,colors.grey),
        ('FONTSIZE',(0,0),(-1,-1),6),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1,4))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# 🔥 ABAS
aba_dashboard, aba_pendentes, aba_finalizados = st.tabs(
    ["Dashboard Diário", "Pendentes", "Finalizados"]
)

# =========================
# 📊 DASHBOARD DIÁRIO
# =========================
with aba_dashboard:

    st.subheader("Dashboard Diário - Cargas NÃO Carregadas")

    df_dashboard = df[df["CARREGAMENTO CONCLUIDO"].str.upper() != "SIM"].copy()

    if not df_dashboard.empty:

        df_dashboard["CUBAGEM FINAL"] = pd.to_numeric(
            df_dashboard["CUBAGEM FINAL"].str.replace(",", ".", regex=False),
            errors="coerce"
        ).fillna(0)

        df_dashboard["VOLUMES"] = pd.to_numeric(
            df_dashboard["VOLUMES"],
            errors="coerce"
        ).fillna(0)

        df_dashboard["PESO Kg"] = pd.to_numeric(
            df_dashboard["PESO Kg"].str.replace(",", ".", regex=False),
            errors="coerce"
        ).fillna(0)

        def classificar(row):
            destino = str(row["DESTINO"]).upper()

            if "CD " in destino:
                return destino

            redespacho = str(row["REDESPACHO"]).strip().upper()

            if redespacho:
                return redespacho

            return "DIRETO CLIENTE"

        df_dashboard["TIPO"] = df_dashboard.apply(classificar, axis=1)

        resumo = df_dashboard.groupby("TIPO").agg({
            "CUBAGEM FINAL":"sum",
            "VOLUMES":"sum"
        }).reset_index()

        st.markdown("### Cubagem por Tipo")
        st.bar_chart(resumo.set_index("TIPO")["CUBAGEM FINAL"])

        st.markdown("### Volumes por Tipo")
        st.bar_chart(resumo.set_index("TIPO")["VOLUMES"])

        col1, col2 = st.columns(2)

        col1.metric("Cubagem Total do Dia",
                    f"{df_dashboard['CUBAGEM FINAL'].sum():.2f}")

        col2.metric("Peso Total do Dia (Kg)",
                    f"{df_dashboard['PESO Kg'].sum():.2f}")

    else:
        st.info("Nenhuma carga pendente no dia.")

# =========================
# 🔴 PENDENTES
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
                <div class="card pendente">
                    <b>{motorista}</b><br>
                    Placa: {placa}<br>
                    Destino: {destino}<br>
                    Data: {data}<br>
                    <div class="badge">GW: {gw}</div><br>
                    <div class="badge badge-pendente">PENDENTE</div>
                </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    "🖨️ Gerar Conferência",
                    data=pdf,
                    file_name=f"Carga_{motorista}_{gw}.pdf",
                    mime="application/pdf",
                    key=f"pendente_{contador}"
                )

# =========================
# 🟢 FINALIZADOS
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
                <div class="card finalizado">
                    <b>{motorista}</b><br>
                    Placa: {placa}<br>
                    Destino: {destino}<br>
                    Data: {data}<br>
                    <div class="badge">GW: {gw}</div><br>
                    <div class="badge badge-ok">FINALIZADO</div>
                </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    "🖨️ Gerar Conferência",
                    data=pdf,
                    file_name=f"Carga_{motorista}_{gw}.pdf",
                    mime="application/pdf",
                    key=f"finalizado_{contador}"
                )
