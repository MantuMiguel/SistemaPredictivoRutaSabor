from django.shortcuts import render


def index(request):
    """Vista del Dataset Histórico de Pedidos. Solo renderiza la plantilla."""
    # AQUÍ LUEGO IRÁ LA LÓGICA DE PANDAS PARA LEER EL CSV.
    return render(request, 'datasets/index.html', {'modulo_activo': 'datasets'})
