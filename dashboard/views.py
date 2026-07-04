from django.shortcuts import render


def inicio(request):
    """Vista de bienvenida del sistema. Solo renderiza la plantilla."""
    return render(request, 'dashboard/inicio.html', {'modulo_activo': 'inicio'})


def index(request):
    """Vista del Panel de Control. Solo renderiza la plantilla."""
    return render(request, 'dashboard/index.html', {'modulo_activo': 'dashboard'})
