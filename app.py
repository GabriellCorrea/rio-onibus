import streamlit as st
import pandas as pd
import folium
import random
from datetime import timedelta
from streamlit_folium import st_folium

# layout mais largo
st.set_page_config(layout="wide")

# título mais compacto
st.markdown("## 🚌 Mapa de Ônibus — últimos 5 minutos")

@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados_onibus.csv")
    df["datahora"] = pd.to_datetime(df["datahora"])
    return df

df = carregar_dados()

# -----------------------------
# formulário
# -----------------------------

with st.form("consulta"):
    col1, col2 = st.columns([3,1])

    with col1:
        linha = st.text_input("Digite a linha de ônibus")

    with col2:
        submit = st.form_submit_button("Buscar")

# -----------------------------
# consulta
# -----------------------------

if submit and linha:

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

        k1, k2, k3 = st.columns(3)

        k1.metric("🚌 Ônibus ativos", qtd_onibus)
        k2.metric("⏱️ Hora inicial", hora_inicio.strftime("%H:%M:%S"))
        k3.metric("⏱️ Hora final", hora_final.strftime("%H:%M:%S"))

        st.divider()

        # -----------------------------
        # mapa
        # -----------------------------

        centro = [
            df_linha["latitude"].mean(),
            df_linha["longitude"].mean()
        ]

        mapa = folium.Map(location=centro, zoom_start=12)

        onibus_ids = df_linha["ordem"].unique()

        random.seed(42)

        cores = {}
        for bus in onibus_ids:
            cores[bus] = "#{:06x}".format(random.randint(0, 0xFFFFFF))

        for bus in onibus_ids:

            dados_bus = df_linha[df_linha["ordem"] == bus].sort_values("datahora")

            pontos = list(zip(dados_bus["latitude"], dados_bus["longitude"]))

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
            width=None,   # ocupa largura toda
            height=650,
            returned_objects=[]
        )

    if len(df_linha) == 0:
        st.write("Nenhum ônibus encontrado")
    else:

        centro = [
            df_linha["latitude"].mean(),
            df_linha["longitude"].mean()
        ]

        mapa = folium.Map(location=centro, zoom_start=12)

        onibus_ids = df_linha["ordem"].unique()

        random.seed(42)

        cores = {}
        for bus in onibus_ids:
            cores[bus] = "#{:06x}".format(random.randint(0, 0xFFFFFF))

        for bus in onibus_ids:

            dados_bus = df_linha[df_linha["ordem"] == bus].sort_values("datahora")

            pontos = list(zip(dados_bus["latitude"], dados_bus["longitude"]))

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
        width=1000,
        height=600,
        returned_objects=[]
    )
