from django.urls import path
from . import views

app_name = 'predicciones'

urlpatterns = [
    path('', views.index, name='index'),
]
