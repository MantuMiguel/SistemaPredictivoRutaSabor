from django.contrib import admin

from .models import DatasetUpload


@admin.register(DatasetUpload)
class DatasetUploadAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_original',
        'estado_validacion',
        'cantidad_registros',
        'cantidad_columnas',
        'periodo_inicio',
        'periodo_fin',
        'fecha_carga',
    )
    readonly_fields = [field.name for field in DatasetUpload._meta.fields]
