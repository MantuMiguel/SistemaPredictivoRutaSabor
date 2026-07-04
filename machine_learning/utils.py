"""
Lógica real de Machine Learning del módulo Modelo Predictivo.

Dos niveles de predicción, ambos de regresión (Aprendizaje Supervisado):

- NIVEL 1 (demanda total por franja): agrega el dataset por fecha + franja_horaria
  y predice `total_pedidos_franja`.
- NIVEL 2 (demanda por producto): usa el dataset a nivel de fila y predice
  `cantidad_vendida` de cada producto en su fecha/franja.

Para cada nivel se entrenan y comparan dos modelos (Regresión Lineal Múltiple y
Random Forest Regressor) y se selecciona automáticamente el mejor por
(menor RMSE, luego menor MAE, luego mayor R²).

Este módulo NO genera predicciones futuras (eso es responsabilidad del futuro
módulo Predicciones) — solo entrena, compara y guarda los mejores modelos.
"""
import math
import time
from pathlib import Path

import joblib
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from django.conf import settings

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NOMBRE_REGRESION_LINEAL = 'Regresión Lineal Múltiple'
NOMBRE_RANDOM_FOREST = 'Random Forest Regressor'

TARGET_DEMANDA = 'total_pedidos_franja'
TARGET_PRODUCTO = 'cantidad_vendida'

FEATURES_DEMANDA_CATEGORICAS = ['dia_semana', 'franja_horaria', 'clima', 'promocion_activa']
FEATURES_DEMANDA_NUMERICAS = [
    'mes', 'anio', 'es_fin_semana', 'es_feriado', 'hora_inicio', 'hora_fin',
    'temperatura', 'lluvia', 'porcentaje_delivery', 'personal_disponible',
]

FEATURES_PRODUCTO_CATEGORICAS = [
    'dia_semana', 'franja_horaria', 'producto', 'categoria', 'canal_venta',
    'promocion_activa', 'tipo_promocion', 'clima',
]
FEATURES_PRODUCTO_NUMERICAS = [
    'mes', 'anio', 'es_fin_semana', 'es_feriado', 'hora_inicio', 'hora_fin',
    'precio_unitario', 'descuento_pct', 'temperatura', 'lluvia',
    'personal_disponible', 'tiempo_preparacion_min', 'stock_disponible', 'porcentaje_delivery',
]

COLOR_LR = '#6B7280'
COLOR_RF = '#C81E2C'

CHART_FILENAMES = {
    'demanda_por_franja': 'demanda_por_franja.png',
    'top_productos': 'top_productos.png',
    'comparacion_mae': 'comparacion_mae.png',
    'comparacion_rmse': 'comparacion_rmse.png',
    'comparacion_r2': 'comparacion_r2.png',
    'real_vs_predicho_lineal': 'real_vs_predicho_lineal.png',
    'real_vs_predicho_random_forest': 'real_vs_predicho_random_forest.png',
    'importancia_variables_rf': 'importancia_variables_rf.png',
    'comparacion_modelos_producto': 'comparacion_modelos_producto.png',
}


# ------------------------------------------------------------------
# 1. Lectura del archivo (mismo criterio que datasets/utils.py)
# ------------------------------------------------------------------

def _leer_dataframe(file_path):
    extension = Path(file_path).suffix.lstrip('.').lower()
    if extension == 'csv':
        return pd.read_csv(file_path, encoding='utf-8-sig')
    if extension == 'xlsx':
        return pd.read_excel(file_path, sheet_name=0, engine='openpyxl')
    raise ValueError(f'Extensión no soportada: .{extension}')


# ------------------------------------------------------------------
# 2-4. Normalización de tipos y variables temporales
# ------------------------------------------------------------------

_DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


def preparar_datos(df):
    """Normaliza tipos y genera variables temporales si no existen."""
    df = df.copy()

    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

    if 'dia_semana' not in df.columns and 'fecha' in df.columns:
        df['dia_semana'] = df['fecha'].dt.dayofweek.map(
            lambda i: _DIAS_SEMANA[i] if pd.notna(i) else None
        )

    if 'mes' not in df.columns and 'fecha' in df.columns:
        df['mes'] = df['fecha'].dt.month

    if 'anio' not in df.columns and 'fecha' in df.columns:
        df['anio'] = df['fecha'].dt.year

    if 'es_fin_semana' not in df.columns and 'fecha' in df.columns:
        df['es_fin_semana'] = (df['fecha'].dt.dayofweek >= 5).astype(int)

    return df


# ------------------------------------------------------------------
# 5. Dataset agregado por franja (NIVEL 1)
# ------------------------------------------------------------------

def _es_promocion_activa(serie):
    valores = serie.astype(str).str.strip().str.lower()
    return 'Sí' if valores.isin(['sí', 'si', 'true', '1']).any() else 'No'


def construir_dataset_franja(df):
    """Agrupa por fecha + franja_horaria y suma cantidad_vendida -> total_pedidos_franja."""
    df = df.copy()

    if 'total_venta' not in df.columns and {'cantidad_vendida', 'precio_unitario'}.issubset(df.columns):
        df['total_venta'] = df['cantidad_vendida'] * df['precio_unitario']

    agregaciones = {'cantidad_vendida': 'sum'}
    if 'total_venta' in df.columns:
        agregaciones['total_venta'] = 'sum'

    columnas_contexto = [
        'dia_semana', 'mes', 'anio', 'es_fin_semana', 'es_feriado',
        'hora_inicio', 'hora_fin', 'clima', 'temperatura', 'lluvia',
        'porcentaje_delivery', 'personal_disponible',
    ]
    for col in columnas_contexto:
        if col in df.columns:
            agregaciones[col] = 'first'

    if 'promocion_activa' in df.columns:
        agregaciones['promocion_activa'] = _es_promocion_activa

    df_franja = df.groupby(['fecha', 'franja_horaria'], as_index=False).agg(agregaciones)
    df_franja = df_franja.rename(columns={
        'cantidad_vendida': 'total_pedidos_franja',
        'total_venta': 'total_venta_franja',
    })
    return df_franja


# ------------------------------------------------------------------
# 6-7. Preparación de X/Y + entrenamiento/comparación de modelos
# ------------------------------------------------------------------

def _limpiar_columna_categorica(serie):
    return serie.fillna('Desconocido').astype(str)


def _limpiar_columna_numerica(serie):
    serie = pd.to_numeric(serie, errors='coerce')
    return serie.fillna(serie.mean())


def _entrenar_nivel(df, categoricas_candidatas, numericas_candidatas, target_col):
    cat_cols = [c for c in categoricas_candidatas if c in df.columns]
    num_cols = [c for c in numericas_candidatas if c in df.columns]
    columnas_usadas = cat_cols + num_cols

    if not columnas_usadas:
        raise ValueError(f'No hay variables disponibles para entrenar el modelo de "{target_col}".')
    if target_col not in df.columns:
        raise ValueError(f'La columna objetivo "{target_col}" no está disponible.')

    data = df[columnas_usadas + [target_col]].copy()
    data = data.dropna(subset=[target_col])

    for col in cat_cols:
        data[col] = _limpiar_columna_categorica(data[col])
    for col in num_cols:
        data[col] = _limpiar_columna_numerica(data[col])

    X = data[columnas_usadas]
    y = data[target_col]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    resultados = {}
    predicciones = {}
    pipelines = {}

    modelos = [
        (NOMBRE_REGRESION_LINEAL, LinearRegression()),
        (NOMBRE_RANDOM_FOREST, RandomForestRegressor(n_estimators=200, random_state=42, max_depth=18)),
    ]

    for nombre, modelo in modelos:
        preprocesador = ColumnTransformer(transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols),
            ('num', StandardScaler(), num_cols),
        ])
        pipeline = Pipeline(steps=[('preprocesador', preprocesador), ('modelo', modelo)])
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(math.sqrt(mean_squared_error(y_test, y_pred)))
        r2 = float(r2_score(y_test, y_pred))

        resultados[nombre] = {'mae': round(mae, 4), 'rmse': round(rmse, 4), 'r2': round(r2, 4)}
        predicciones[nombre] = {'y_test': y_test.reset_index(drop=True), 'y_pred': y_pred}
        pipelines[nombre] = pipeline

    mejor_nombre = min(
        resultados,
        key=lambda nombre: (resultados[nombre]['rmse'], resultados[nombre]['mae'], -resultados[nombre]['r2']),
    )

    return {
        'columnas_usadas': columnas_usadas,
        'resultados': resultados,
        'predicciones': predicciones,
        'pipelines': pipelines,
        'mejor_nombre': mejor_nombre,
    }


def _importancia_variables(pipeline, top_n=15):
    preprocesador = pipeline.named_steps['preprocesador']
    modelo = pipeline.named_steps['modelo']
    if not hasattr(modelo, 'feature_importances_'):
        return []
    nombres = preprocesador.get_feature_names_out()
    importancias = modelo.feature_importances_
    pares = sorted(zip(nombres, importancias), key=lambda par: par[1], reverse=True)[:top_n]
    return [
        {'variable': str(nombre).split('__', 1)[-1], 'importancia': round(float(valor), 4)}
        for nombre, valor in pares
    ]


# ------------------------------------------------------------------
# Gráficos (Matplotlib, backend "Agg", guardados como PNG)
# ------------------------------------------------------------------

def _guardar_figura(fig, ruta_absoluta):
    ruta_absoluta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_absoluta, dpi=120, bbox_inches='tight')
    plt.close(fig)


def _grafico_demanda_por_franja(df_franja, ruta):
    promedio = df_franja.groupby('franja_horaria')[TARGET_DEMANDA].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(promedio.index.astype(str), promedio.values, color=COLOR_RF)
    ax.set_title('Demanda promedio por franja horaria')
    ax.set_xlabel('Franja horaria')
    ax.set_ylabel('Pedidos promedio')
    ax.grid(axis='y', alpha=0.3)
    _guardar_figura(fig, ruta)


def _grafico_top_productos(df, ruta, top_n=10):
    top = df.groupby('producto')[TARGET_PRODUCTO].sum().sort_values(ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(top.index[::-1], top.values[::-1], color=COLOR_RF)
    ax.set_title(f'Top {len(top)} productos más vendidos (histórico)')
    ax.set_xlabel('Unidades vendidas')
    ax.grid(axis='x', alpha=0.3)
    _guardar_figura(fig, ruta)


def _grafico_comparacion_metrica(resultados, metrica, titulo, ylabel, ruta):
    nombres = list(resultados.keys())
    valores = [resultados[n][metrica] for n in nombres]
    colores = [COLOR_LR if n == NOMBRE_REGRESION_LINEAL else COLOR_RF for n in nombres]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(nombres, valores, color=colores)
    ax.set_title(titulo)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis='x', labelrotation=10)
    ax.grid(axis='y', alpha=0.3)
    _guardar_figura(fig, ruta)


def _grafico_real_vs_predicho(y_test, y_pred, titulo, ruta, color):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(y_test, y_pred, alpha=0.5, color=color, edgecolor='none')
    minimo = float(min(y_test.min(), y_pred.min()))
    maximo = float(max(y_test.max(), y_pred.max()))
    ax.plot([minimo, maximo], [minimo, maximo], linestyle='--', color='#1F2430', linewidth=1)
    ax.set_title(titulo)
    ax.set_xlabel('Valor real')
    ax.set_ylabel('Valor predicho')
    ax.grid(alpha=0.3)
    _guardar_figura(fig, ruta)


def _grafico_importancia_variables(importancias, ruta, top_n=12):
    top = importancias[:top_n]
    nombres = [item['variable'] for item in top][::-1]
    valores = [item['importancia'] for item in top][::-1]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(nombres, valores, color=COLOR_RF)
    ax.set_title('Importancia de variables (Random Forest - demanda total)')
    ax.set_xlabel('Importancia')
    ax.grid(axis='x', alpha=0.3)
    _guardar_figura(fig, ruta)


def _grafico_comparacion_modelos_producto(resultados, ruta):
    metricas = [('mae', 'MAE'), ('rmse', 'RMSE'), ('r2', 'R²')]
    nombres = list(resultados.keys())
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, (clave, etiqueta) in zip(axes, metricas):
        valores = [resultados[n][clave] for n in nombres]
        colores = [COLOR_LR if n == NOMBRE_REGRESION_LINEAL else COLOR_RF for n in nombres]
        ax.bar(nombres, valores, color=colores)
        ax.set_title(etiqueta)
        ax.tick_params(axis='x', labelrotation=15)
        ax.grid(axis='y', alpha=0.3)
    fig.suptitle('Comparación de modelos — Demanda por producto')
    _guardar_figura(fig, ruta)


# ------------------------------------------------------------------
# Orquestación completa del entrenamiento
# ------------------------------------------------------------------

def ejecutar_entrenamiento(dataset_upload):
    """
    Entrena ambos niveles (demanda total y por producto) con Regresión Lineal
    y Random Forest, guarda los mejores modelos con joblib y genera los 9
    gráficos con Matplotlib. No hace predicciones futuras.
    """
    inicio = time.time()

    try:
        df_crudo = _leer_dataframe(dataset_upload.archivo.path)
    except Exception as exc:
        return {'estado': 'error', 'errores': [f'No se pudo leer el archivo del dataset: {exc}']}

    try:
        df = preparar_datos(df_crudo)
        df_franja = construir_dataset_franja(df)

        demanda = _entrenar_nivel(df_franja, FEATURES_DEMANDA_CATEGORICAS, FEATURES_DEMANDA_NUMERICAS, TARGET_DEMANDA)
        producto = _entrenar_nivel(df, FEATURES_PRODUCTO_CATEGORICAS, FEATURES_PRODUCTO_NUMERICAS, TARGET_PRODUCTO)

        media_root = Path(settings.MEDIA_ROOT)
        modelos_dir = media_root / 'models'
        charts_dir = media_root / 'charts'
        modelos_dir.mkdir(parents=True, exist_ok=True)
        charts_dir.mkdir(parents=True, exist_ok=True)

        mejor_pipeline_demanda = demanda['pipelines'][demanda['mejor_nombre']]
        mejor_pipeline_producto = producto['pipelines'][producto['mejor_nombre']]

        ruta_modelo_demanda = modelos_dir / 'modelo_demanda.joblib'
        ruta_modelo_producto = modelos_dir / 'modelo_producto.joblib'
        joblib.dump(mejor_pipeline_demanda, ruta_modelo_demanda)
        joblib.dump(mejor_pipeline_producto, ruta_modelo_producto)

        pipeline_rf_demanda = demanda['pipelines'].get(NOMBRE_RANDOM_FOREST)
        importancia = _importancia_variables(pipeline_rf_demanda) if pipeline_rf_demanda is not None else []

        version = int(time.time())

        def _url_grafico(clave):
            return f"{settings.MEDIA_URL}charts/{CHART_FILENAMES[clave]}?v={version}"

        graficos = {}

        _grafico_demanda_por_franja(df_franja, charts_dir / CHART_FILENAMES['demanda_por_franja'])
        graficos['demanda_por_franja'] = _url_grafico('demanda_por_franja')

        _grafico_top_productos(df, charts_dir / CHART_FILENAMES['top_productos'])
        graficos['top_productos'] = _url_grafico('top_productos')

        _grafico_comparacion_metrica(
            demanda['resultados'], 'mae', 'Comparación de MAE — Demanda total', 'MAE',
            charts_dir / CHART_FILENAMES['comparacion_mae'],
        )
        graficos['comparacion_mae'] = _url_grafico('comparacion_mae')

        _grafico_comparacion_metrica(
            demanda['resultados'], 'rmse', 'Comparación de RMSE — Demanda total', 'RMSE',
            charts_dir / CHART_FILENAMES['comparacion_rmse'],
        )
        graficos['comparacion_rmse'] = _url_grafico('comparacion_rmse')

        _grafico_comparacion_metrica(
            demanda['resultados'], 'r2', 'Comparación de R² — Demanda total', 'R²',
            charts_dir / CHART_FILENAMES['comparacion_r2'],
        )
        graficos['comparacion_r2'] = _url_grafico('comparacion_r2')

        pred_lr = demanda['predicciones'].get(NOMBRE_REGRESION_LINEAL)
        if pred_lr is not None:
            _grafico_real_vs_predicho(
                pred_lr['y_test'], pred_lr['y_pred'], 'Real vs. predicho — Regresión Lineal',
                charts_dir / CHART_FILENAMES['real_vs_predicho_lineal'], COLOR_LR,
            )
            graficos['real_vs_predicho_lineal'] = _url_grafico('real_vs_predicho_lineal')

        pred_rf = demanda['predicciones'].get(NOMBRE_RANDOM_FOREST)
        if pred_rf is not None:
            _grafico_real_vs_predicho(
                pred_rf['y_test'], pred_rf['y_pred'], 'Real vs. predicho — Random Forest',
                charts_dir / CHART_FILENAMES['real_vs_predicho_random_forest'], COLOR_RF,
            )
            graficos['real_vs_predicho_random_forest'] = _url_grafico('real_vs_predicho_random_forest')

        if importancia:
            _grafico_importancia_variables(importancia, charts_dir / CHART_FILENAMES['importancia_variables_rf'])
            graficos['importancia_variables_rf'] = _url_grafico('importancia_variables_rf')

        _grafico_comparacion_modelos_producto(producto['resultados'], charts_dir / CHART_FILENAMES['comparacion_modelos_producto'])
        graficos['comparacion_modelos_producto'] = _url_grafico('comparacion_modelos_producto')

        tiempo = round(time.time() - inicio, 2)
        media_root_str = str(media_root)

        return {
            'estado': 'entrenado',
            'modelo_seleccionado_demanda': demanda['mejor_nombre'],
            'modelo_seleccionado_producto': producto['mejor_nombre'],
            'mae_demanda': demanda['resultados'][demanda['mejor_nombre']]['mae'],
            'rmse_demanda': demanda['resultados'][demanda['mejor_nombre']]['rmse'],
            'r2_demanda': demanda['resultados'][demanda['mejor_nombre']]['r2'],
            'mae_producto': producto['resultados'][producto['mejor_nombre']]['mae'],
            'rmse_producto': producto['resultados'][producto['mejor_nombre']]['rmse'],
            'r2_producto': producto['resultados'][producto['mejor_nombre']]['r2'],
            'metricas_detalladas': {'demanda': demanda['resultados'], 'producto': producto['resultados']},
            'variables_usadas_demanda': demanda['columnas_usadas'],
            'variables_usadas_producto': producto['columnas_usadas'],
            'importancia_variables': importancia,
            'ruta_modelo_demanda': str(ruta_modelo_demanda).replace(media_root_str, '').lstrip('\\/').replace('\\', '/'),
            'ruta_modelo_producto': str(ruta_modelo_producto).replace(media_root_str, '').lstrip('\\/').replace('\\', '/'),
            'graficos': graficos,
            'tiempo_entrenamiento_segundos': tiempo,
            'errores': [],
        }
    except Exception as exc:
        return {'estado': 'error', 'errores': [f'Error durante el entrenamiento: {exc}']}
