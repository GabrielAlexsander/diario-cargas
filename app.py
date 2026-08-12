import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph, PageBreak, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
import io
import os
import base64

st.set_page_config(page_title="Painel Diário de Cargas", layout="wide")


def localizar_logo():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminhos = [
        os.path.join(base_dir, "logo.png"),
        os.path.join(base_dir, "Imagem1.png"),
        os.path.join(base_dir, "logo.jpg"),
        os.path.join(base_dir, "logo.jpeg"),
        os.path.join(base_dir, "assets", "logo.png"),
        os.path.join(base_dir, "assets", "Imagem1.png"),
        os.path.join(base_dir, "assets", "logo.jpg"),
        os.path.join(base_dir, "assets", "logo.jpeg"),
    ]

    for caminho in caminhos:
        if os.path.exists(caminho):
            return caminho

    return None


LOGO_PATH = localizar_logo()


def logo_html():
    if not LOGO_PATH:
        return '<div class="logo-texto">TRANSNET</div>'

    extensao = os.path.splitext(LOGO_PATH)[1].lower()
    mime = "jpeg" if extensao in [".jpg", ".jpeg"] else "png"

    with open(LOGO_PATH, "rb") as arquivo:
        logo_base64 = base64.b64encode(arquivo.read()).decode()

    return f'<img src="data:image/{mime};base64,{logo_base64}" alt="TRANSNET">'


# GOOGLE SHEETS VIA STREAMLIT SECRETS
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

# SEPARAR POR LINHA VAZIA
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

# ESTILO
st.markdown("""
<style>
.stApp {
    background: #f4f7fb;
}

.block-container {
    padding-top: 1.15rem;
    padding-bottom: 2rem;
    max-width: 1280px;
}

.hero {
    position: relative;
    display: grid;
    grid-template-columns: 218px minmax(0, 1fr);
    align-items: center;
    gap: 18px;
    background: #ffffff;
    border: 1px solid #d9e2f0;
    border-radius: 12px;
    padding: 16px 22px;
    margin-bottom: 22px;
    box-shadow: 0 12px 26px rgba(15, 23, 42, 0.06);
    overflow: hidden;
}

.hero::after {
    content: "";
    position: absolute;
    left: 22px;
    right: 22px;
    bottom: 0;
    height: 3px;
    background: linear-gradient(90deg, #2445d8 0%, #8fa8ff 38%, rgba(143, 168, 255, 0) 72%);
}

.hero-logo {
    width: 218px;
    min-width: 218px;
    height: 72px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    padding-right: 18px;
    border-right: 1px solid #e2e8f0;
    transform: translateY(6px);
}

.hero-logo img {
    width: 210px;
    max-height: 72px;
    object-fit: contain;
    object-position: left center;
    display: block;
    transform: translateY(9px);
}

.logo-texto {
    font-size: 28px;
    font-weight: 900;
    color: #2445d8;
    letter-spacing: 0;
}

.hero-info {
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 1px;
}

.hero-kicker {
    color: #2445d8;
    font-size: 10px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0;
    line-height: 1;
}

hero-title {
    font-size: 31px;
    font-weight: 900;
    line-height: 1.05;
    margin: 0;
    padding-left: 0;
    color: #172033;
    text-wrap: pretty;
}

.hero-title span {
    color: #2445d8;
}

.hero-subtitle {
    color: #475569;
    font-size: 13px;
    font-weight: 700;
    margin-top: -26px;
    margin-left: 2px;
}

div[data-testid="stTabs"] button {
    font-weight: 800;
    color: #475569;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #2445d8;
}

div[data-testid="stCheckbox"] label {
    font-weight: 700;
    color: #334155;
}

div.stDownloadButton > button {
    width: 100%;
    border-radius: 10px;
    border: 1px solid rgba(55, 100, 255, 0.18);
    background: #2445d8;
    color: #ffffff;
    font-weight: 800;
    padding: 0.55rem 0.8rem;
    transition: all 0.2s ease;
}

div.stDownloadButton > button:hover {
    background: #1d35ad;
    border-color: #1d35ad;
    color: #ffffff;
    transform: translateY(-1px);
}

.card {
    min-height: 275px;
    padding: 16px;
    border-radius: 14px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.07);
    margin-bottom: 10px;
    font-size: 13px;
    color: #0f172a !important;
    background: #ffffff;
}

.card b {
    color: #0f172a !important;
}

.card:hover {
    transform: translateY(-2px);
    transition: all 0.2s ease;
    box-shadow: 0 16px 32px rgba(15, 23, 42, 0.11);
}

.finalizado {
    border-left: 6px solid #16a34a;
}

.pendente {
    border-left: 6px solid #dc2626;
}

.card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
}

.card-label {
    color: #64748b;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0;
    margin-bottom: 4px;
}

.card-title {
    min-height: 42px;
    font-size: 16px;
    line-height: 1.25;
    color: #0f172a;
    font-weight: 900;
    word-break: break-word;
}

.card-grid {
    display: grid;
    gap: 8px;
    margin-top: 14px;
}

.card-line {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    padding-top: 8px;
    border-top: 1px solid #e5e7eb;
}

.card-line span {
    color: #64748b;
    font-weight: 700;
}

.card-line strong {
    color: #111827;
    text-align: right;
    word-break: break-word;
}

.badge {
    padding: 5px 9px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 900;
    display: inline-block;
    white-space: nowrap;
}

.badge-ok {
    background: #dcfce7;
    color: #166534 !important;
}

.badge-pendente {
    background: #fee2e2;
    color: #991b1b !important;
}

.gw-chip {
    display: inline-block;
    margin-top: 12px;
    padding: 6px 10px;
    border-radius: 999px;
    background: #eef2ff;
    color: #2445d8;
    font-size: 12px;
    font-weight: 900;
}

@media (max-width: 760px) {
    .hero {
        grid-template-columns: 1fr;
        gap: 10px;
        padding: 16px;
    }

    .hero-logo {
        width: 100%;
        min-width: 100%;
        height: 68px;
        padding-right: 0;
        border-right: none;
    }

    .hero-logo img {
        width: 210px;
        max-height: 68px;
    }

    .hero-title {
        font-size: 28px;
    }
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero">
    <div class="hero-logo">
        {logo_html()}
    </div>
    <div class="hero-info">
        <div class="hero-kicker">Painel operacional</div>
        <h1 class="hero-title">Painel de <span>cargas</span></h1>
        <div class="hero-subtitle">Porcelana - Tramontina</div>
    </div>
</div>
""", unsafe_allow_html=True)


# PDF
def criar_logo_pdf():
    if LOGO_PATH:
        largura_original, altura_original = ImageReader(LOGO_PATH).getSize()

        largura_maxima = 145
        altura_maxima = 46
        proporcao = min(
            largura_maxima / largura_original,
            altura_maxima / altura_original
        )

        largura = largura_original * proporcao
        altura = altura_original * proporcao

        return RLImage(LOGO_PATH, width=largura, height=altura, hAlign="LEFT")

    styles = getSampleStyleSheet()
    return Paragraph(
        "<b>TRANSNET</b>",
        ParagraphStyle(
            "logo_texto_pdf",
            parent=styles["Normal"],
            fontSize=16,
            leading=18,
            textColor=colors.HexColor("#2445d8"),
        )
    )


def montar_elementos_pdf(bloco):
    elements = []

    styles = getSampleStyleSheet()
    style_small = ParagraphStyle(
        'small',
        parent=styles['Normal'],
        fontSize=6,
        leading=6
    )

    primeira = bloco.iloc[0]
    tipo_movimentacao = primeira.iloc[12] if len(primeira) > 12 else ""

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

    titulo_pdf = Paragraph(
        "<b>Relatório de cargas</b><br/><font size='7' color='#64748b'>Porcelana - Tramontina</font>",
        ParagraphStyle(
            "pdf_brand_title",
            parent=styles["Normal"],
            fontSize=11,
            leading=13,
            textColor=colors.HexColor("#0f172a"),
        )
    )

    brand_table = Table(
        [[criar_logo_pdf(), titulo_pdf]],
        colWidths=[160, 375],
        rowHeights=[58]
    )

    brand_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('BOX', (0,0), (-1,-1), 0.4, colors.HexColor("#dbe3ef")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))

    header = [
        ["Motorista", primeira["MOTORISTA"]],
        ["Placa", primeira["PLACA"]],
        ["Destino", primeira["DESTINO"]],
        ["Data", primeira["DATA"]],
        ["Tipo de Movimentação", tipo_movimentacao],
        ["GW", primeira["COLETA GW"]],
        ["Cubagem Total (Soma das NFs)", f"{cubagem_total:.2f}"],
        ["Peso Total (Kg)", f"{peso_total:.2f}"],
        ["Cálculo KIT", f"{resultado_kit:.2f}"],
        ["Cálculo MIX", f"{resultado_mix:.2f}"],
    ]

    header_table = Table(header, colWidths=[130, 405])
    header_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#dbe3ef")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#eef2ff")),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor("#1d35ad")),
        ('FONTSIZE', (0,0), (-1,-1), 6),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))

    tabela = [["CLIENTE", "DESTINO NF", "NF", "CONF.", "VOL", "PESO", "CUB.", "REDESP."]]

    for _, row in bloco.iterrows():

        redespacho = str(row["REDESPACHO"]).strip().upper()
        destino_nota = redespacho if redespacho else "ENTREGA DIRETA"

        try:
            cubagem = float(str(row["CUBAGEM FINAL"]).replace(",", "."))
            cubagem_formatada = f"{cubagem:.2f}"
        except:
            cubagem_formatada = "0.00"

        tabela.append([
            Paragraph(str(row["CLIENTE"]), style_small),
            Paragraph(str(row["DESTINO"]), style_small),
            Paragraph(str(row["NOTAS FISCAIS"]), style_small),
            "",
            Paragraph(str(row["VOLUMES"]), style_small),
            Paragraph(str(row["PESO Kg"]), style_small),
            Paragraph(cubagem_formatada, style_small),
            Paragraph(destino_nota, style_small),
        ])

    table = Table(tabela, colWidths=[95, 70, 45, 30, 30, 40, 40, 55])

    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1d35ad")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor("#cbd5e1")),
        ('FONTSIZE',(0,0),(-1,-1),6),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))

    elements.append(brand_table)
    elements.append(Spacer(1,6))
    elements.append(header_table)
    elements.append(Spacer(1,4))
    elements.append(table)

    return elements


def gerar_pdf(bloco):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=5,
        leftMargin=5,
        topMargin=5,
        bottomMargin=5
    )

    elements = montar_elementos_pdf(bloco)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_pdf_selecionados(blocos_selecionados):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=5,
        leftMargin=5,
        topMargin=5,
        bottomMargin=5
    )

    elements = []

    for indice, bloco in enumerate(blocos_selecionados):
        if indice > 0:
            elements.append(PageBreak())

        elements.extend(montar_elementos_pdf(bloco))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# FILTRO DE DATA
def converter_data(valor):
    data_convertida = pd.to_datetime(str(valor).strip(), dayfirst=True, errors="coerce")
    if pd.isna(data_convertida):
        return None
    return data_convertida.date()


# ABAS
aba_pendentes, aba_finalizados = st.tabs(["Pendentes", "Finalizados"])

# PENDENTES
with aba_pendentes:
    filtrar_data_pendentes = st.checkbox("Filtrar por data", key="check_data_pendentes")
    filtro_data_pendentes = None
    selecionados_pendentes = []

    if filtrar_data_pendentes:
        filtro_data_pendentes = st.date_input(
            "Data",
            format="DD/MM/YYYY",
            key="filtro_data_pendentes"
        )

    cols = st.columns(3)
    contador = 0

    for indice_bloco, bloco in enumerate(blocos):
        primeira = bloco.iloc[0]
        status = str(primeira["CARREGAMENTO CONCLUIDO"]).strip().upper()

        data_bloco = converter_data(primeira["DATA"])

        if filtro_data_pendentes and data_bloco != filtro_data_pendentes:
            continue

        if status != "SIM":
            col = cols[contador % 3]
            contador += 1

            with col:
                motorista = primeira["MOTORISTA"]
                placa = primeira["PLACA"]
                destino = primeira["DESTINO"]
                data = primeira["DATA"]
                gw = primeira["COLETA GW"]
                tipo_carga = primeira["TIPO DE CARGA"]

                pdf = gerar_pdf(bloco)

                st.markdown(f"""
                <div class="card pendente">
                    <div class="card-top">
                        <div>
                            <div class="card-label">Motorista</div>
                            <div class="card-title">{motorista}</div>
                        </div>
                        <div class="badge badge-pendente">PENDENTE</div>
                    </div>
                    <div class="card-grid">
                        <div class="card-line"><span>Placa</span><strong>{placa}</strong></div>
                        <div class="card-line"><span>Destino</span><strong>{destino}</strong></div>
                        <div class="card-line"><span>Tipo de Carga</span><strong>{tipo_carga}</strong></div>
                        <div class="card-line"><span>Data</span><strong>{data}</strong></div>
                    </div>
                    <div class="gw-chip">GW: {gw}</div>
                </div>
                """, unsafe_allow_html=True)

                selecionado = st.checkbox(
                    "Selecionar",
                    key=f"selecionar_pendente_{indice_bloco}"
                )

                if selecionado:
                    selecionados_pendentes.append(bloco)

                st.download_button(
                    "Gerar Conferência",
                    data=pdf,
                    file_name=f"Carga_{motorista}_{gw}.pdf",
                    mime="application/pdf",
                    key=f"pendente_{contador}"
                )

    if len(selecionados_pendentes) > 1:
        pdf_selecionados = gerar_pdf_selecionados(selecionados_pendentes)

        st.download_button(
            "Imprimir selecionados",
            data=pdf_selecionados,
            file_name="Cargas_pendentes_selecionadas.pdf",
            mime="application/pdf",
            key="imprimir_pendentes_selecionados"
        )

# FINALIZADOS
with aba_finalizados:
    filtrar_data_finalizados = st.checkbox("Filtrar por data", key="check_data_finalizados")
    filtro_data_finalizados = None
    selecionados_finalizados = []

    if filtrar_data_finalizados:
        filtro_data_finalizados = st.date_input(
            "Data",
            format="DD/MM/YYYY",
            key="filtro_data_finalizados"
        )

    cols = st.columns(3)
    contador = 0

    for indice_bloco, bloco in enumerate(blocos):
        primeira = bloco.iloc[0]
        status = str(primeira["CARREGAMENTO CONCLUIDO"]).strip().upper()

        data_bloco = converter_data(primeira["DATA"])

        if filtro_data_finalizados and data_bloco != filtro_data_finalizados:
            continue

        if status == "SIM":
            col = cols[contador % 3]
            contador += 1

            with col:
                motorista = primeira["MOTORISTA"]
                placa = primeira["PLACA"]
                destino = primeira["DESTINO"]
                data = primeira["DATA"]
                gw = primeira["COLETA GW"]
                tipo_carga = primeira["TIPO DE CARGA"]

                pdf = gerar_pdf(bloco)

                st.markdown(f"""
                <div class="card finalizado">
                    <div class="card-top">
                        <div>
                            <div class="card-label">Motorista</div>
                            <div class="card-title">{motorista}</div>
                        </div>
                        <div class="badge badge-ok">FINALIZADO</div>
                    </div>
                    <div class="card-grid">
                        <div class="card-line"><span>Placa</span><strong>{placa}</strong></div>
                        <div class="card-line"><span>Destino</span><strong>{destino}</strong></div>
                        <div class="card-line"><span>Tipo de Carga</span><strong>{tipo_carga}</strong></div>
                        <div class="card-line"><span>Data</span><strong>{data}</strong></div>
                    </div>
                    <div class="gw-chip">GW: {gw}</div>
                </div>
                """, unsafe_allow_html=True)

                selecionado = st.checkbox(
                    "Selecionar",
                    key=f"selecionar_finalizado_{indice_bloco}"
                )

                if selecionado:
                    selecionados_finalizados.append(bloco)

                st.download_button(
                    "Gerar Conferência",
                    data=pdf,
                    file_name=f"Carga_{motorista}_{gw}.pdf",
                    mime="application/pdf",
                    key=f"finalizado_{contador}"
                )

    if len(selecionados_finalizados) > 1:
        pdf_selecionados = gerar_pdf_selecionados(selecionados_finalizados)

        st.download_button(
            "Imprimir selecionados",
            data=pdf_selecionados,
            file_name="Cargas_finalizadas_selecionadas.pdf",
            mime="application/pdf",
            key="imprimir_finalizados_selecionados"
        )
