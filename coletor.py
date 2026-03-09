import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# -----------------------------
# 1️⃣ definir intervalo de tempo
# -----------------------------

data_final = datetime.now(ZoneInfo("America/Sao_Paulo"))
data_inicial = data_final - timedelta(minutes=5)

data_final_str = data_final.strftime("%Y-%m-%d+%H:%M:%S")
data_inicial_str = data_inicial.strftime("%Y-%m-%d+%H:%M:%S")

url = f"https://dados.mobilidade.rio/gps/sppo?dataInicial={data_inicial_str}&dataFinal={data_final_str}"

print("URL:", url)

# -----------------------------
# 2️⃣ request API
# -----------------------------

response = requests.get(url)
print("Status:", response.status_code)

dados = response.json()
print("Registros:", len(dados))

# -----------------------------
# 3️⃣ criar dataframe
# -----------------------------

df = pd.DataFrame(dados)

# -----------------------------
# 4️⃣ converter timestamps
# -----------------------------

df["datahora"] = pd.to_datetime(df["datahora"], unit="ms", utc=True)
df["datahoraenvio"] = pd.to_datetime(df["datahoraenvio"], unit="ms", utc=True)
df["datahoraservidor"] = pd.to_datetime(df["datahoraservidor"], unit="ms", utc=True)

df["datahora"] = df["datahora"].dt.tz_convert("America/Sao_Paulo")
df["datahoraenvio"] = df["datahoraenvio"].dt.tz_convert("America/Sao_Paulo")
df["datahoraservidor"] = df["datahoraservidor"].dt.tz_convert("America/Sao_Paulo")

# -----------------------------
# 5️⃣ criar colunas de data
# -----------------------------

for col in ["datahora", "datahoraenvio", "datahoraservidor"]:

    df[f"data_{col}"] = df[col].dt.date
    df[f"hora_{col}"] = df[col].dt.hour
    df[f"minuto_{col}"] = df[col].dt.minute
    df[f"segundo_{col}"] = df[col].dt.second

# -----------------------------
# 6️⃣ remover colunas originais
# -----------------------------

df = df.drop(columns=["datahoraenvio", "datahoraservidor"], errors="ignore")

# -----------------------------
# 7️⃣ corrigir latitude e longitude
# -----------------------------

df["latitude"] = df["latitude"].str.replace(",", ".", regex=False).astype(float)
df["longitude"] = df["longitude"].str.replace(",", ".", regex=False).astype(float)

# -----------------------------
# 8️⃣ salvar CSV
# -----------------------------

df.to_csv("dados_onibus.csv", index=False)

print("CSV atualizado com sucesso")
