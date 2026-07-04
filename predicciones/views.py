from django.shortcuts import render


def index(request):
    """Vista de Predicción de Pedidos para Cocina. Solo renderiza la plantilla."""
    # AQUÍ LUEGO SE CONECTARÁ CON EL MODELO ENTRENADO.
    return render(request, 'predicciones/index.html', {'modulo_activo': 'predicciones'})
