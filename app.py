import streamlit as st
import pandas as pd
import folium
import random
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_folium import st_folium

# -----------------------------
# configuração da página
# -----------------------------
st.set_page_config(layout="wide")

# -----------------------------
# CSS VISUAL
# -----------------------------
st.markdown("""
<style>

/* título */
.titulo{
    font-size:38px;
    font-weight:700;
    margin-bottom:5px;
}

/* subtitulo */
.subtitulo{
    color:#9ca3af;
    margin-bottom:25px;
}

/* caixa de input */
.stTextInput input{
    height:55px;
    border-radius:14px;
    font-size:18px;
}

/* botão */
.stButton button{
    height:55px;
    border-radius:14px;
    font-size:18px;
    font-weight:600;
}

/* KPI */
.kpi-container{
    margin-top:25px;
    margin-bottom:20px;
}

.kpi{
    padding:10px 0;
}

.kpi-title{
    color:#94a3b8;
    font-size:16px;
}

.kpi-value{
    font-size:48px;
    font-weight:700;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# função para carregar dados
# -----------------------------
@st.cache_data(ttl=30, show_spinner=False)
def carregar_dados():

    data_final = datetime.now(ZoneInfo("America/Sao_Paulo"))
    data_inicial = data_final - timedelta(minutes=5)

    data_final_str = data_final.strftime("%Y-%m-%d+%H:%M:%S")
    data_inicial_str = data_inicial.strftime("%Y-%m-%d+%H:%M:%S")

    url = f"https://dados.mobilidade.rio/gps/sppo?dataInicial={data_inicial_str}&dataFinal={data_final_str}"

    response = requests.get(url)

    if response.status_code != 200:
        return pd.DataFrame()

    dados = response.json()

    df = pd.DataFrame(dados)

    if df.empty:
        return df

    # converter timestamps
    df["datahora"] = pd.to_datetime(df["datahora"], unit="ms", utc=True)
    df["datahora"] = df["datahora"].dt.tz_convert("America/Sao_Paulo")

    # corrigir latitude e longitude
    df["latitude"] = df["latitude"].str.replace(",", ".", regex=False).astype(float)
    df["longitude"] = df["longitude"].str.replace(",", ".", regex=False).astype(float)

    return df


# -----------------------------
# carregar dados
# -----------------------------
with st.spinner("Atualizando posições dos ônibus..."):
    df = carregar_dados()

if df.empty:
    st.warning("Não foi possível carregar dados da API.")
    st.stop()


# -----------------------------
# guardar linha pesquisada
# -----------------------------
if "linha" not in st.session_state:
    st.session_state.linha = ""


# -----------------------------
# HEADER
# -----------------------------
st.markdown('<div class="titulo">🚌 Mapa de Ônibus — Últimos 5 minutos</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Dados em tempo real — SMTR/RJ</div>', unsafe_allow_html=True)

# -----------------------------
# formulário
# -----------------------------
with st.form("consulta"):

    col1, col2 = st.columns([6,1])

    with col1:
        linha_input = st.text_input(
            "Digite a linha de ônibus",
            value=st.session_state.linha,
            label_visibility="collapsed",
            placeholder="Digite a linha (ex: 485)"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("🔎 Buscar")

if submit:
    st.session_state.linha = linha_input

linha = st.session_state.linha


# -----------------------------
# consulta
# -----------------------------
if linha:

    tempo_max = df["datahora"].max()
    limite = tempo_max - timedelta(minutes=5)

    df_5min = df[df["datahora"] >= limite]
    df_linha = df_5min[df_5min["linha"].astype(str) == linha]

    if len(df_linha) == 0:
        st.warning("Nenhum ônibus encontrado nos últimos 5 minutos")

    else:

        # KPIs
        qtd_onibus = df_linha["ordem"].nunique()
        hora_inicio = df_linha["datahora"].min()
        hora_final = df_linha["datahora"].max()

        st.markdown('<div class="kpi-container">', unsafe_allow_html=True)

        k1,k2,k3 = st.columns(3)

        with k1:
            st.markdown(f"""
            <div class="kpi">
                <div class="kpi-title">🚌 Ônibus ativos</div>
                <div class="kpi-value">{qtd_onibus}</div>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            st.markdown(f"""
            <div class="kpi">
                <div class="kpi-title">⏱ Hora inicial</div>
                <div class="kpi-value">{hora_inicio.strftime("%H:%M:%S")}</div>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            st.markdown(f"""
            <div class="kpi">
                <div class="kpi-title">⏱ Hora final</div>
                <div class="kpi-value">{hora_final.strftime("%H:%M:%S")}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------
# mapa
# -----------------------------
if linha and not df_linha.empty:

    centro = [
        df_linha["latitude"].mean(),
        df_linha["longitude"].mean()
    ]

    mapa = folium.Map(location=centro, zoom_start=12)

    onibus_ids = df_linha["ordem"].unique()

    random.seed(42)
    cores = {
        bus: "#{:06x}".format(random.randint(0,0xFFFFFF))
        for bus in onibus_ids
    }

    for bus in onibus_ids:

        dados_bus = df_linha[df_linha["ordem"] == bus].sort_values("datahora")

        pontos = list(zip(dados_bus["latitude"],dados_bus["longitude"]))

        if len(pontos) > 1:
            folium.PolyLine(
                pontos,
                color=cores[bus],
                weight=4,
                tooltip=f"Ônibus {bus}"
            ).add_to(mapa)

        ultimo = dados_bus.iloc[-1]

        folium.CircleMarker(
            location=[ultimo["latitude"], ultimo["longitude"]],
            radius=6,
            color=cores[bus],
            fill=True,
            popup=f"Linha {linha} | Ônibus {bus}"
        ).add_to(mapa)

    st_folium(
        mapa,
        width=None,
        height=650,
        key="mapa_onibus"
    )
