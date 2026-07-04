from datetime import date

from django.contrib import messages
from django.shortcuts import redirect, render

from .models import PredictionResult
from .utils import (
    generar_prediccion,
    obtener_ultimo_dataset_valido,
    obtener_ultimo_training_run_entrenado,
)


def _procesar_consulta(request):
    fecha_str = request.POST.get('fecha_prediccion')
    franja_horaria = request.POST.get('franja_horaria', 'Todo el día')
    promocion_activa = request.POST.get('promocion_activa', 'No')
    tipo_promocion = request.POST.get('tipo_promocion', 'Ninguna')
    descuento_pct = request.POST.get('descuento_pct', '0')
    clima = request.POST.get('clima', 'Soleado')

    if not fecha_str:
        messages.error(request, 'Selecciona una fecha para consultar la predicción.')
        return

    try:
        fecha_prediccion = date.fromisoformat(fecha_str)
        descuento_pct = int(descuento_pct)
    except (ValueError, TypeError):
        messages.error(request, 'Los datos del formulario no son válidos.')
        return

    parametros_entrada = {
        'fecha_prediccion': fecha_str,
        'franja_horaria': franja_horaria,
        'promocion_activa': promocion_activa,
        'tipo_promocion': tipo_promocion,
        'descuento_pct': descuento_pct,
        'clima': clima,
    }

    resultado = generar_prediccion(
        fecha_prediccion, franja_horaria, clima, promocion_activa, tipo_promocion, descuento_pct
    )

    if resultado['estado'] == 'error':
        PredictionResult.objects.create(
            fecha_prediccion=fecha_prediccion,
            franja_horaria=franja_horaria,
            parametros_entrada=parametros_entrada,
            estado=PredictionResult.ESTADO_ERROR,
            errores=resultado['errores'],
        )
        messages.error(request, resultado['errores'][0] if resultado['errores'] else 'Ocurrió un error al predecir.')
        return

    PredictionResult.objects.create(
        training_run=resultado['training_run'],
        fecha_prediccion=fecha_prediccion,
        franja_horaria=franja_horaria,
        pedidos_estimados=resultado['pedidos_estimados'],
        franja_critica=resultado['franja_critica'],
        nivel_demanda=resultado['nivel_demanda'],
        productos_top=resultado['productos_top'],
        recomendaciones=resultado['recomendaciones'],
        parametros_entrada=parametros_entrada,
        resultado_detallado={
            'resultado_por_franja': resultado['resultado_por_franja'],
            'graficos': resultado['graficos'],
            'productos_operativos_top3': resultado['productos_operativos_top3'],
            'productos_lideres_texto': resultado['productos_lideres_texto'],
        },
        modelo_demanda_usado=resultado['modelo_demanda_usado'],
        modelo_producto_usado=resultado['modelo_producto_usado'],
        estado=PredictionResult.ESTADO_GENERADO,
    )
    messages.success(request, 'Predicción generada correctamente.')


def index(request):
    """Vista de Predicciones: consulta demanda futura usando el modelo ya entrenado."""
    training_run = obtener_ultimo_training_run_entrenado()
    dataset_valido = obtener_ultimo_dataset_valido()
    sistema_listo = training_run is not None and dataset_valido is not None

    if request.method == 'POST':
        if not sistema_listo:
            messages.error(request, 'Primero debes entrenar un modelo desde el módulo Modelo Predictivo.')
            return redirect('predicciones:index')
        _procesar_consulta(request)
        return redirect('predicciones:index')

    prediccion = PredictionResult.objects.order_by('-fecha_consulta').first()

    return render(request, 'predicciones/index.html', {
        'modulo_activo': 'predicciones',
        'sistema_listo': sistema_listo,
        'training_run': training_run,
        'dataset_valido': dataset_valido,
        'prediccion': prediccion,
        'hoy': date.today().isoformat(),
    })
