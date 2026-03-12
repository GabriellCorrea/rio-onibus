import streamlit as st
import pandas as pd
import folium
import random
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_folium import st_folium

# --------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# --------------------------------------------------

st.set_page_config(layout="wide")

# --------------------------------------------------
# CSS DO PAINEL (visual igual ao da imagem)
# --------------------------------------------------

st.markdown("""
<style>

.stApp{
    background-color:#050b18;
}

.panel{
    background-color:#081021;
    padding:25px;
    border-right:1px solid #1f2a44;
    height:100vh;
}

.title{
    font-size:26px;
    font-weight:700;
    color:white;
}

.subtitle{
    color:#7aa0d8;
    font-size:14px;
}

.section{
    margin-top:30px;
    color:#2ef2d1;
    font-weight:600;
    letter-spacing:1px;
}

.quick{
    background:#111a2e;
    border-radius:20px;
    padding:6px 14px;
    margin:4px;
    display:inline-block;
    color:#a9c4ff;
    border:1px solid #26395c;
}

.card{
    background:#0f1a30;
    border-radius:15px;
    padding:20px;
    border:1px solid #1f2a44;
}

.metric-big{
    font-size:32px;
    font-weight:700;
    color:white;
}

.metric-label{
    color:#7c96c5;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# FUNÇÃO ORIGINAL (NÃO ALTERADA)
# --------------------------------------------------

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

    df["datahora"] = pd.to_datetime(df["datahora"], unit="ms", utc=True)
    df["datahora"] = df["datahora"].dt.tz_convert("America/Sao_Paulo")

    df["latitude"] = df["latitude"].str.replace(",", ".", regex=False).astype(float)
    df["longitude"] = df["longitude"].str.replace(",", ".", regex=False).astype(float)

    return df

# --------------------------------------------------
# CARREGAR DADOS
# --------------------------------------------------

df = carregar_dados()

if df.empty:
    st.warning("Não foi possível carregar dados da API.")
    st.stop()

# --------------------------------------------------
# SESSION STATE (MESMA LÓGICA)
# --------------------------------------------------

if "linha" not in st.session_state:
    st.session_state.linha = ""

# --------------------------------------------------
# LAYOUT PRINCIPAL
# --------------------------------------------------

col_painel, col_mapa = st.columns([1.1,3.5])

# --------------------------------------------------
# PAINEL (VISUAL)
# --------------------------------------------------

with col_painel:

    st.markdown('<div class="panel">', unsafe_allow_html=True)

    st.markdown('<div class="title">Rio Bus Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Tempo real · SMTR/RJ</div>', unsafe_allow_html=True)

    st.markdown('<div class="section">LINHA DO ÔNIBUS</div>', unsafe_allow_html=True)

    linha_input = st.text_input("", value=st.session_state.linha)

    if st.button("Buscar no mapa"):
        st.session_state.linha = linha_input

    st.markdown('<div class="section">LINHAS RÁPIDAS</div>', unsafe_allow_html=True)

    st.markdown("""
    <span class="quick">473</span>
    <span class="quick">232</span>
    <span class="quick">485</span>
    <span class="quick">SP</span>
    <span class="quick">2336</span>
    <span class="quick">3001</span>
    <span class="quick">867</span>
    <span class="quick">415</span>
    """, unsafe_allow_html=True)

    linha = st.session_state.linha

    if linha:

        tempo_max = df["datahora"].max()
        limite = tempo_max - timedelta(minutes=5)

        df_5min = df[df["datahora"] >= limite]
        df_linha = df_5min[df_5min["linha"].astype(str) == linha]

        st.markdown(f'<div class="section">LINHA {linha}</div>', unsafe_allow_html=True)

        if len(df_linha) > 0:

            qtd_onibus = df_linha["ordem"].nunique()

            c1,c2 = st.columns(2)

            with c1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big">{qtd_onibus}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Ônibus</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with c2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-big">0 km/h</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Vel. média</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# MAPA (MESMA LÓGICA ORIGINAL)
# --------------------------------------------------

with col_mapa:

    if st.session_state.linha:

        linha = st.session_state.linha

        tempo_max = df["datahora"].max()
        limite = tempo_max - timedelta(minutes=5)

        df_5min = df[df["datahora"] >= limite]
        df_linha = df_5min[df_5min["linha"].astype(str) == linha]

        if len(df_linha) > 0:

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
                        weight=4
                    ).add_to(mapa)

                ultimo = dados_bus.iloc[-1]

                folium.CircleMarker(
                    location=[ultimo["latitude"], ultimo["longitude"]],
                    radius=6,
                    color=cores[bus],
                    fill=True
                ).add_to(mapa)

            st_folium(mapa, height=800, width=None)
