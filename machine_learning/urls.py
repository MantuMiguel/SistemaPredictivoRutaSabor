from django.urls import path
from . import views

app_name = 'machine_learning'

urlpatterns = [
    path('', views.index, name='index'),
]
