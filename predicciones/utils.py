"""
Lógica real del módulo Predicciones.

Este módulo NO entrena modelos ni carga datasets: solo carga los modelos ya
entrenados (.joblib) del último TrainingRun con estado "entrenado" y los usa
para estimar la demanda futura de una fecha/franja consultada por el usuario.

Reutiliza (por import, sin modificar) la preparación de variables temporales
y las listas de features de machine_learning/utils.py, para que la fila que
se arma aquí sea consistente con lo que el modelo aprendió a predecir.
"""
import os
from pathlib import Path

import joblib
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from django.conf import settings

from datasets.models import DatasetUpload
from machine_learning.models import TrainingRun
from machine_learning.utils import (
    FEATURES_DEMANDA_CATEGORICAS,
    FEATURES_DEMANDA_NUMERICAS,
    FEATURES_PRODUCTO_CATEGORICAS,
    FEATURES_PRODUCTO_NUMERICAS,
    NOMBRE_RANDOM_FOREST,
    NOMBRE_REGRESION_LINEAL,
    TARGET_DEMANDA,
    TARGET_PRODUCTO,
    preparar_datos,
)

# ------------------------------------------------------------------
# Franjas horarias oficiales (únicas válidas en todo el sistema)
# ------------------------------------------------------------------

FRANJAS_OFICIALES = {
    'Desayuno': {'hora_inicio': 7, 'hora_fin': 11},
    'Almuerzo': {'hora_inicio': 12, 'hora_fin': 16},
    'Cena': {'hora_inicio': 18, 'hora_fin': 22},
}
ORDEN_FRANJAS = ['Desayuno', 'Almuerzo', 'Cena']

CLIMA_PARAMS = {
    'Soleado': {'lluvia': 0, 'temp_min': 23, 'temp_max': 31},
    'Nublado': {'lluvia': 0, 'temp_min': 18, 'temp_max': 24},
    'Lluvioso': {'lluvia': 1, 'temp_min': 16, 'temp_max': 22},
}

RANGOS_DEMANDA_FRANJA = [
    (0, 79, 'Baja demanda'),
    (80, 119, 'Demanda moderada'),
    (120, 179, 'Alta demanda'),
    (180, None, 'Demanda crítica'),
]
RANGOS_DEMANDA_DIARIA = [
    (0, 199, 'Baja demanda'),
    (200, 349, 'Demanda moderada'),
    (350, 499, 'Alta demanda'),
    (500, None, 'Demanda crítica'),
]

CHART_FILENAMES = {
    'prediccion_por_franja': 'prediccion_por_franja.png',
    'prediccion_top_productos': 'prediccion_top_productos.png',
}

COLOR_PRIMARIO = '#C81E2C'

# Grupos de productos usados por las reglas de Cocina (sección "Top operativo").
# "Operativo" excluye Bebidas: una gaseosa de alta rotación no debe dominar la
# card de productos líderes ni disparar recomendaciones de cocina.
NOMBRES_HAMBURGUESAS = {'hamburguesa clásica', 'hamburguesa bbq', 'cheeseburger'}
NOMBRES_SALCHIPAPAS = {'salchipapa clásica', 'salchipapa especial'}
NOMBRES_PIZZAS = {'pizza personal', 'pizza familiar'}

# MEJORA FUTURA (no implementada): mapa de calor semanal de demanda por día y
# franja horaria. Solo tiene sentido cuando el formulario permita consultar un
# rango de "próximos 7 días"; hoy la consulta es de una sola fecha, así que un
# mapa de calor no aportaría información adicional a la vista.


# ------------------------------------------------------------------
# Disponibilidad del sistema (reglas funcionales 1-3)
# ------------------------------------------------------------------

def obtener_ultimo_training_run_entrenado():
    return TrainingRun.objects.filter(estado=TrainingRun.ESTADO_ENTRENADO).order_by('-fecha_entrenamiento').first()


def obtener_ultimo_dataset_valido():
    return DatasetUpload.objects.filter(estado_validacion=DatasetUpload.ESTADO_VALIDO).order_by('-fecha_carga').first()


def sistema_listo_para_predecir():
    return obtener_ultimo_training_run_entrenado() is not None and obtener_ultimo_dataset_valido() is not None


# ------------------------------------------------------------------
# Carga de modelos entrenados (solo lectura, nunca se reentrena aquí)
# ------------------------------------------------------------------

def _leer_dataframe(file_path):
    extension = Path(file_path).suffix.lstrip('.').lower()
    if extension == 'csv':
        return pd.read_csv(file_path, encoding='utf-8-sig')
    if extension == 'xlsx':
        return pd.read_excel(file_path, sheet_name=0, engine='openpyxl')
    raise ValueError(f'Extensión no soportada: .{extension}')


def cargar_pipelines(training_run):
    media_root = Path(settings.MEDIA_ROOT)
    ruta_demanda = media_root / training_run.ruta_modelo_demanda
    ruta_producto = media_root / training_run.ruta_modelo_producto

    if not ruta_demanda.exists() or not ruta_producto.exists():
        raise FileNotFoundError(
            'No se encontraron los archivos del modelo entrenado (.joblib) en media/models/. '
            'Vuelve a entrenar el modelo desde Modelo Predictivo.'
        )

    pipeline_demanda = joblib.load(ruta_demanda)
    pipeline_producto = joblib.load(ruta_producto)
    return pipeline_demanda, pipeline_producto


# ------------------------------------------------------------------
# Contexto histórico: promedios y catálogos desde el último dataset válido
# ------------------------------------------------------------------

def _moda_o_primero(serie):
    serie = serie.dropna()
    if serie.empty:
        return None
    moda = serie.mode()
    return moda.iat[0] if not moda.empty else serie.iat[0]


def construir_contexto_historico(dataset_valido):
    """Lee el dataset validado y calcula los promedios/catálogos que el usuario no ingresa."""
    df_crudo = _leer_dataframe(dataset_valido.archivo.path)
    df = preparar_datos(df_crudo)

    contexto = {'df': df}

    productos = sorted(df['producto'].dropna().unique().tolist()) if 'producto' in df.columns else []
    contexto['productos'] = productos

    contexto['categoria_por_producto'] = (
        df.groupby('producto')['categoria'].agg(_moda_o_primero).to_dict()
        if {'producto', 'categoria'}.issubset(df.columns) else {}
    )
    contexto['precio_por_producto'] = (
        df.groupby('producto')['precio_unitario'].mean().to_dict()
        if {'producto', 'precio_unitario'}.issubset(df.columns) else {}
    )
    contexto['tiempo_preparacion_por_producto'] = (
        df.groupby('producto')['tiempo_preparacion_min'].mean().to_dict()
        if {'producto', 'tiempo_preparacion_min'}.issubset(df.columns) else {}
    )
    contexto['stock_por_producto'] = (
        df.groupby('producto')['stock_disponible'].mean().to_dict()
        if {'producto', 'stock_disponible'}.issubset(df.columns) else {}
    )
    contexto['personal_por_franja'] = (
        df.groupby('franja_horaria')['personal_disponible'].mean().to_dict()
        if {'franja_horaria', 'personal_disponible'}.issubset(df.columns) else {}
    )
    contexto['canal_por_franja'] = (
        df.groupby('franja_horaria')['canal_venta'].agg(_moda_o_primero).to_dict()
        if {'franja_horaria', 'canal_venta'}.issubset(df.columns) else {}
    )
    contexto['delivery_por_franja_clima'] = (
        df.groupby(['franja_horaria', 'clima'])['porcentaje_delivery'].mean().to_dict()
        if {'franja_horaria', 'clima', 'porcentaje_delivery'}.issubset(df.columns) else {}
    )
    contexto['delivery_por_franja'] = (
        df.groupby('franja_horaria')['porcentaje_delivery'].mean().to_dict()
        if {'franja_horaria', 'porcentaje_delivery'}.issubset(df.columns) else {}
    )

    # Promedios/valores generales (fallback si no hay dato específico)
    contexto['fallback'] = {
        'precio_unitario': df['precio_unitario'].mean() if 'precio_unitario' in df.columns else 0,
        'tiempo_preparacion_min': df['tiempo_preparacion_min'].mean() if 'tiempo_preparacion_min' in df.columns else 0,
        'stock_disponible': df['stock_disponible'].mean() if 'stock_disponible' in df.columns else 0,
        'personal_disponible': df['personal_disponible'].mean() if 'personal_disponible' in df.columns else 0,
        'canal_venta': _moda_o_primero(df['canal_venta']) if 'canal_venta' in df.columns else 'Presencial',
        'porcentaje_delivery': df['porcentaje_delivery'].mean() if 'porcentaje_delivery' in df.columns else 0,
        'categoria': 'Sin categoría',
    }

    # Días feriados históricos: se busca por (mes, día) si esa fecha ya fue feriado antes.
    contexto['feriados_mes_dia'] = {}
    if {'fecha', 'es_feriado'}.issubset(df.columns):
        tmp = df.dropna(subset=['fecha']).copy()
        tmp['mes_dia'] = tmp['fecha'].dt.strftime('%m-%d')
        contexto['feriados_mes_dia'] = tmp.groupby('mes_dia')['es_feriado'].max().to_dict()

    return contexto


# ------------------------------------------------------------------
# Variables temporales y de clima a partir de la consulta del usuario
# ------------------------------------------------------------------

_DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


def calcular_variables_temporales(fecha_prediccion, contexto):
    dia_semana = _DIAS_SEMANA[fecha_prediccion.weekday()]
    mes = fecha_prediccion.month
    anio = fecha_prediccion.year
    es_fin_semana = int(fecha_prediccion.weekday() >= 5)

    mes_dia = fecha_prediccion.strftime('%m-%d')
    es_feriado = int(contexto.get('feriados_mes_dia', {}).get(mes_dia, 0) or 0)

    return {
        'dia_semana': dia_semana,
        'mes': mes,
        'anio': anio,
        'es_fin_semana': es_fin_semana,
        'es_feriado': es_feriado,
    }


def calcular_variables_clima(clima):
    parametros = CLIMA_PARAMS.get(clima, CLIMA_PARAMS['Soleado'])
    temperatura = (parametros['temp_min'] + parametros['temp_max']) / 2
    return {'clima': clima, 'temperatura': temperatura, 'lluvia': parametros['lluvia']}


# ------------------------------------------------------------------
# Construcción de filas de entrada para cada modelo
# ------------------------------------------------------------------

def _valor_con_fallback(diccionario, clave, fallback):
    valor = diccionario.get(clave)
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return fallback
    return valor


def construir_fila_demanda(franja, variables_tiempo, variables_clima, promocion_activa, contexto):
    horario = FRANJAS_OFICIALES[franja]
    fallback = contexto['fallback']

    personal = _valor_con_fallback(contexto['personal_por_franja'], franja, fallback['personal_disponible'])
    delivery = contexto['delivery_por_franja_clima'].get((franja, variables_clima['clima']))
    if delivery is None:
        delivery = _valor_con_fallback(contexto['delivery_por_franja'], franja, fallback['porcentaje_delivery'])

    fila = {
        'dia_semana': variables_tiempo['dia_semana'],
        'franja_horaria': franja,
        'clima': variables_clima['clima'],
        'promocion_activa': promocion_activa,
        'mes': variables_tiempo['mes'],
        'anio': variables_tiempo['anio'],
        'es_fin_semana': variables_tiempo['es_fin_semana'],
        'es_feriado': variables_tiempo['es_feriado'],
        'hora_inicio': horario['hora_inicio'],
        'hora_fin': horario['hora_fin'],
        'temperatura': variables_clima['temperatura'],
        'lluvia': variables_clima['lluvia'],
        'porcentaje_delivery': delivery,
        'personal_disponible': personal,
    }
    return {clave: fila[clave] for clave in FEATURES_DEMANDA_CATEGORICAS + FEATURES_DEMANDA_NUMERICAS}


def construir_filas_producto(franja, variables_tiempo, variables_clima, promocion_activa, tipo_promocion, descuento_pct, contexto):
    horario = FRANJAS_OFICIALES[franja]
    fallback = contexto['fallback']
    canal_venta = _valor_con_fallback(contexto['canal_por_franja'], franja, fallback['canal_venta'])
    personal = _valor_con_fallback(contexto['personal_por_franja'], franja, fallback['personal_disponible'])
    delivery = contexto['delivery_por_franja_clima'].get((franja, variables_clima['clima']))
    if delivery is None:
        delivery = _valor_con_fallback(contexto['delivery_por_franja'], franja, fallback['porcentaje_delivery'])

    filas = []
    for producto in contexto['productos']:
        categoria = _valor_con_fallback(contexto['categoria_por_producto'], producto, fallback['categoria'])
        precio_unitario = _valor_con_fallback(contexto['precio_por_producto'], producto, fallback['precio_unitario'])
        tiempo_preparacion = _valor_con_fallback(
            contexto['tiempo_preparacion_por_producto'], producto, fallback['tiempo_preparacion_min']
        )
        stock_disponible = _valor_con_fallback(contexto['stock_por_producto'], producto, fallback['stock_disponible'])

        fila = {
            'dia_semana': variables_tiempo['dia_semana'],
            'franja_horaria': franja,
            'producto': producto,
            'categoria': categoria,
            'canal_venta': canal_venta,
            'promocion_activa': promocion_activa,
            'tipo_promocion': tipo_promocion,
            'clima': variables_clima['clima'],
            'mes': variables_tiempo['mes'],
            'anio': variables_tiempo['anio'],
            'es_fin_semana': variables_tiempo['es_fin_semana'],
            'es_feriado': variables_tiempo['es_feriado'],
            'hora_inicio': horario['hora_inicio'],
            'hora_fin': horario['hora_fin'],
            'precio_unitario': precio_unitario,
            'descuento_pct': descuento_pct,
            'temperatura': variables_clima['temperatura'],
            'lluvia': variables_clima['lluvia'],
            'personal_disponible': personal,
            'tiempo_preparacion_min': tiempo_preparacion,
            'stock_disponible': stock_disponible,
            'porcentaje_delivery': delivery,
        }
        filas.append({clave: fila[clave] for clave in FEATURES_PRODUCTO_CATEGORICAS + FEATURES_PRODUCTO_NUMERICAS})

    return pd.DataFrame(filas), contexto['productos']


# ------------------------------------------------------------------
# Niveles de demanda
# ------------------------------------------------------------------

def _nivel_por_rango(valor, rangos):
    for minimo, maximo, etiqueta in rangos:
        if maximo is None:
            if valor >= minimo:
                return etiqueta
        elif minimo <= valor <= maximo:
            return etiqueta
    return rangos[-1][2]


def nivel_demanda_franja(valor):
    return _nivel_por_rango(valor, RANGOS_DEMANDA_FRANJA)


def nivel_demanda_diaria(valor):
    return _nivel_por_rango(valor, RANGOS_DEMANDA_DIARIA)


# ------------------------------------------------------------------
# Centro de recomendaciones inteligentes
# ------------------------------------------------------------------

def _suma_por_coincidencia(productos_top_completos, palabra_clave, campo='categoria'):
    palabra_clave = palabra_clave.lower()
    return sum(
        item['cantidad_estimada'] for item in productos_top_completos
        if palabra_clave in str(item.get(campo, '')).lower()
    )


def es_bebida(categoria):
    return 'bebida' in str(categoria or '').lower()


def calcular_productos_operativos(productos_completos):
    """Productos completos sin Bebidas, ya ordenados de mayor a menor demanda."""
    return [item for item in productos_completos if not es_bebida(item.get('categoria'))]


def _dedupe(lista):
    return list(dict.fromkeys(lista))


def generar_recomendaciones(
    resultado_por_franja, productos_completos, productos_operativos_top3,
    promocion_activa, clima, es_todo_el_dia, delivery_estimado_max,
):
    # Claves ASCII en minúscula (sin tilde) para que el acceso por punto en los
    # templates de Django sea siempre seguro; las etiquetas visibles con tilde
    # se escriben directamente en el template.
    recomendaciones = {'abastecimiento': [], 'cocina': [], 'personal': [], 'operacion': []}

    # ---- Abastecimiento: umbrales por producto/categoría (sobre todos los productos, con o sin bebidas) ----
    unidades_pollo_broaster = sum(
        item['cantidad_estimada'] for item in productos_completos
        if str(item.get('producto', '')).strip().lower() == 'pollo broaster'
    )
    unidades_hamburguesas = _suma_por_coincidencia(productos_completos, 'hamburguesa')
    unidades_salchipapas = _suma_por_coincidencia(productos_completos, 'salchipapa') or _suma_por_coincidencia(productos_completos, 'papas')
    unidades_bebidas = _suma_por_coincidencia(productos_completos, 'bebida') or (
        _suma_por_coincidencia(productos_completos, 'gaseosa') + _suma_por_coincidencia(productos_completos, 'jugo')
    )

    pedidos_por_franja = {item['franja_horaria']: item['pedidos_estimados'] for item in resultado_por_franja}
    niveles_por_franja = {item['franja_horaria']: item['nivel_demanda'] for item in resultado_por_franja}

    if unidades_pollo_broaster > 45:
        recomendaciones['abastecimiento'].append('Comprar más pollo y papas: se espera alta demanda de Pollo Broaster.')
    if unidades_hamburguesas > 40:
        recomendaciones['abastecimiento'].append('Revisar stock de pan, carne, queso y salsas para hamburguesas.')
    if unidades_salchipapas > 50:
        recomendaciones['abastecimiento'].append('Aumentar stock de papas y salchichas.')

    niveles_altos = {'Alta demanda', 'Demanda crítica'}
    if promocion_activa == 'Sí' and any(nivel in niveles_altos for nivel in niveles_por_franja.values()):
        recomendaciones['abastecimiento'].append('Revisar stock antes del turno: hay promoción activa y demanda alta.')

    # ---- Cocina: basada en el Top 3 operativo (sin Bebidas), no en umbrales genéricos ----
    nombres_top3 = {str(item['producto']).strip().lower() for item in productos_operativos_top3}

    if 'pollo broaster' in nombres_top3:
        recomendaciones['cocina'].append('Preparar anticipadamente pollo broaster y papas para la franja crítica.')
    if 'alitas bbq' in nombres_top3:
        recomendaciones['cocina'].append('Preparar porciones de alitas y salsas antes del inicio del turno.')
    if nombres_top3 & NOMBRES_HAMBURGUESAS:
        recomendaciones['cocina'].append('Adelantar mise en place de pan, carne, queso, vegetales y salsas para hamburguesas.')
    if nombres_top3 & NOMBRES_SALCHIPAPAS:
        recomendaciones['cocina'].append('Preparar papas y salchichas con anticipación para reducir tiempos de espera.')
    if nombres_top3 & NOMBRES_PIZZAS:
        recomendaciones['cocina'].append('Preparar masa, queso y toppings antes de la franja con mayor demanda.')
    if 'sándwich de pollo' in nombres_top3:
        recomendaciones['cocina'].append('Preparar pollo, pan y vegetales para sándwiches antes del turno.')
    if not recomendaciones['cocina']:
        recomendaciones['cocina'].append('Mantener preparación estándar y monitorear la demanda durante la franja.')

    # ---- Operación ----
    if unidades_bebidas > 60:
        recomendaciones['operacion'].append('Refrigerar bebidas con anticipación.')
    if clima == 'Lluvioso':
        recomendaciones['operacion'].append('Reforzar delivery y preparar envases adicionales.')
    if delivery_estimado_max is not None and delivery_estimado_max > 60:
        recomendaciones['operacion'].append('Reforzar despacho y coordinación con delivery.')

    # ---- Personal ----
    if es_todo_el_dia:
        total_dia = sum(pedidos_por_franja.values())
        nivel_dia = nivel_demanda_diaria(total_dia)
        if nivel_dia in niveles_altos:
            recomendaciones['personal'].append(f'Reforzar el personal operativo: se espera {nivel_dia.lower()} en el día.')
    if 'Almuerzo' in pedidos_por_franja and pedidos_por_franja['Almuerzo'] > 180:
        recomendaciones['personal'].append('Asignar apoyo adicional en cocina durante el almuerzo.')
    if 'Cena' in pedidos_por_franja and pedidos_por_franja['Cena'] > 160:
        recomendaciones['personal'].append('Asignar apoyo en cocina y despacho durante la cena.')

    return {categoria: _dedupe(mensajes) for categoria, mensajes in recomendaciones.items()}


# ------------------------------------------------------------------
# Gráficos (Matplotlib, Agg)
# ------------------------------------------------------------------

def _guardar_figura(fig, ruta_absoluta):
    ruta_absoluta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_absoluta, dpi=120, bbox_inches='tight')
    plt.close(fig)


def _grafico_prediccion_por_franja(resultado_por_franja, ruta):
    nombres = [item['franja_horaria'] for item in resultado_por_franja]
    valores = [item['pedidos_estimados'] for item in resultado_por_franja]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(nombres, valores, color=COLOR_PRIMARIO)
    ax.set_title('Predicción de pedidos por franja horaria')
    ax.set_xlabel('Franja horaria')
    ax.set_ylabel('Pedidos estimados')
    ax.grid(axis='y', alpha=0.3)
    _guardar_figura(fig, ruta)


def _grafico_prediccion_top_productos(productos_top, ruta):
    nombres = [item['producto'] for item in productos_top][::-1]
    valores = [item['cantidad_estimada'] for item in productos_top][::-1]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(nombres, valores, color=COLOR_PRIMARIO)
    ax.set_title('Top productos esperados')
    ax.set_xlabel('Unidades estimadas')
    ax.grid(axis='x', alpha=0.3)
    _guardar_figura(fig, ruta)


# ------------------------------------------------------------------
# Orquestación completa de la consulta de predicción
# ------------------------------------------------------------------

def generar_prediccion(fecha_prediccion, franja_seleccionada, clima, promocion_activa, tipo_promocion, descuento_pct):
    """
    Genera la predicción de demanda para la fecha/franja consultada, usando
    únicamente los modelos ya entrenados (no entrena nada aquí).
    """
    training_run = obtener_ultimo_training_run_entrenado()
    dataset_valido = obtener_ultimo_dataset_valido()

    if training_run is None or dataset_valido is None:
        return {
            'estado': 'error',
            'errores': ['Primero debes entrenar un modelo desde el módulo Modelo Predictivo.'],
        }

    try:
        pipeline_demanda, pipeline_producto = cargar_pipelines(training_run)
    except Exception as exc:
        return {'estado': 'error', 'errores': [str(exc)]}

    try:
        contexto = construir_contexto_historico(dataset_valido)
        variables_tiempo = calcular_variables_temporales(fecha_prediccion, contexto)
        variables_clima = calcular_variables_clima(clima)

        es_todo_el_dia = franja_seleccionada == 'Todo el día'
        franjas_a_predecir = ORDEN_FRANJAS if es_todo_el_dia else [franja_seleccionada]

        resultado_por_franja = []
        productos_por_franja = {}
        delivery_por_franja_usado = {}

        for franja in franjas_a_predecir:
            fila_demanda = construir_fila_demanda(franja, variables_tiempo, variables_clima, promocion_activa, contexto)
            delivery_por_franja_usado[franja] = fila_demanda.get('porcentaje_delivery')

            pedidos_estimados = float(pipeline_demanda.predict(pd.DataFrame([fila_demanda]))[0])
            # Pedidos estimados siempre como número entero (no decimales) en cards,
            # resultados por franja y gráficos.
            pedidos_estimados = int(max(0, round(pedidos_estimados)))

            resultado_por_franja.append({
                'franja_horaria': franja,
                'pedidos_estimados': pedidos_estimados,
                'nivel_demanda': nivel_demanda_franja(pedidos_estimados),
            })

            df_filas_producto, productos = construir_filas_producto(
                franja, variables_tiempo, variables_clima, promocion_activa, tipo_promocion, descuento_pct, contexto
            )
            predicciones_producto = pipeline_producto.predict(df_filas_producto)
            productos_por_franja[franja] = [
                {'producto': producto, 'cantidad_estimada': max(0.0, round(float(valor), 1))}
                for producto, valor in zip(productos, predicciones_producto)
            ]

        # Acumula unidades estimadas por producto a través de las franjas consultadas
        acumulado = {}
        categoria_por_producto = contexto['categoria_por_producto']
        for franja, items in productos_por_franja.items():
            for item in items:
                acumulado[item['producto']] = acumulado.get(item['producto'], 0.0) + item['cantidad_estimada']

        productos_completos = [
            {
                'producto': producto,
                'categoria': categoria_por_producto.get(producto, 'Sin categoría'),
                'cantidad_estimada': round(cantidad, 1),
            }
            for producto, cantidad in acumulado.items()
        ]
        productos_completos.sort(key=lambda item: item['cantidad_estimada'], reverse=True)
        productos_top = productos_completos[:5]

        # Top operativo: igual ranking pero sin Bebidas, para no dejar que una
        # gaseosa de alta rotación domine la card de "Productos líderes" ni las
        # recomendaciones de Cocina.
        productos_operativos = calcular_productos_operativos(productos_completos)
        productos_operativos_top3 = productos_operativos[:3]
        nombres_lideres = [item['producto'] for item in productos_operativos_top3[:2]]
        if not nombres_lideres:
            # Si no hay ningún producto fuera de Bebidas, se usa el top general como respaldo.
            nombres_lideres = [item['producto'] for item in productos_top[:2]]
        productos_lideres_texto = ', '.join(nombres_lideres) if nombres_lideres else '—'

        if es_todo_el_dia:
            pedidos_estimados_totales = int(sum(item['pedidos_estimados'] for item in resultado_por_franja))
            franja_critica = max(resultado_por_franja, key=lambda item: item['pedidos_estimados'])['franja_horaria']
            nivel_operativo = nivel_demanda_diaria(pedidos_estimados_totales)
        else:
            pedidos_estimados_totales = resultado_por_franja[0]['pedidos_estimados']
            franja_critica = resultado_por_franja[0]['franja_horaria']
            nivel_operativo = resultado_por_franja[0]['nivel_demanda']

        delivery_valores = [v for v in delivery_por_franja_usado.values() if v is not None]
        delivery_estimado_max = max(delivery_valores) if delivery_valores else None

        recomendaciones = generar_recomendaciones(
            resultado_por_franja, productos_completos, productos_operativos_top3,
            promocion_activa, clima, es_todo_el_dia, delivery_estimado_max,
        )

        media_root = Path(settings.MEDIA_ROOT)
        charts_dir = media_root / 'charts'
        charts_dir.mkdir(parents=True, exist_ok=True)
        version = int(pd.Timestamp.now().timestamp())

        _grafico_prediccion_por_franja(resultado_por_franja, charts_dir / CHART_FILENAMES['prediccion_por_franja'])
        _grafico_prediccion_top_productos(productos_top or productos_completos[:1], charts_dir / CHART_FILENAMES['prediccion_top_productos'])

        graficos = {
            'prediccion_por_franja': f"{settings.MEDIA_URL}charts/{CHART_FILENAMES['prediccion_por_franja']}?v={version}",
            'prediccion_top_productos': f"{settings.MEDIA_URL}charts/{CHART_FILENAMES['prediccion_top_productos']}?v={version}",
        }

        return {
            'estado': 'generado',
            'pedidos_estimados': pedidos_estimados_totales,
            'franja_critica': franja_critica,
            'nivel_demanda': nivel_operativo,
            'resultado_por_franja': resultado_por_franja,
            'productos_top': productos_top,
            'productos_operativos_top3': productos_operativos_top3,
            'productos_lideres_texto': productos_lideres_texto,
            'recomendaciones': recomendaciones,
            'graficos': graficos,
            'modelo_demanda_usado': training_run.modelo_seleccionado_demanda,
            'modelo_producto_usado': training_run.modelo_seleccionado_producto,
            'training_run': training_run,
            'errores': [],
        }
    except Exception as exc:
        return {'estado': 'error', 'errores': [f'Error al generar la predicción: {exc}']}
