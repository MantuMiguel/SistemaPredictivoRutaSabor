"""
Utilidades del Panel de Control (Dashboard).

El Dashboard NO entrena modelos ni carga datasets: solo lee lo que ya existe
(último DatasetUpload válido, último TrainingRun entrenado, último
PredictionResult generado) y, si hay modelo entrenado, calcula un mapa de
calor semanal de apoyo usando ÚNICAMENTE el modelo de demanda total.

Reutiliza (sin duplicar) la lógica de predicciones/utils.py para construir
el contexto histórico y las filas de entrada del modelo.
"""
from datetime import date, timedelta

import pandas as pd

from machine_learning.models import TrainingRun
from predicciones.models import PredictionResult
from predicciones.utils import (
    ORDEN_FRANJAS,
    calcular_planificacion_personal_por_franja,
    calcular_variables_clima,
    calcular_variables_temporales,
    cargar_pipeline_demanda,
    construir_contexto_historico,
    construir_fila_demanda,
    nivel_demanda_franja,
    obtener_ultimo_dataset_valido,
    obtener_ultimo_training_run_entrenado,
)

DIAS_SEMANA_ES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

# El Dashboard no tiene formulario: usa siempre estos valores por defecto para
# las variables que en Predicciones sí puede elegir el usuario.
CLIMA_DEFECTO = 'Soleado'
PROMOCION_DEFECTO = 'No'

CATEGORIAS_RECOMENDACION = ('abastecimiento', 'cocina', 'personal', 'operacion')


def calcular_semana_actual(hoy=None):
    """Lunes y domingo de la semana actual (semana de lunes a domingo)."""
    hoy = hoy or date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)
    return lunes, domingo


def _generar_mapa_calor(pipeline_demanda, contexto):
    """
    Predice pedidos estimados para cada (día de la semana actual) x (franja),
    usando un único predict() por lote (21 filas) en vez de 21 llamadas
    separadas, ya que esto se recalcula en cada carga del Dashboard.
    """
    variables_clima = calcular_variables_clima(CLIMA_DEFECTO)
    lunes, domingo = calcular_semana_actual()
    hoy = date.today()

    metadatos = []
    filas_features = []

    for i, nombre_dia in enumerate(DIAS_SEMANA_ES):
        fecha = lunes + timedelta(days=i)
        variables_tiempo = calcular_variables_temporales(fecha, contexto)
        for franja in ORDEN_FRANJAS:
            fila = construir_fila_demanda(franja, variables_tiempo, variables_clima, PROMOCION_DEFECTO, contexto)
            metadatos.append((i, fecha, franja))
            filas_features.append(fila)

    predicciones = pipeline_demanda.predict(pd.DataFrame(filas_features))

    celdas_por_dia = {}
    for (indice_dia, fecha, franja), valor in zip(metadatos, predicciones):
        pedidos = int(max(0, round(float(valor))))
        celdas_por_dia.setdefault(indice_dia, {})[franja] = {
            'pedidos_estimados': pedidos,
            'nivel_demanda': nivel_demanda_franja(pedidos),
        }

    mapa_calor = []
    for i, nombre_dia in enumerate(DIAS_SEMANA_ES):
        fecha = lunes + timedelta(days=i)
        mapa_calor.append({
            'dia': nombre_dia,
            'fecha': fecha,
            'es_hoy': fecha == hoy,
            'celdas': celdas_por_dia[i],
        })

    return mapa_calor, lunes, domingo


def _demanda_por_franja_hoy(mapa_calor):
    """Pedidos estimados de hoy por franja, en el formato que espera
    calcular_planificacion_personal_por_franja(). [] si hoy no está en el mapa."""
    hoy = date.today()
    fila_hoy = next((fila for fila in mapa_calor if fila['fecha'] == hoy), None)
    if not fila_hoy:
        return []

    return [
        {'franja_horaria': franja, 'pedidos_estimados': celda['pedidos_estimados']}
        for franja, celda in fila_hoy['celdas'].items()
    ]


def top_productos_historicos(contexto, top_n=5):
    """Top productos de todo el histórico (fallback cuando no hay PredictionResult)."""
    df = contexto.get('df')
    if df is None or not {'producto', 'cantidad_vendida'}.issubset(df.columns):
        return []

    categoria_por_producto = contexto.get('categoria_por_producto', {})
    resumen = df.groupby('producto')['cantidad_vendida'].sum().sort_values(ascending=False).head(top_n)
    return [
        {
            'producto': producto,
            'categoria': categoria_por_producto.get(producto, 'Sin categoría'),
            'cantidad_estimada': round(float(valor), 1),
        }
        for producto, valor in resumen.items()
    ]


def _resumen_recomendaciones(recomendaciones, max_items=4):
    resumen = []
    for categoria in CATEGORIAS_RECOMENDACION:
        items = (recomendaciones or {}).get(categoria) or []
        if items:
            resumen.append({'categoria': categoria, 'texto': items[0]})
        if len(resumen) >= max_items:
            break
    return resumen


def construir_datos_dashboard():
    """
    Orquestador único: reúne todo lo que necesita templates/dashboard/index.html.
    No entrena modelos, no carga datasets, no reemplaza a Predicciones.
    """
    dataset_valido = obtener_ultimo_dataset_valido()
    training_run = obtener_ultimo_training_run_entrenado()
    prediccion = PredictionResult.objects.filter(
        estado=PredictionResult.ESTADO_GENERADO
    ).order_by('-fecha_consulta').first()

    datos = {
        'dataset_valido': dataset_valido,
        'training_run': training_run,
        'prediccion': prediccion,
        'mapa_calor': None,
        'lunes_semana': None,
        'domingo_semana': None,
        'pedidos_estimados_hoy': None,
        'franja_critica_hoy': None,
        'planificacion_personal_franjas': [],
        'personal_operativo_pico': None,
        'productos_lideres_texto': None,
        'top_productos': [],
        'top_productos_es_historico': False,
        'recomendaciones_rapidas': [],
        'error_calculo': None,
    }

    if prediccion:
        datos['productos_lideres_texto'] = prediccion.resultado_detallado.get('productos_lideres_texto')
        datos['recomendaciones_rapidas'] = _resumen_recomendaciones(prediccion.recomendaciones)

    if not dataset_valido or not training_run:
        return datos

    try:
        contexto = construir_contexto_historico(dataset_valido)
        pipeline_demanda = cargar_pipeline_demanda(training_run)
        mapa_calor, lunes, domingo = _generar_mapa_calor(pipeline_demanda, contexto)

        demanda_hoy = _demanda_por_franja_hoy(mapa_calor)
        planificacion_personal_franjas = calcular_planificacion_personal_por_franja(demanda_hoy)
        personal_operativo_pico = next(
            (fila for fila in planificacion_personal_franjas if fila['es_franja_critica']), None
        )
        pedidos_hoy = sum(fila['pedidos_estimados'] for fila in demanda_hoy) if demanda_hoy else None
        franja_critica_hoy = personal_operativo_pico['franja_horaria'] if personal_operativo_pico else None

        datos.update({
            'mapa_calor': mapa_calor,
            'lunes_semana': lunes,
            'domingo_semana': domingo,
            'pedidos_estimados_hoy': pedidos_hoy,
            'franja_critica_hoy': franja_critica_hoy,
            'planificacion_personal_franjas': planificacion_personal_franjas,
            'personal_operativo_pico': personal_operativo_pico,
        })

        if prediccion:
            datos['top_productos'] = prediccion.productos_top[:5]
            datos['top_productos_es_historico'] = False
        else:
            datos['top_productos'] = top_productos_historicos(contexto)
            datos['top_productos_es_historico'] = True

    except Exception as exc:
        datos['error_calculo'] = str(exc)

    return datos
