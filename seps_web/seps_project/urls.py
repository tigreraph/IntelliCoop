from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('ranking/', views.ranking, name='ranking'),
    path('segmentos/', views.segmentos, name='segmentos'),
    path('cooperativa/<str:ruc>/', views.cooperativa_detalle, name='cooperativa_detalle'),
    path('rakkun/', views.rakkun, name='rakkun'),
    path('rakkun-avatar/', views.rakkun_avatar, name='rakkun_avatar'),
    path('prediccion/', views.prediccion, name='prediccion'),
    path('api/rakkun/preguntar/', views.rakkun_chat, name='rakkun_chat'),
    path('api/tts/', views.tts, name='tts'),
]
