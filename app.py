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

# CSS para estilo escuro do painel
st.markdown("""
<style>

[data-testid="stAppViewContainer"] {
    background-color: #0f172a;
}

.sidebar-card {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
}

h1,h2,h3,h4,p,label {
    color: white;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# função carregar dados
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
    st.warning("Não foi possível carregar dados.")
    st.stop()


# -----------------------------
# layout principal
# -----------------------------
col_painel, col_mapa = st.columns([1,3])


# -----------------------------
# painel lateral
# -----------------------------
with col_painel:

    st.markdown("### 🚌 Rio Bus Tracker")
    st.caption("Tempo real · SMTR/RJ")

    linha = st.text_input("Linha do ônibus")

    buscar = st.button("🔎 Buscar no mapa")

    st.markdown("### Linhas rápidas")

    colA,colB,colC = st.columns(3)

    if colA.button("473"): linha="473"
    if colB.button("232"): linha="232"
    if colC.button("485"): linha="485"

    st.divider()

    if linha:

        tempo_max = df["datahora"].max()
        limite = tempo_max - timedelta(minutes=5)

        df_5min = df[df["datahora"] >= limite]
        df_linha = df_5min[df_5min["linha"].astype(str) == linha]

        if len(df_linha) == 0:
            st.warning("Nenhum ônibus encontrado")

        else:

            qtd_onibus = df_linha["ordem"].nunique()

            st.metric("Ônibus", qtd_onibus)


# -----------------------------
# mapa
# -----------------------------
with col_mapa:

    if linha and len(df_linha)>0:

        centro = [
            df_linha["latitude"].mean(),
            df_linha["longitude"].mean()
        ]

    else:

        centro = [-22.90,-43.20]

    mapa = folium.Map(location=centro, zoom_start=11)

    if linha and len(df_linha)>0:

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
                ).add_to(mapa)

            ultimo = dados_bus.iloc[-1]

            folium.CircleMarker(
                location=[ultimo["latitude"], ultimo["longitude"]],
                radius=6,
                color=cores[bus],
                fill=True,
            ).add_to(mapa)

    st_folium(
        mapa,
        width=None,
        height=800
    )
