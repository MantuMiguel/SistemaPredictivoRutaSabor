"""
Utilidades de validación del Dataset Histórico de Ruta del Sabor.

Este módulo solo lee y valida la ESTRUCTURA de un archivo .csv/.xlsx
(columnas, cantidad de filas, periodo, valores faltantes, vista previa).
No entrena modelos ni genera predicciones.
"""
import os

import pandas as pd

# Columnas obligatorias: si falta alguna, el dataset se rechaza.
COLUMNAS_OBLIGATORIAS = [
    'fecha',
    'franja_horaria',
    'producto',
    'categoria',
    'cantidad_vendida',
    'canal_venta',
    'promocion_activa',
    'tipo_promocion',
    'descuento_pct',
    'precio_unitario',
]

# Columnas opcionales: si falta alguna, solo se muestra una advertencia.
COLUMNAS_OPCIONALES = [
    'clima',
    'temperatura',
    'lluvia',
    'personal_disponible',
    'tiempo_preparacion_min',
    'stock_disponible',
    'porcentaje_delivery',
]

EXTENSIONES_PERMITIDAS = ('csv', 'xlsx')


def _extension(nombre_o_ruta):
    return os.path.splitext(nombre_o_ruta)[1].lstrip('.').lower()


def _leer_dataframe(file_path, extension):
    if extension == 'csv':
        # utf-8-sig: quita el BOM si el archivo lo trae (común al exportar desde Excel).
        return pd.read_csv(file_path, encoding='utf-8-sig')
    if extension == 'xlsx':
        # Primera hoja del libro (en el dataset oficial: "dataset_producto").
        return pd.read_excel(file_path, sheet_name=0, engine='openpyxl')
    raise ValueError(f'Extensión no soportada: .{extension}')


def _sanitizar_valor(valor):
    """Convierte un valor de pandas/numpy a algo simple y serializable en JSON."""
    if pd.isna(valor):
        return ''
    if hasattr(valor, 'item'):
        valor = valor.item()
    if hasattr(valor, 'strftime'):
        return valor.strftime('%Y-%m-%d')
    return valor


def _resultado_base():
    return {
        'estado': 'invalido',
        'cantidad_registros': 0,
        'cantidad_columnas': 0,
        'columnas_detectadas': [],
        'columnas_faltantes': [],
        'columnas_opcionales_faltantes': [],
        'errores': [],
        'advertencias': [],
        'periodo_inicio': None,
        'periodo_fin': None,
        'valores_faltantes': {'total_celdas_vacias': 0, 'porcentaje': 0.0, 'por_columna': {}},
        'vista_previa': [],
    }


def validate_dataset(file_path, nombre_original=None):
    """
    Valida un archivo de historial de ventas (.csv o .xlsx) contra el esquema
    oficial de Ruta del Sabor (columnas obligatorias/opcionales).

    Devuelve un diccionario con el resultado; no lanza excepciones por datos
    inválidos (solo por errores de programación). No entrena modelos, no
    hace predicciones: solo lee y resume la estructura del archivo.
    """
    nombre_original = nombre_original or os.path.basename(file_path)
    resultado = _resultado_base()

    extension = _extension(file_path)
    if extension not in EXTENSIONES_PERMITIDAS:
        resultado['errores'].append(
            f'Formato de archivo no soportado ("{extension}"). Usa un archivo .csv o .xlsx.'
        )
        return resultado

    try:
        df = _leer_dataframe(file_path, extension)
    except Exception as exc:  # noqa: BLE001 - queremos reportar cualquier fallo de lectura
        resultado['errores'].append(f'No se pudo leer "{nombre_original}": {exc}')
        return resultado

    columnas = list(df.columns)
    resultado['columnas_detectadas'] = columnas
    resultado['cantidad_registros'] = int(len(df))
    resultado['cantidad_columnas'] = int(len(columnas))

    faltantes_obligatorias = [c for c in COLUMNAS_OBLIGATORIAS if c not in columnas]
    faltantes_opcionales = [c for c in COLUMNAS_OPCIONALES if c not in columnas]
    resultado['columnas_faltantes'] = faltantes_obligatorias
    resultado['columnas_opcionales_faltantes'] = faltantes_opcionales

    # Valores faltantes en todo el archivo (no solo en las columnas del esquema).
    total_celdas = int(df.size) or 1
    total_vacias = int(df.isnull().sum().sum())
    por_columna = {col: int(cnt) for col, cnt in df.isnull().sum().items() if cnt > 0}
    resultado['valores_faltantes'] = {
        'total_celdas_vacias': total_vacias,
        'porcentaje': round((total_vacias / total_celdas) * 100, 2),
        'por_columna': por_columna,
    }

    # Periodo histórico, a partir de la columna fecha (si está presente).
    if 'fecha' in columnas:
        fechas_validas = pd.to_datetime(df['fecha'], errors='coerce').dropna()
        if not fechas_validas.empty:
            resultado['periodo_inicio'] = fechas_validas.min().date().isoformat()
            resultado['periodo_fin'] = fechas_validas.max().date().isoformat()

    # Vista previa: primeras 10 filas, en el mismo orden que columnas_detectadas.
    preview_df = df.head(10)[columnas]
    resultado['vista_previa'] = [
        [_sanitizar_valor(v) for v in fila]
        for fila in preview_df.itertuples(index=False, name=None)
    ]

    if faltantes_obligatorias:
        resultado['estado'] = 'invalido'
        resultado['errores'].append(
            'Faltan columnas obligatorias: ' + ', '.join(faltantes_obligatorias)
        )
        return resultado

    resultado['estado'] = 'valido'
    if faltantes_opcionales:
        resultado['advertencias'].append(
            'Faltan columnas opcionales: ' + ', '.join(faltantes_opcionales)
        )

    return resultado
