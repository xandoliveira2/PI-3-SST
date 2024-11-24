from django.shortcuts import render
from django.http import HttpResponse,JsonResponse,QueryDict
from django import forms
import django as dj
import plotly.express as pe
from plotly.offline import plot
import pandas as pd
import pymongo as pm
from django.views.decorators.csrf import csrf_exempt
import json
import plotly.graph_objs as go
import numpy as np
import os
from django.conf import settings
import requests
from time import sleep
def tudoNumerico(palavra:str):
    palavra = str(palavra)
    for i in palavra:
        if not i.isdigit():
            return False
    return True

def obter_endereco_por_cep(cep):
    try:
        if tudoNumerico(cep):
            url = f"https://viacep.com.br/ws/{cep}/json/"
            resposta = requests.get(url,timeout=0.1)
        elif '-' in cep:
            cep = cep.replace("-", "")
            url = f"https://viacep.com.br/ws/{cep}/json/"
            resposta = requests.get(url,timeout=0.1)
        else:
            return cep
        if resposta.status_code == 200:
            dados = resposta.json()
            if "erro" in dados:
                return f"CEP {cep} não encontrado."

            return dados.get("logradouro", "Rua não encontrada.")
        else:
            return "Erro ao buscar dados."
    except:
        print('entrou no except de erro na API')
        try:
            # Verifique se cep é uma string numérica válida antes de tentar converter
            cep_int = int(cep)  # strip() para remover espaços em branco
            dicionario = {
                13974503: "Avenida Castro Alves",
                13974080: "Tereza Lera Paoletti",
            }
            print(cep_int,'  < --cep int')
            return dicionario.get(cep_int,'CEP não encontrado no bd')
        except Exception as e:
            print('entrou no except 2, mas aqui nao vejo motivo p quebrar')
            print(e, '<--erro')
            # Caso não consiga converter para inteiro, retorne uma mensagem de erro
            return e
    
def obter_endereco_delay(cep):
    return obter_endereco_por_cep(cep)
   

def hours_to_decimals_convertion(formato:str):
    """
    formato : horas:minutos:segundos:direção (latitude e longitude)\n
    exemplo: 29°30'29"W\n
    Converte latitude e longitude no formato decimal para aplicar no gráfico de mapa
    que puxa por valores decimais
    """
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
def dcolor(value:int|float,valores:list) -> str:
    """Gera o a cor o qual aquele valor será representado no mapa, cujo valores são\n
    definidos pelo usuário em ordem decrescente, ou seja, o primeiro valor\n
    da lista será o vermelho,laranja,amarelo,azul e verde respectivamente\n
    opacidade 55 representado em hexadecimal equivale a 33% de opacidade"""
    if value >= int(valores[0]):
        return '#ff0000'
    elif value >= int(valores[1]):
        return '#ffa500'
    elif value >= int(valores[2]):
        return '#ffff00'
    elif value >= int(valores[3]):
        return '#0000ff'
    else:
        return '#00ff00'

   
    
    
    
client = pm.MongoClient('mongodb://localhost:27017/')
db = client['pi']
collection = db['autoflow']
df = pd.DataFrame(collection.find())
df['latitude_atualizada'] = df['latitude'].apply(hours_to_decimals_convertion)
df['longitude_atualizada'] = df['longitude'].apply(hours_to_decimals_convertion)
# df['color'] = df['total'].apply(dcolor)

def aplicarCores(dataframe = df,ParametrosValores=[50,35,25,15]):
    dataframe['color'] = dataframe['total'].apply(lambda value: dcolor(int(value), ParametrosValores))



df['rua'] = df['rua'].apply(obter_endereco_delay)
print(df)
df['data'] = pd.to_datetime(df['data'],format='%d/%m/%Y') 
df['data'] = df['data'].dt.strftime('%d/%m/%Y') 
df['size_column'] = df['total'].apply(lambda x: x if x != 0 else 0.1)
df = df.sort_values('data')

@csrf_exempt
def recebe_data(request):
    if request.method == "POST":
        dados = json.loads(request.body)
        dado_recebido = dados.get('data')
        
        return JsonResponse({'status':'sucesso','dado_recebido':dado_recebido})
    else:
        return JsonResponse({'erro':'Método não permitido'},status=405)


def enviar_coluna_data(request):

    coluna_dados = df['data'].unique().tolist()
   
    return JsonResponse({'dados':coluna_dados})

def enviar_coluna_rua(request):
    data = request.GET.get('param1')
    
    coluna_rua = df[df['data'] == data]['rua'].unique().tolist()

    return JsonResponse({'ruas':coluna_rua})

def enviar_coluna_horarios(request):
    data = request.GET.get('param1')
    horas = df[df['data']==data]['horario'].unique().tolist()
    horas = sorted(horas)
    
    return JsonResponse({'horas':horas})

contadorPagina = 0
def density_map_view(request):
    global contadorPagina
    filtro_data = request.GET.get('param1')
    filtro_hora = request.GET.get('param2')
    filtro_veiculos = request.GET.get('param3', 'carros motos')#('param3', 'carros motos')  # Default para 'carros motos'
    ruas = request.GET.get('ruas')
    ruas = ruas.split(',') if ruas else []
    

    filtro_veiculos = filtro_veiculos.split()
    while '' in filtro_veiculos:
        filtro_veiculos.remove('')
    
    base = ['rua','total'] + filtro_veiculos

    df_filtered1 = df[(df['horario'] == filtro_hora) & (df['data'] == filtro_data)]
    
    
    
    df_filtered1['total'] = 0
    for item in filtro_veiculos:
        df_filtered1['total'] += df_filtered1[item]

    df_filtered1['size_column'] = df_filtered1['total'].apply(lambda x: x if x != 0 else 0.5)
    
    # Aplica cores antes de usar no gráfico
    if 'param4' in request.GET:
        valores = request.GET.get('param4').split('_')
        aplicarCores(df_filtered1, valores)
        data = {
            "vermelho": valores[0],
            "laranja": valores[1],
            "amarelo": valores[2],
            "azul": valores[3],
            "verde": int(valores[3]) - 1
        }
    elif contadorPagina == 0:
        aplicarCores(df_filtered1)
        data = {
            "vermelho": 50,
            "laranja": 35,
            "amarelo": 25,
            "azul": 15,
            "verde": 14
        }
        contadorPagina +=1
    else:
        listaCor = []
        with open('static/cores.json', 'r') as jsonFile:
            data = json.load(jsonFile)
            listaCor.append(int(data["vermelho"]))
            listaCor.append(int(data["laranja"]))
            listaCor.append(int(data["amarelo"]))
            listaCor.append(int(data["azul"]))
        aplicarCores(df_filtered1,listaCor)
    # Salva as cores no arquivo JSON
    file_path = os.path.join(settings.BASE_DIR, 'static', 'cores.json')
    with open(file_path, 'w') as jsonFile:
        json.dump(data, jsonFile, indent=4)
    
    df_filtered1 = df_filtered1[df_filtered1['rua'].isin(ruas)] #<-- essa linha daqui 
    density_map = pe.scatter_mapbox(
        df_filtered1,
        lat='latitude_atualizada',
        lon='longitude_atualizada',
        mapbox_style="carto-darkmatter",
        center={'lat': -22.436491574441884, 'lon': -46.823405867130425},
        zoom=14,
        size='size_column',
        range_color=[10, 60],
        color_continuous_scale='Viridis',
        opacity=0.6,
        custom_data=base,#['rua','total', 'motos', 'carros'],
        color='color',
        color_discrete_map={'#ff0000': 'red', '#00ff00': 'green', '#ffa500': 'orange', '#0000ff': 'blue','#ffff00':'yellow'},
    )

    hover_template_str = ""
    for i, j in enumerate(base):
        hover_template_str += f"{base[i].capitalize()}: %"+"{"+"customdata["+f"{i}"+"]"+"}<br>"
    hover_template_str+='<extra></extra>'
    density_map.update_traces(hovertemplate = hover_template_str)
    density_map.update_layout(showlegend=False)
    grafico_html = plot(density_map,output_type='div')
 
    
    return render(request, 'density_map.html',{'grafico_html':grafico_html})





def pagRelatorio(request):
    return render(request,'relatorio.html')
# views here



def login_view(request):
    return render(request, 'login.html')


def home(request):
    return render(request, 'home.html')
