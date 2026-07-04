from django.db import models


class DatasetUpload(models.Model):
    """Un archivo de historial de ventas subido y validado desde el módulo Dataset."""

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_VALIDO = 'valido'
    ESTADO_INVALIDO = 'invalido'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_VALIDO, 'Válido'),
        (ESTADO_INVALIDO, 'Inválido'),
    ]

    archivo = models.FileField(upload_to='datasets/')
    nombre_original = models.CharField(max_length=255)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    cantidad_registros = models.IntegerField(null=True, blank=True)
    cantidad_columnas = models.IntegerField(null=True, blank=True)
    estado_validacion = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE
    )

    columnas_detectadas = models.JSONField(default=list, blank=True)
    columnas_faltantes = models.JSONField(default=list, blank=True)
    columnas_opcionales_faltantes = models.JSONField(default=list, blank=True)
    errores_validacion = models.JSONField(default=list, blank=True)
    advertencias = models.JSONField(default=list, blank=True)

    periodo_inicio = models.DateField(null=True, blank=True)
    periodo_fin = models.DateField(null=True, blank=True)

    valores_faltantes = models.JSONField(default=dict, blank=True)
    vista_previa = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-fecha_carga']

    def __str__(self):
        return f'{self.nombre_original} ({self.estado_validacion})'
