import streamlit as st
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph, KeepTogether
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

st.set_page_config(page_title="Painel Diário de Cargas", layout="wide")

# 🔐 GOOGLE SHEETS VIA STREAMLIT SECRETS
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

info = json.loads(st.secrets["gcp_service_account"]["json"])
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
    color: #155724;
}
.badge-pendente {
    background: #f8d7da;
    color: #721c24;
}
</style>
""", unsafe_allow_html=True)

# 🖨️ PDF
def gerar_pdf(bloco):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=10,
        leftMargin=10,
        topMargin=10,
        bottomMargin=10
    )

    elements = []
    styles = getSampleStyleSheet()

    style_small = ParagraphStyle(
        'small',
        parent=styles['Normal'],
        fontSize=7,
        leading=8
    )

    primeira = bloco.iloc[0]

    cubagem_total = 0
    for _, row in bloco.iterrows():
        try:
            cubagem_total += float(str(row["CUBAGEM FINAL"]).replace(",", "."))
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
        ["Cálculo KIT", f"{resultado_kit:.2f}"],
        ["Cálculo MIX", f"{resultado_mix:.2f}"],
    ]

    header_table = Table(header, colWidths=[160, 340])
    header_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.4, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('FONTSIZE', (0,0), (-1,-1), 8)
    ]))

    tabela = [["CLIENTE", "NF", "VOL", "PESO", "REDESPACHO", "CONF."]]

    for _, row in bloco.iterrows():
        redespacho = row["REDESPACHO"].strip().upper()
        destino_nota = redespacho if redespacho else "ENTREGA DIRETA"

        tabela.append([
            Paragraph(str(row["CLIENTE"]), style_small),
            str(row["NOTAS FISCAIS"]),
            str(row["VOLUMES"]),
            str(row["PESO Kg"]),
            destino_nota,
            ""
        ])

    table = Table(tabela, colWidths=[230, 90, 60, 70, 110, 50])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.4, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (5,1), (5,-1), 'CENTER')
    ]))

    elements.append(KeepTogether([header_table, Spacer(1,6), table]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# 🧩 CARDS
cols = st.columns(3)

for i, bloco in enumerate(blocos):

    col = cols[i % 3]

    with col:

        primeira = bloco.iloc[0]

        motorista = primeira["MOTORISTA"]
        placa = primeira["PLACA"]
        destino = primeira["DESTINO"]
        data = primeira["DATA"]
        gw = primeira["COLETA GW"]

        status = str(primeira["CARREGAMENTO CONCLUIDO"]).strip().upper()

        if status == "SIM":
            classe = "card finalizado"
            badge = '<div class="badge badge-ok">FINALIZADO</div>'
        else:
            classe = "card pendente"
            badge = '<div class="badge badge-pendente">PENDENTE</div>'

        pdf = gerar_pdf(bloco)

        st.markdown(f"""
        <div class="{classe}">
            <b>{motorista}</b><br>
            Placa: {placa}<br>
            Destino: {destino}<br>
            Data: {data}<br>
            <div class="badge">GW: {gw}</div><br>
            {badge}
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            "🖨️ Gerar Conferência",
            data=pdf,
            file_name=f"Carga_{motorista}_{gw}.pdf",
            mime="application/pdf",
            key=f"download_{i}"
        )
