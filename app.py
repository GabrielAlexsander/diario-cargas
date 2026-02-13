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


# 🖨️ PDF EM PÉ
def gerar_pdf(bloco):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,  # 🔥 AGORA EM PÉ
        rightMargin=5,
        leftMargin=5,
        topMargin=5,
        bottomMargin=5
    )

    elements = []
    styles = getSampleStyleSheet()

    style_small = ParagraphStyle(
        'small',
        parent=styles['Normal'],
        fontSize=6,
        leading=6
    )

    primeira = bloco.iloc[0]

    # 🔹 Soma Cubagem
    cubagem_total = 0
    for _, row in bloco.iterrows():
        try:
            cubagem_total += float(str(row["CUBAGEM FINAL"]).replace(",", "."))
        except:
            pass

    # 🔹 Soma Peso Total
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
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))

    tabela = [["CLIENTE", "NF", "VOL", "PESO", "REDESP.", "CONF."]]

    for _, row in bloco.iterrows():
        redespacho = str(row["REDESPACHO"]).strip().upper()
        destino_nota = redespacho if redespacho else "ENTREGA DIRETA"

        tabela.append([
            Paragraph(str(row["CLIENTE"]), style_small),
            Paragraph(str(row["NOTAS FISCAIS"]), style_small),
            Paragraph(str(row["VOLUMES"]), style_small),
            Paragraph(str(row["PESO Kg"]), style_small),
            Paragraph(destino_nota, style_small),
            ""
        ])

    # 🔥 COLUNAS REDUZIDAS PARA CABER EM PÉ
    table = Table(tabela, colWidths=[150, 60, 40, 50, 70, 35])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.3, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1,4))
    elements.append(table)

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
