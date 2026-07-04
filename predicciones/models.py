from django.db import models

from machine_learning.models import TrainingRun


class PredictionResult(models.Model):
    """Una consulta de demanda futura resuelta con el último TrainingRun entrenado."""

    ESTADO_GENERADO = 'generado'
    ESTADO_ERROR = 'error'
    ESTADO_CHOICES = [
        (ESTADO_GENERADO, 'Generado'),
        (ESTADO_ERROR, 'Error'),
    ]

    training_run = models.ForeignKey(
        TrainingRun, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='predicciones',
    )
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    fecha_prediccion = models.DateField(null=True, blank=True)
    franja_horaria = models.CharField(max_length=20, blank=True)

    pedidos_estimados = models.FloatField(null=True, blank=True)
    franja_critica = models.CharField(max_length=20, blank=True)
    nivel_demanda = models.CharField(max_length=30, blank=True)

    productos_top = models.JSONField(default=list, blank=True)
    recomendaciones = models.JSONField(default=dict, blank=True)
    parametros_entrada = models.JSONField(default=dict, blank=True)
    resultado_detallado = models.JSONField(default=dict, blank=True)

    modelo_demanda_usado = models.CharField(max_length=100, blank=True)
    modelo_producto_usado = models.CharField(max_length=100, blank=True)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_GENERADO)
    errores = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-fecha_consulta']

    def __str__(self):
        return f'Predicción {self.fecha_prediccion} - {self.franja_horaria} ({self.estado})'
