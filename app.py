import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Extrato PDF → Excel com Plano de Contas", layout="wide")

 # Hiding humburguer menu
        hide_st_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    header {visibility: hidden;}
                    </style>
                    """
        st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("Observer - Extrato PDF → Excel com Plano de Contas")

uploaded_file = st.file_uploader("Envie o extrato em PDF", type=["pdf"])

# -------------------------
# DICIONÁRIO DE PLANO DE CONTAS
# -------------------------

plano_contas = {
    "mercado": "Despesa → Alimentação",
    "supermercado": "Despesa → Alimentação",
    "ifood": "Despesa → Alimentação",
    "padaria": "Despesa → Alimentação",

    "combust": "Despesa → Combustível",
    "posto": "Despesa → Combustível",
    "ipiranga": "Despesa → Combustível",

    "uber": "Despesa → Transporte",
    "99": "Despesa → Transporte",
    "taxi": "Despesa → Transporte",

    "salário": "Receita → Salários",
    "pagto": "Receita → Clientes",
    "depósito": "Receita → Depósitos",
    "transferência recebida": "Receita → Transferência",

    "pix enviado": "Despesa → Transferências",
    "pagamento": "Despesa → Pagamentos",
    "boleto": "Despesa → Boletos",

    "saque": "Despesa → Saque",
    "tarifa": "Despesa → Tarifas Bancárias",
    "mensalidade": "Despesa → Tarifas Bancárias",
}

def classificar_plano_contas(descricao: str):
    desc_lower = descricao.lower()

    for palavra, conta in plano_contas.items():
        if palavra in desc_lower:
            return conta

    if "-" in desc_lower or "compra" in desc_lower:
        return "Despesa → Outras"

    return "Outros"


# -------------------------
# EXTRATOR DE PDF COM PROGRESSO
# -------------------------

def extract_data_from_pdf(pdf_file):
    data = []

    with pdfplumber.open(pdf_file) as pdf:
        total_pages = len(pdf.pages)
        progress_bar = st.progress(0)

        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                lines = text.split("\n")

                for line in lines:
                    parts = line.split()
                    if len(parts) < 3:
                        continue

                    if "/" in parts[0]:
                        try:
                            date = parts[0]
                            value = parts[-1]
                            description = " ".join(parts[1:-1])

                            value = value.replace(".", "").replace(",", ".")
                            value = float(value)

                            plano = classificar_plano_contas(description)

                            data.append([date, description, value, plano])
                        except:
                            pass

            # Atualizando a barra de progresso
            progress_bar.progress((i + 1) / total_pages)

    return pd.DataFrame(data, columns=["Data", "Descrição", "Valor", "Plano de Contas Sugerido"])


# -------------------------
# INTERFACE
# -------------------------

if uploaded_file:
    st.info("Processando PDF, aguarde...")

    df = extract_data_from_pdf(uploaded_file)

    if df.empty:
        st.error("Nenhum lançamento encontrado. O PDF pode estar em imagem ou fora do padrão.")
    else:
        st.success(f"{len(df)} lançamentos identificados!")
        st.dataframe(df, use_container_width=True)

        # gerar excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Extrato")

        st.download_button(
            label="📥 Baixar Excel",
            data=output.getvalue(),
            file_name="extrato_plano_contas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
