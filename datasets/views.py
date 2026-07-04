from django.contrib import messages
from django.shortcuts import redirect, render

from .models import DatasetUpload
from .utils import COLUMNAS_OBLIGATORIAS, COLUMNAS_OPCIONALES, EXTENSIONES_PERMITIDAS, validate_dataset


def _procesar_carga(request):
    """Guarda el archivo subido, lo valida y persiste el resultado en DatasetUpload."""
    archivo = request.FILES.get('archivo')

    if not archivo:
        messages.error(request, 'Selecciona un archivo .csv o .xlsx antes de continuar.')
        return

    extension = archivo.name.rsplit('.', 1)[-1].lower() if '.' in archivo.name else ''
    if extension not in EXTENSIONES_PERMITIDAS:
        messages.error(request, 'Formato no soportado. Usa un archivo .csv o .xlsx.')
        return

    dataset_upload = DatasetUpload.objects.create(archivo=archivo, nombre_original=archivo.name)

    resultado = validate_dataset(dataset_upload.archivo.path, nombre_original=archivo.name)

    dataset_upload.cantidad_registros = resultado['cantidad_registros']
    dataset_upload.cantidad_columnas = resultado['cantidad_columnas']
    dataset_upload.estado_validacion = resultado['estado']
    dataset_upload.columnas_detectadas = resultado['columnas_detectadas']
    dataset_upload.columnas_faltantes = resultado['columnas_faltantes']
    dataset_upload.columnas_opcionales_faltantes = resultado['columnas_opcionales_faltantes']
    dataset_upload.errores_validacion = resultado['errores']
    dataset_upload.advertencias = resultado['advertencias']
    dataset_upload.periodo_inicio = resultado['periodo_inicio']
    dataset_upload.periodo_fin = resultado['periodo_fin']
    dataset_upload.valores_faltantes = resultado['valores_faltantes']
    dataset_upload.vista_previa = resultado['vista_previa']
    dataset_upload.save()

    if resultado['estado'] == 'valido':
        if resultado['advertencias']:
            messages.warning(request, 'Dataset válido, con advertencias. Revisa el resumen.')
        else:
            messages.success(request, 'Dataset validado correctamente.')
    else:
        messages.error(request, 'El dataset fue rechazado: faltan columnas obligatorias.')


def index(request):
    """Vista del Dataset Histórico: carga, valida y muestra el historial de ventas."""
    if request.method == 'POST':
        _procesar_carga(request)
        return redirect('datasets:index')

    dataset = DatasetUpload.objects.order_by('-fecha_carga').first()

    columnas_esquema_ok = None
    if dataset is not None:
        columnas_esquema_ok = (
            len(COLUMNAS_OBLIGATORIAS)
            + len(COLUMNAS_OPCIONALES)
            - len(dataset.columnas_faltantes)
            - len(dataset.columnas_opcionales_faltantes)
        )

    return render(request, 'datasets/index.html', {
        'modulo_activo': 'datasets',
        'dataset': dataset,
        'columnas_obligatorias': COLUMNAS_OBLIGATORIAS,
        'columnas_opcionales': COLUMNAS_OPCIONALES,
        'columnas_esquema_total': len(COLUMNAS_OBLIGATORIAS) + len(COLUMNAS_OPCIONALES),
        'columnas_esquema_ok': columnas_esquema_ok,
    })
