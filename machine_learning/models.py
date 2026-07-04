from django.db import models

from datasets.models import DatasetUpload


class TrainingRun(models.Model):
    """Un entrenamiento real de los modelos de demanda (total y por producto)."""

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_ENTRENADO = 'entrenado'
    ESTADO_ERROR = 'error'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_ENTRENADO, 'Entrenado'),
        (ESTADO_ERROR, 'Error'),
    ]

    dataset = models.ForeignKey(
        DatasetUpload, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='entrenamientos',
    )
    fecha_entrenamiento = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)

    # Nivel 1: demanda total por franja
    modelo_seleccionado_demanda = models.CharField(max_length=100, blank=True)
    mae_demanda = models.FloatField(null=True, blank=True)
    rmse_demanda = models.FloatField(null=True, blank=True)
    r2_demanda = models.FloatField(null=True, blank=True)

    # Nivel 2: demanda por producto
    modelo_seleccionado_producto = models.CharField(max_length=100, blank=True)
    mae_producto = models.FloatField(null=True, blank=True)
    rmse_producto = models.FloatField(null=True, blank=True)
    r2_producto = models.FloatField(null=True, blank=True)

    metricas_detalladas = models.JSONField(default=dict, blank=True)
    variables_usadas_demanda = models.JSONField(default=list, blank=True)
    variables_usadas_producto = models.JSONField(default=list, blank=True)
    importancia_variables = models.JSONField(default=list, blank=True)

    ruta_modelo_demanda = models.CharField(max_length=255, blank=True)
    ruta_modelo_producto = models.CharField(max_length=255, blank=True)

    graficos = models.JSONField(default=dict, blank=True)
    errores = models.JSONField(default=list, blank=True)

    tiempo_entrenamiento_segundos = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_entrenamiento']

    def __str__(self):
        return f'Entrenamiento {self.fecha_entrenamiento:%Y-%m-%d %H:%M} ({self.estado})'
