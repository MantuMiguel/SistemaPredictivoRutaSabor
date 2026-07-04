from django.contrib import messages
from django.shortcuts import redirect, render

from datasets.models import DatasetUpload

from .models import TrainingRun
from .utils import NOMBRE_RANDOM_FOREST, NOMBRE_REGRESION_LINEAL, ejecutar_entrenamiento


def _entrenar(request, dataset_valido):
    run = TrainingRun.objects.create(dataset=dataset_valido, estado=TrainingRun.ESTADO_PENDIENTE)
    resultado = ejecutar_entrenamiento(dataset_valido)

    if resultado['estado'] == 'error':
        run.estado = TrainingRun.ESTADO_ERROR
        run.errores = resultado['errores']
        run.save()
        messages.error(request, 'Ocurrió un error durante el entrenamiento. Revisa el detalle abajo.')
        return

    run.estado = TrainingRun.ESTADO_ENTRENADO
    run.modelo_seleccionado_demanda = resultado['modelo_seleccionado_demanda']
    run.modelo_seleccionado_producto = resultado['modelo_seleccionado_producto']
    run.mae_demanda = resultado['mae_demanda']
    run.rmse_demanda = resultado['rmse_demanda']
    run.r2_demanda = resultado['r2_demanda']
    run.mae_producto = resultado['mae_producto']
    run.rmse_producto = resultado['rmse_producto']
    run.r2_producto = resultado['r2_producto']
    run.metricas_detalladas = resultado['metricas_detalladas']
    run.variables_usadas_demanda = resultado['variables_usadas_demanda']
    run.variables_usadas_producto = resultado['variables_usadas_producto']
    run.importancia_variables = resultado['importancia_variables']
    run.ruta_modelo_demanda = resultado['ruta_modelo_demanda']
    run.ruta_modelo_producto = resultado['ruta_modelo_producto']
    run.graficos = resultado['graficos']
    run.tiempo_entrenamiento_segundos = resultado['tiempo_entrenamiento_segundos']
    run.save()
    messages.success(request, 'Modelo entrenado correctamente.')


def index(request):
    """Vista del Modelo Predictivo: entrena, compara y guarda los modelos de demanda."""
    dataset_valido = DatasetUpload.objects.filter(
        estado_validacion=DatasetUpload.ESTADO_VALIDO
    ).order_by('-fecha_carga').first()

    if request.method == 'POST':
        if not dataset_valido:
            messages.error(request, 'Primero debes cargar y validar un dataset.')
            return redirect('machine_learning:index')
        _entrenar(request, dataset_valido)
        return redirect('machine_learning:index')

    entrenamiento = TrainingRun.objects.order_by('-fecha_entrenamiento').first()

    metricas = entrenamiento.metricas_detalladas if entrenamiento else {}
    metricas_demanda = metricas.get('demanda', {})
    metricas_producto = metricas.get('producto', {})

    return render(request, 'machine_learning/index.html', {
        'modulo_activo': 'machine_learning',
        'dataset_valido': dataset_valido,
        'entrenamiento': entrenamiento,
        'metricas_demanda_lr': metricas_demanda.get(NOMBRE_REGRESION_LINEAL),
        'metricas_demanda_rf': metricas_demanda.get(NOMBRE_RANDOM_FOREST),
        'metricas_producto_lr': metricas_producto.get(NOMBRE_REGRESION_LINEAL),
        'metricas_producto_rf': metricas_producto.get(NOMBRE_RANDOM_FOREST),
        'nombre_regresion_lineal': NOMBRE_REGRESION_LINEAL,
        'nombre_random_forest': NOMBRE_RANDOM_FOREST,
    })
