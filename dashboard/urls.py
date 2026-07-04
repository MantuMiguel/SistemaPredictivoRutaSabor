from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('panel-de-control/', views.index, name='index'),
]
