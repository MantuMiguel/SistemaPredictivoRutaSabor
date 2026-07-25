from django.shortcuts import render

from .utils import construir_datos_dashboard


def inicio(request):
    """Vista de bienvenida del sistema. Solo renderiza la plantilla."""
    return render(request, 'dashboard/inicio.html', {'modulo_activo': 'inicio'})


def index(request):
    """Vista del Panel de Control: resumen ejecutivo con datos reales del sistema."""
    datos = construir_datos_dashboard()
    datos['modulo_activo'] = 'dashboard'
    return render(request, 'dashboard/index.html', datos)
