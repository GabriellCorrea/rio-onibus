import streamlit as st
import pandas as pd
import folium
import random
from datetime import timedelta
from streamlit_folium import st_folium

st.title("Mapa de Ônibus - Últimos 5 minutos")

@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados_onibus.csv")
    df["datahora"] = pd.to_datetime(df["datahora"])
    return df

df = carregar_dados()

# FORMULÁRIO (evita atualização a cada tecla)
with st.form("consulta"):
    linha = st.text_input("Digite a linha de ônibus")
    submit = st.form_submit_button("Buscar")

if submit and linha:

    tempo_max = df["datahora"].max()
    limite = tempo_max - timedelta(minutes=5)

    df_5min = df[df["datahora"] >= limite]

    df_linha = df_5min[df_5min["linha"].astype(str) == linha]

    st.write("Registros da linha:", len(df_linha))

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
