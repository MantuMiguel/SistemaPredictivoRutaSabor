from django.contrib import admin

from .models import PredictionResult


@admin.register(PredictionResult)
class PredictionResultAdmin(admin.ModelAdmin):
    list_display = (
        'fecha_consulta',
        'fecha_prediccion',
        'franja_horaria',
        'estado',
        'pedidos_estimados',
        'nivel_demanda',
        'franja_critica',
    )
    readonly_fields = [field.name for field in PredictionResult._meta.fields]
