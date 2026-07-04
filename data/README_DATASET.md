# Dataset Sintético - Ruta del Sabor

## Descripción

Este dataset representa el historial de ventas sintético de una empresa pequeña dedicada a la comercialización de comida rápida llamada **Ruta del Sabor**.

El objetivo del dataset es servir como base para un sistema inteligente de apoyo a la toma de decisiones, orientado a predecir la demanda futura de pedidos y productos para optimizar la planificación de cocina, insumos, personal y operación.

## Periodo histórico

- Fecha inicial: 2024-01-01
- Fecha final: 2025-06-30
- Duración aproximada: 18 meses

## Archivos generados

1. `ruta_del_sabor_dataset.csv`
   - Dataset principal a nivel de producto, fecha y franja horaria.

2. `ruta_del_sabor_dataset.xlsx`
   - Versión Excel del dataset principal.
   - Incluye dos hojas:
     - `dataset_producto`
     - `demanda_franja`

3. `ruta_del_sabor_demanda_franja.csv`
   - Dataset agregado por fecha y franja horaria.

## Cantidad de registros

- Registros dataset principal: 7329
- Registros dataset agregado por franja: 1641

## Franjas horarias

- Desayuno: 07:00 - 11:00
- Almuerzo: 12:00 - 16:00
- Cena: 18:00 - 22:00

## Productos incluidos

- Hamburguesa Clásica
- Hamburguesa BBQ
- Cheeseburger
- Pollo Broaster
- Alitas BBQ
- Salchipapa Clásica
- Salchipapa Especial
- Pizza Personal
- Pizza Familiar
- Sándwich de Pollo
- Gaseosa
- Jugo Natural

## Columnas obligatorias

Estas columnas son requeridas por el sistema para validar el dataset:

- fecha
- franja_horaria
- producto
- categoria
- cantidad_vendida
- canal_venta
- promocion_activa
- tipo_promocion
- descuento_pct
- precio_unitario

## Columnas opcionales

Estas columnas enriquecen el análisis, pero no deben bloquear la carga si no existen en un dataset real:

- clima
- temperatura
- lluvia
- personal_disponible
- tiempo_preparacion_min
- stock_disponible
- porcentaje_delivery

## Variables independientes

El modelo utilizará variables como:

- fecha
- dia_semana
- mes
- es_fin_semana
- es_feriado
- franja_horaria
- producto
- categoria
- canal_venta
- promocion_activa
- tipo_promocion
- descuento_pct
- clima
- temperatura
- lluvia
- personal_disponible
- tiempo_preparacion_min
- stock_disponible
- porcentaje_delivery

## Variables objetivo

### Nivel 1: Demanda total por franja

Variable objetivo:

- total_pedidos_franja

Esta variable se encuentra en el archivo agregado `ruta_del_sabor_demanda_franja.csv`.

Sirve para predecir cuántos pedidos se esperan en una fecha y franja horaria específica.

### Nivel 2: Demanda por producto

Variable objetivo:

- cantidad_vendida

Esta variable se encuentra en el dataset principal.

Sirve para estimar qué productos tendrán mayor demanda en una determinada fecha y franja horaria.

## Uso dentro del sistema

El flujo esperado es:

1. El administrador carga el archivo CSV o Excel desde el módulo Dataset.
2. El sistema valida las columnas obligatorias.
3. El sistema muestra resumen, columnas detectadas y vista previa.
4. El módulo Modelo Predictivo procesa la información con Pandas.
5. Se entrenan modelos de regresión:
   - Regresión Lineal Múltiple
   - Random Forest Regressor
6. Se comparan los modelos mediante:
   - MAE
   - RMSE
   - R²
7. El mejor modelo se utiliza para generar predicciones.
8. Las predicciones se convierten en recomendaciones operativas.

## Observación

Los datos son sintéticos, pero fueron generados con patrones realistas:

- Mayor demanda en almuerzo y cena.
- Mayor demanda los viernes, sábados y domingos.
- Incremento por promociones.
- Incremento del delivery durante cena y lluvia.
- Productos con distinta rotación según la franja.
- Variación por clima, feriados y fines de semana.
