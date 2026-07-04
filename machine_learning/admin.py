from django.contrib import admin

from .models import TrainingRun


@admin.register(TrainingRun)
class TrainingRunAdmin(admin.ModelAdmin):
    list_display = (
        'fecha_entrenamiento',
        'estado',
        'dataset',
        'modelo_seleccionado_demanda',
        'rmse_demanda',
        'modelo_seleccionado_producto',
        'rmse_producto',
        'tiempo_entrenamiento_segundos',
    )
    readonly_fields = [field.name for field in TrainingRun._meta.fields]
