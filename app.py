import streamlit as st
import pandas as pd
import folium
import random
from datetime import timedelta
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=30000, key="refresh")

# layout mais largo
st.set_page_config(layout="wide")

# título mais compacto
st.markdown("## 🚌 Mapa de Ônibus — Últimos 5 minutos")

# -----------------------------
# função para carregar dados
# -----------------------------
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

@st.cache_data(ttl=30)
def carregar_dados():

    data_final = datetime.now(ZoneInfo("America/Sao_Paulo"))
    data_inicial = data_final - timedelta(minutes=5)

    data_final_str = data_final.strftime("%Y-%m-%d+%H:%M:%S")
    data_inicial_str = data_inicial.strftime("%Y-%m-%d+%H:%M:%S")

    url = f"https://dados.mobilidade.rio/gps/sppo?dataInicial={data_inicial_str}&dataFinal={data_final_str}"

    r = requests.get(url)
    dados = r.json()

    df = pd.DataFrame(dados)

    df["datahora"] = pd.to_datetime(df["datahora"], unit="ms", utc=True)
    df["datahora"] = df["datahora"].dt.tz_convert("America/Sao_Paulo")

    df["latitude"] = df["latitude"].str.replace(",", ".").astype(float)
    df["longitude"] = df["longitude"].str.replace(",", ".").astype(float)

    return df

# -----------------------------
# formulário de consulta
# -----------------------------
with st.form("consulta"):
    col1, col2 = st.columns([5,1])

    with col1:
        linha = st.text_input("Digite a linha de ônibus")

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("Buscar")

# -----------------------------
# consulta e exibição
# -----------------------------
if submit and linha:

    # filtra últimos 5 minutos
    tempo_max = df["datahora"].max()
    limite = tempo_max - timedelta(minutes=5)
    df_5min = df[df["datahora"] >= limite]
    df_linha = df_5min[df_5min["linha"].astype(str) == linha]

    if len(df_linha) == 0:
        st.warning("Nenhum ônibus encontrado nos últimos 5 minutos")
    else:
        # -----------------------------
        # KPIs
        # -----------------------------
        qtd_onibus = df_linha["ordem"].nunique()
        hora_inicio = df_linha["datahora"].min()
        hora_final = df_linha["datahora"].max()

        k1, k2, k3 = st.columns(3)
        k1.metric("🚌 Ônibus ativos", qtd_onibus)
        k2.metric("⏱️ Hora inicial", hora_inicio.strftime("%H:%M:%S"))
        k3.metric("⏱️ Hora final", hora_final.strftime("%H:%M:%S"))

        st.divider()

        # -----------------------------
        # mapa
        # -----------------------------
        centro = [df_linha["latitude"].mean(), df_linha["longitude"].mean()]
        mapa = folium.Map(location=centro, zoom_start=12)

        onibus_ids = df_linha["ordem"].unique()
        random.seed(42)
        cores = {bus: "#{:06x}".format(random.randint(0, 0xFFFFFF)) for bus in onibus_ids}

        for bus in onibus_ids:
            dados_bus = df_linha[df_linha["ordem"] == bus].sort_values("datahora")
            pontos = list(zip(dados_bus["latitude"], dados_bus["longitude"]))

            # desenha rota
            if len(pontos) > 1:
                folium.PolyLine(pontos, color=cores[bus], weight=4, tooltip=f"Ônibus {bus}").add_to(mapa)

            # marcador do último ponto
            ultimo = dados_bus.iloc[-1]
            folium.CircleMarker(
                location=[ultimo["latitude"], ultimo["longitude"]],
                radius=6,
                color=cores[bus],
                fill=True,
                popup=f"Linha {linha} | Ônibus {bus}"
            ).add_to(mapa)

        # exibe mapa
        st_folium(
            mapa,
            width=None,
            height=650,
            returned_objects=[],
            key="mapa_onibus"
        )
