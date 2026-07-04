from django.shortcuts import render


def index(request):
    """Vista del Modelo Predictivo de Demanda. Solo renderiza la plantilla."""
    # AQUÍ LUEGO IRÁ LA LÓGICA DE SCIKIT-LEARN.
    return render(request, 'machine_learning/index.html', {'modulo_activo': 'machine_learning'})
