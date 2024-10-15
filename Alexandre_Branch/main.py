import streamlit as st
import pandas as pd
import plotly.express as pe
import pymongo as pm
def decimal_to_degree(formato: str):
    if 'S' in formato or 'W' in formato or 'N' in formato or 'E' in formato:

        if 'S' in formato or 'W' in formato:
            negativo = True
        else:
            negativo = False
        formato = formato.replace('S', '').replace('N', '').replace('W', '').replace('E', '')
        try:
            horas = float(formato.split('°')[0])
        except:
            horas = 0.0
        try:
            minutos = float(formato.split('°')[1].split("'")[0])
        except:
            minutos = 0.0
        try:        
            segundos = float(formato.split("'")[1].removesuffix('"'))
        except:
            segundos = 0.0
        decimal = horas + (minutos / 60) + (segundos / 3600)
        if negativo:
            decimal *= -1
        return decimal
    else:
        return formato
def dcolor(value):
    if value > 50:
        return '#ff000055'
    elif value< 20:
        return '#00ff0055'
    else:
        return '#0000ff55'
#     if value > 50:
#         return [1.0, 0, 0, 0.2]
#     elif value< 20:
#         return [0, 1.0, 0, 0.2]
#     else:
#         return [0, 0, 1.0, 0.2]

st.set_page_config(page_title='Testando gráficos para PI' , layout='wide')
client = pm.MongoClient('mongodb://localhost:27017/')
db = client['teste']
collection = db['simlulandodados1']
# collection.insert_one(
#     {'carro': 20,
#      'moto': 30,
#      'media': 25,
#      'horario': '13:00',
#      'data': '10/01/2024',
     
#      }
# )
df = pd.DataFrame(collection.find())
df['data'] = pd.to_datetime(df['data'],format='%d/%m/%Y')
df['data'] = df['data'].dt.strftime('%d/%m/%Y')
try:
    df = df.sort_values('data')
    df = df.sort_values('horario')
except:
    pass
data = st.sidebar.selectbox("Data",df['data'].unique())
# horario = st.select_slider("Horario",df['horario'].unique())
# horarios = st.sidebar.selectbox('Horarios',df['horario'].unique())
df = df.drop('_id',axis=1)
df['latitude_atualizada'] = df['latitude'].apply(decimal_to_degree)
df['longitude_atualizada'] = df['longitude'].apply(decimal_to_degree)
 
df['color'] = df['total'].apply(dcolor)
# df['Total'] = df['carros']+df['motos']  
# df.reset_index(drop=False,inplace=True)
df_filtered = df[df["data"] == data]
df
# chartline1 = st.line_chart(df_filtered,x='horario',y=['carros','motos','Total'])
tent_plot = pe.line(df_filtered,'horario',[df_filtered['carros'],df_filtered['motos'],df_filtered['total']])
tent_plot1 = pe.line(df_filtered,'horario',[df_filtered['carros'],df_filtered['motos']])

# col1 = st.plotly_chart(tent_plot)
col1 = st.columns(2)
col2 = st.columns(2)
lista = []

with col1[0]:
    st.plotly_chart(tent_plot1)
with col1[1]:
    st.plotly_chart(tent_plot)

option = st.selectbox("Horários:",df_filtered['horario'])
df_filtered1 = df[(df['horario']==option) & (df['data'] == data)]


st.map(df_filtered1,latitude='latitude_atualizada',longitude='longitude_atualizada',size='total',color='color')

