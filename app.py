import streamlit as st
import pandas as pd
import folium
import random
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# -----------------------------
# CSS DO PAINEL
# -----------------------------

st.markdown("""
<style>

[data-testid="stSidebar"]{
    background-color:#081021;
}

.stTextInput input{
    background:#0f1a30;
    border-radius:12px;
}

.stButton>button{
    width:100%;
    border-radius:14px;
    background:linear-gradient(90deg,#19d3c5,#2aa5d8);
    color:black;
    font-weight:600;
    border:none;
}

.kpi-card{
    background:#0f1a30;
    border-radius:15px;
    padding:20px;
    border:1px solid #1f2a44;
}

.kpi-number{
    font-size:30px;
    font-weight:700;
}

.kpi-label{
    color:#8aa4d8;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# FUNÇÃO ORIGINAL
# -----------------------------

@st.cache_data(ttl=30)
def carregar_dados():

    data_final = datetime.now(ZoneInfo("America/Sao_Paulo"))
    data_inicial = data_final - timedelta(minutes=5)

    data_final_str = data_final.strftime("%Y-%m-%d+%H:%M:%S")
    data_inicial_str = data_inicial.strftime("%Y-%m-%d+%H:%M:%S")

    url = f"https://dados.mobilidade.rio/gps/sppo?dataInicial={data_inicial_str}&dataFinal={data_final_str}"

    r = requests.get(url)

    if r.status_code != 200:
        return pd.DataFrame()

    dados = r.json()
    df = pd.DataFrame(dados)

    if df.empty:
        return df

    df["datahora"] = pd.to_datetime(df["datahora"], unit="ms", utc=True)
    df["datahora"] = df["datahora"].dt.tz_convert("America/Sao_Paulo")

    df["latitude"] = df["latitude"].str.replace(",", ".", regex=False).astype(float)
    df["longitude"] = df["longitude"].str.replace(",", ".", regex=False).astype(float)

    return df


df = carregar_dados()

if df.empty:
    st.warning("Erro ao buscar dados")
    st.stop()

# -----------------------------
# SESSION
# -----------------------------

if "linha" not in st.session_state:
    st.session_state.linha = ""

# -----------------------------
# SIDEBAR (PAINEL)
# -----------------------------

with st.sidebar:

    st.title("Rio Bus Tracker")
    st.caption("Tempo real · SMTR/RJ")

    st.markdown("### LINHA DO ÔNIBUS")

    linha_input = st.text_input("", value=st.session_state.linha)

    if st.button("Buscar no mapa"):
        st.session_state.linha = linha_input

    st.markdown("### LINHAS RÁPIDAS")

    c1,c2,c3 = st.columns(3)

    if c1.button("473"):
        st.session_state.linha="473"

    if c2.button("232"):
        st.session_state.linha="232"

    if c3.button("485"):
        st.session_state.linha="485"

    c4,c5,c6 = st.columns(3)

    if c4.button("3001"):
        st.session_state.linha="3001"

    if c5.button("867"):
        st.session_state.linha="867"

    if c6.button("415"):
        st.session_state.linha="415"

    linha = st.session_state.linha

    if linha:

        tempo_max = df["datahora"].max()
        limite = tempo_max - timedelta(minutes=5)

        df_5min = df[df["datahora"] >= limite]
        df_linha = df_5min[df_5min["linha"].astype(str) == linha]

        if len(df_linha)>0:

            qtd_onibus = df_linha["ordem"].nunique()

            hora_inicio = df_linha["datahora"].min()
            hora_final = df_linha["datahora"].max()

            st.markdown(f"### LINHA {linha}")

            k1,k2 = st.columns(2)

            with k1:
                st.markdown(f"""
                <div class="kpi-card">
                <div class="kpi-number">{qtd_onibus}</div>
                <div class="kpi-label">Ônibus</div>
                </div>
                """,unsafe_allow_html=True)

            with k2:
                st.markdown(f"""
                <div class="kpi-card">
                <div class="kpi-number">{hora_inicio.strftime("%H:%M:%S")}</div>
                <div class="kpi-label">Início dos dados</div>
                </div>
                """,unsafe_allow_html=True)

            st.markdown(f"""
            <div class="kpi-card">
            <div class="kpi-number">{hora_final.strftime("%H:%M:%S")}</div>
            <div class="kpi-label">Último dado coletado</div>
            </div>
            """,unsafe_allow_html=True)

# -----------------------------
# MAPA
# -----------------------------

linha = st.session_state.linha

if linha:

    tempo_max = df["datahora"].max()
    limite = tempo_max - timedelta(minutes=5)

    df_5min = df[df["datahora"] >= limite]
    df_linha = df_5min[df_5min["linha"].astype(str) == linha]

    if len(df_linha)>0:

        centro = [
            df_linha["latitude"].mean(),
            df_linha["longitude"].mean()
        ]

    else:
        centro=[-22.90,-43.20]

else:
    centro=[-22.90,-43.20]

mapa = folium.Map(location=centro, zoom_start=12)

if linha and len(df_linha)>0:

    onibus_ids = df_linha["ordem"].unique()

    random.seed(42)

    cores = {
        bus:"#{:06x}".format(random.randint(0,0xFFFFFF))
        for bus in onibus_ids
    }

    for bus in onibus_ids:

        dados_bus = df_linha[df_linha["ordem"]==bus].sort_values("datahora")

        pontos=list(zip(dados_bus["latitude"],dados_bus["longitude"]))

        if len(pontos)>1:

            folium.PolyLine(
                pontos,
                color=cores[bus],
                weight=4
            ).add_to(mapa)

        ultimo=dados_bus.iloc[-1]

        folium.CircleMarker(
            location=[ultimo["latitude"],ultimo["longitude"]],
            radius=6,
            color=cores[bus],
            fill=True
        ).add_to(mapa)

st_folium(
    mapa,
    height=800,
    width=None
)
