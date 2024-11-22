from django.urls import path
from .views import density_map_view,enviar_coluna_data,recebe_data,enviar_coluna_horarios,pagRelatorio#,update_map

app_name = 'grafico'  # Define o namespace do app


urlpatterns = [
    path('density-map/', density_map_view, name='density_map_view'),
    path('density-map/requisicao/',enviar_coluna_data,name='enviar_coluna_data'),
    path('density-map/receber-dado/',recebe_data, name='recebe_data'),
    #path('mapa_fetch/',update_map, name='update_map'),
    path('density-map/requisicao/horarios',enviar_coluna_horarios,name='enviar_coluna_horarios'),
    path('relatorio',pagRelatorio,name='pagRelatorio'),
    
    # path('login/',login_view, name='login')  # Rota para login

]
