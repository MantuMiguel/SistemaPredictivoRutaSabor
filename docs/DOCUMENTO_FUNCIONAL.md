# Documento Funcional Oficial — Ruta del Sabor

**Sistema Inteligente de Apoyo a la Toma de Decisiones para Restaurantes de Comida Rápida**

| | |
|---|---|
| **Versión** | 1.0 |
| **Fecha** | 2026-07-04 |
| **Autor** | Analista Funcional Senior / Arquitectura de Software |
| **Estado** | Especificación funcional oficial — base para las siguientes fases de desarrollo |
| **Alcance de este documento** | Solo documentación y validación. No introduce cambios visuales, de estilos ni funcionalidades nuevas. |

---

## Índice

1. [Descripción del negocio](#1-descripción-del-negocio)
2. [Objetivo general](#2-objetivo-general)
3. [Objetivos específicos](#3-objetivos-específicos)
4. [Alcance del sistema](#4-alcance-del-sistema)
5. [Lo que el sistema NO es](#5-lo-que-el-sistema-no-es)
6. [Arquitectura funcional](#6-arquitectura-funcional)
7. [Flujo general del sistema](#7-flujo-general-del-sistema)
8. [Descripción detallada de cada módulo](#8-descripción-detallada-de-cada-módulo)
9. [Casos de uso](#9-casos-de-uso)
10. [Flujo del usuario administrador](#10-flujo-del-usuario-administrador)
11. [Reglas de negocio](#11-reglas-de-negocio)
12. [Diseño del dataset objetivo](#12-diseño-del-dataset-objetivo)
13. [Validación del dataset actual contra el dataset objetivo](#13-validación-del-dataset-actual-contra-el-dataset-objetivo)
14. [Arquitectura Machine Learning](#14-arquitectura-machine-learning)
15. [Modelos utilizados](#15-modelos-utilizados)
16. [Métricas de evaluación](#16-métricas-de-evaluación)
17. [Flujo de entrenamiento](#17-flujo-de-entrenamiento)
18. [Flujo de predicción](#18-flujo-de-predicción)
19. [Centro de recomendaciones inteligentes](#19-centro-de-recomendaciones-inteligentes)
20. [Recomendaciones por categoría](#20-recomendaciones-por-categoría)
21. [Ajustes necesarios en Dataset, Modelo Predictivo y Predicciones](#21-ajustes-necesarios-en-dataset-modelo-predictivo-y-predicciones)
22. [Conclusiones](#22-conclusiones)
23. [Anexo — Validación específica solicitada](#23-anexo--validación-específica-solicitada)

---

## 1. Descripción del negocio

**Ruta del Sabor** es una **empresa pequeña** dedicada a la comercialización de comida rápida — no una cadena grande ni multi-local. Opera con un **catálogo limitado pero variado** (entre 10 y 15 productos activos: hamburguesas, pollo broaster, alitas, salchipapas, pizzas personales/familiares, sándwiches y bebidas), atiende por canal local y por delivery, y enfrenta los problemas operativos típicos del rubro:

- Picos de demanda difíciles de anticipar (franjas de almuerzo y cena).
- Quiebres de stock en insumos críticos (pan, carne, papas, envases).
- Decisiones de compra, producción y personal basadas en la experiencia del encargado de turno, no en datos.
- Coordinación reactiva (no proactiva) entre cocina y delivery.

El proyecto **Ruta del Sabor** nace como respuesta a este problema: un sistema de software que usa el historial de ventas para **anticipar** la demanda futura y traducir esa predicción en recomendaciones operativas concretas.

## 2. Objetivo general

> Desarrollar un sistema inteligente que, mediante técnicas de Aprendizaje Supervisado basadas en modelos de regresión, analice el historial de ventas para predecir la demanda futura de pedidos y de los productos más solicitados, generando recomendaciones que optimicen la planificación de insumos, la preparación de cocina y la gestión operativa del restaurante.

## 3. Objetivos específicos

1. Centralizar el historial de ventas en un módulo de **Dataset** con validación de estructura y calidad de datos.
2. Entrenar y comparar modelos de regresión (**Regresión Lineal Múltiple** y **Random Forest Regressor**) sobre ese histórico.
3. Seleccionar automáticamente el modelo con mejor desempeño según métricas objetivas (MAE, RMSE, R²).
4. Exponer un módulo de **Predicciones** que use el mejor modelo entrenado para estimar la demanda futura por fecha, rango y turno.
5. Traducir las predicciones en un **Centro de Recomendaciones Inteligentes**, categorizado por Abastecimiento, Cocina, Personal y Operación.
6. Ofrecer un **Dashboard** ejecutivo que resuma, de un vistazo, el estado del negocio y del modelo.
7. Mantener una interfaz simple, sin roles, sin login y sin módulos ajenos al propósito predictivo (no POS, no facturación, no inventario).

## 4. Alcance del sistema

El sistema cubre:

- Carga y validación de historial de ventas (Dataset).
- Entrenamiento, comparación y selección de modelos predictivos (Modelo Predictivo).
- Consulta de demanda futura por fecha/rango/turno (Predicciones).
- Panel ejecutivo de indicadores (Dashboard).
- Página informativa de bienvenida (Inicio).
- Generación de recomendaciones operativas basadas en reglas de negocio aplicadas sobre la salida del modelo.

Fuera de alcance (explícitamente):

- Registro transaccional de pedidos en tiempo real.
- Facturación o emisión de comprobantes.
- Control de inventario/kardex.
- Gestión de usuarios, roles, permisos o autenticación.
- Módulo de Reportes (queda deshabilitado, marcado como "Próximamente").

## 5. Lo que el sistema NO es

| No es | Por qué se aclara |
|---|---|
| **POS** (Punto de Venta) | No registra transacciones de venta reales ni cobra pedidos. |
| **Sistema de Facturación** | No emite boletas/facturas ni maneja impuestos. |
| **Sistema de Inventario/ERP** | No controla stock en tiempo real ni movimientos de almacén; solo *sugiere* niveles de abastecimiento a partir de la predicción. |
| **Sistema con usuarios/roles** | Es de un solo perfil de uso (administrador), sin login ni permisos diferenciados. |

Lo que **sí** es: un sistema de apoyo a la decisión (*Decision Support System*) enfocado en **predicción de demanda** y **recomendación operativa**, construido sobre Aprendizaje Supervisado de tipo regresión.

## 6. Arquitectura funcional

El proyecto está construido en **Django 5.2** con arquitectura de apps independientes, una por módulo funcional, y una capa de presentación común (`base.html`) que todas heredan:

```
config/                  # Proyecto Django (settings, urls raíz)
├── dashboard/           # Inicio + Panel de Control (Dashboard)
├── datasets/            # Módulo Dataset
├── machine_learning/     # Módulo Modelo Predictivo (incluye services/ para lógica ML futura)
├── predicciones/         # Módulo Predicciones
├── templates/            # base.html + templates por módulo
├── static/               # css/styles.css, js/*.js
└── media/                # Reservado para archivos subidos (Dataset) — actualmente vacío
```

Características actuales de la arquitectura (estado real verificado en el código):

- **Sin modelos de base de datos propios**: los 4 archivos `models.py` de las apps están vacíos (solo el boilerplate de Django). No existe persistencia de dataset, entrenamientos ni predicciones — todo lo mostrado en las plantillas es **contenido de demostración estático**.
- **Sin dependencias de Machine Learning instaladas**: no hay `pandas`, `numpy` ni `scikit-learn` en el entorno virtual. El módulo `machine_learning/services/` existe como carpeta pero solo contiene un `__init__.py` vacío.
- **Sin autenticación**: `django.contrib.auth` está instalado por defecto de Django pero no se usa en ninguna vista; no hay login, no hay decoradores de permisos.
- **Presentación**: Tailwind CSS vía CDN + Material Symbols, sin Bootstrap. Este documento no modifica nada de esa capa.

Esta arquitectura es coherente con el objetivo de la fase actual: **validar y ordenar la lógica funcional antes de construir la capa de datos y de ML real.**

## 7. Flujo general del sistema

```
 ┌───────────┐     ┌───────────────────┐     ┌────────────────────┐     ┌───────────────┐
 │  Dataset   │ ──▶ │ Modelo Predictivo  │ ──▶ │   Predicciones      │ ──▶ │   Dashboard    │
 │ (carga y   │     │ (entrenar, comparar│     │ (consultar demanda  │     │ (resumen       │
 │ validación)│     │  y elegir el mejor)│     │  futura + turnos +  │     │  ejecutivo)    │
 └───────────┘     └───────────────────┘     │  recomendaciones)   │     └───────────────┘
                                              └────────────────────┘
```

Este es el **flujo de datos** (de dónde viene la información y hacia dónde va). El **flujo de navegación** del usuario no es necesariamente lineal: el administrador puede entrar directamente a Predicciones o al Dashboard sin repetir el flujo completo cada vez, siempre que ya exista un dataset cargado y un modelo entrenado.

## 8. Descripción detallada de cada módulo

### 8.1 Inicio

**Propósito:** landing informativa. Explica qué hace el sistema, sus beneficios, el flujo general y las ventajas de usar Machine Learning para este problema de negocio.

**Debe contener:**
- Qué hace el sistema (predicción de demanda + recomendaciones).
- Beneficios de negocio (menos quiebres de stock, menos desperdicio, mejores tiempos de entrega).
- Flujo general (Dataset → Modelo → Predicciones, en forma resumida/visual).
- Ventajas de usar Machine Learning frente a la planificación manual.
- Cómo apoya la toma de decisiones del administrador.

**No debe contener:** tablas de datos, entrenamiento de modelos, ni predicciones activas — es puramente informativa.

**Estado actual:** existe la landing (`dashboard/inicio.html`) con hero de bienvenida y 3 tarjetas de "Capacidades Estratégicas" (Anticipación de Pedidos, Optimización de Insumos, Mejora en Delivery). Cubre parcialmente el propósito: **falta** una mención explícita a las ventajas del Machine Learning frente a la planificación manual y un mini-flujo visual (Dataset → Modelo → Predicciones). No tiene tablas ni lógica de entrenamiento/predicción — correcto.

### 8.2 Dashboard

**Propósito:** resumen ejecutivo. Es la foto rápida del estado del negocio y del modelo, no un módulo de trabajo.

**Debe mostrar:**
- Pedidos esperados (hoy/próximo periodo).
- Franja crítica.
- Producto líder.
- Último entrenamiento del modelo.
- Modelo seleccionado.
- Precisión o métrica principal (ej. R²).
- Alertas rápidas.
- Recomendaciones rápidas.
- Indicadores generales.

**No debe:** cargar dataset, entrenar modelos directamente, ni duplicar la función de Predicciones (no debe tener su propio formulario de consulta por fecha/turno).

**Estado actual:** existen 4 KPI cards (Pedidos estimados del día, Producto con mayor demanda, Franja horaria crítica, Promoción con mayor impacto), gráfico de demanda por hora, top de productos, alertas operativas y recomendaciones para cocina, y una sección "Problemas que resuelve". **Brecha identificada:** no muestra ninguno de los 3 indicadores relacionados al modelo (**último entrenamiento**, **modelo seleccionado**, **precisión/R²**) — ver sección 21.

### 8.3 Dataset

**Propósito:** administración exclusiva del historial de datos que alimenta al Modelo Predictivo.

**Debe permitir:** subir archivo Excel/CSV y validar su estructura.

**Debe mostrar después de subir:** cantidad de registros, cantidad de columnas, periodo histórico, valores faltantes, vista previa, estado de validación, columnas detectadas, errores si faltan columnas obligatorias.

**No debe:** entrenar modelos ni hacer predicciones.

**Estado actual:** existe carga de archivo `.csv`/`.xlsx` con validación **únicamente de extensión** (en JavaScript, sin backend), 4 cards de resumen (total de registros, rango de fechas, productos registrados, última actualización) y una tabla de vista previa con 14 columnas de ejemplo. **Brechas identificadas:** no muestra cantidad de columnas, valores faltantes, columnas detectadas explícitamente, ni errores por columnas obligatorias faltantes — ver detalle en sección 21 y en el Anexo.

### 8.4 Modelo Predictivo

**Propósito:** único módulo responsable del ciclo de Machine Learning.

**Debe permitir:** entrenar modelos, compararlos, seleccionar automáticamente el mejor, y marcarlo como disponible para Predicciones.

**Modelos oficiales:** Regresión Lineal Múltiple y Random Forest Regressor.

**Debe mostrar:** MAE, RMSE, R², tiempo de entrenamiento, variables utilizadas, importancia de variables, mejor modelo seleccionado, fecha del último entrenamiento, estado del modelo.

**No debe:** cargar dataset ni ofrecer la consulta de predicciones futuras como función principal.

**Estado actual:** este es el módulo **más alineado** con la especificación. Ya muestra estado del modelo, R², variable más influyente, último entrenamiento, botón "Entrenar modelo" (simulado con un modal JS), comparación Regresión Lineal vs. Random Forest con MAE/RMSE/R², ranking de importancia de variables y un flujo visual Dataset → Procesamiento → Entrenamiento → Predicción. **Brecha identificada:** no muestra explícitamente el **tiempo de entrenamiento** como dato independiente, ni un indicador textual de "modelo guardado/disponible para predicciones" distinto del estado general.

### 8.5 Predicciones

**Propósito:** consulta de demanda futura usando el mejor modelo ya entrenado. No entrena ni carga datos.

**Debe permitir:** consultar una fecha futura o un rango, y responder con cantidad esperada de pedidos, franja horaria de mayor demanda, productos más demandados, nivel esperado de operación y recomendaciones inteligentes.

**Debe mostrar predicción por turnos** (Mañana / Tarde / Noche), cada uno con horario, pedidos estimados, hora pico, producto más demandado y recomendación operativa.

**Puede mostrar:** gráfico de demanda por hora, gráfico de productos más demandados, centro de recomendaciones inteligentes.

**Las promociones no deben ser parte principal del formulario** — deben ir como simulación avanzada opcional.

**Estado actual:** ya es el módulo más cercano a esta definición tras el ajuste funcional de la fase anterior: formulario principal reducido a Fecha a consultar / Rango de predicción / Franja horaria; "Simular promoción" y "Tipo de promoción" viven en un `<details>` colapsable de "Opciones avanzadas de simulación"; existen 4 KPI cards, resultado destacado, 3 cards de "Predicción por turnos" (Mañana/Tarde/Noche) con los 5 datos requeridos, gráfico de demanda por hora y lista de productos con mayor demanda. **Brecha identificada:** las recomendaciones actuales son una **lista plana** de 3 ítems, no un Centro de Recomendaciones Inteligentes categorizado (Abastecimiento / Cocina / Personal / Operación) como pide esta fase — ver secciones 19, 20 y 21.

## 9. Casos de uso

| # | Caso de uso | Actor | Módulo | Descripción |
|---|---|---|---|---|
| CU-01 | Cargar historial de ventas | Administrador | Dataset | Sube un archivo CSV/Excel con el histórico de ventas para que el sistema lo valide y lo deje disponible para entrenamiento. |
| CU-02 | Validar estructura del dataset | Sistema | Dataset | Verifica columnas obligatorias, tipos de datos, valores faltantes y periodo cubierto; informa errores si el archivo no cumple el esquema. |
| CU-03 | Entrenar modelos predictivos | Administrador | Modelo Predictivo | Ejecuta el entrenamiento de Regresión Lineal y Random Forest sobre el dataset validado. |
| CU-04 | Comparar modelos y elegir el mejor | Sistema | Modelo Predictivo | Calcula MAE/RMSE/R² de cada modelo y marca automáticamente el de mejor desempeño como disponible para Predicciones. |
| CU-05 | Consultar demanda futura por fecha | Administrador | Predicciones | Selecciona una fecha o rango y obtiene pedidos estimados, franja crítica, productos top y recomendaciones. |
| CU-06 | Consultar demanda por turno | Administrador | Predicciones | Revisa el detalle de Mañana/Tarde/Noche para planificar personal y producción por bloque horario. |
| CU-07 | Simular impacto de una promoción | Administrador | Predicciones (avanzado) | Activa la simulación opcional de promoción para ver cómo cambiaría la demanda estimada (funcionalidad secundaria, no bloquea el flujo principal). |
| CU-08 | Revisar recomendaciones inteligentes | Administrador | Predicciones | Consulta el centro de recomendaciones categorizado (Abastecimiento, Cocina, Personal, Operación) derivado de la predicción vigente. |
| CU-09 | Revisar estado general del negocio | Administrador | Dashboard | Entra al panel ejecutivo para ver, de un vistazo, indicadores clave sin tener que operar los módulos de detalle. |
| CU-10 | Conocer el sistema | Visitante/Administrador nuevo | Inicio | Lee la landing para entender el propósito, beneficios y flujo del sistema antes de operarlo. |

## 10. Flujo del usuario administrador

```
1. Entra a "Inicio"
   └─ Lee de qué trata el sistema y cómo lo ayuda.

2. Va a "Dataset"
   └─ Sube el historial de ventas (CSV/Excel).
   └─ El sistema valida estructura, columnas y calidad de datos.
   └─ Revisa el resumen (registros, periodo, columnas, valores faltantes).

3. Va a "Modelo Predictivo"
   └─ Entrena Regresión Lineal y Random Forest sobre el dataset validado.
   └─ Compara MAE / RMSE / R² de ambos modelos.
   └─ El sistema selecciona automáticamente el mejor modelo.

4. Va a "Predicciones"
   └─ Elige una fecha o rango a futuro.
   └─ (Opcional) Simula una promoción en "Opciones avanzadas".
   └─ Consulta pedidos estimados, franja crítica, productos top, turnos.
   └─ Revisa el Centro de Recomendaciones Inteligentes.

5. Va a "Dashboard" (en cualquier momento)
   └─ Revisa el resumen ejecutivo: negocio + estado del modelo, sin repetir el flujo completo.
```

El administrador **no necesita repetir los pasos 2 y 3 cada vez** — solo cuando quiera actualizar el dataset o volver a entrenar el modelo con datos más recientes.

## 11. Reglas de negocio

Estas reglas son la especificación formal de cómo el sistema debe interpretar la salida del modelo y convertirla en mensajes/recomendaciones. Ninguna de estas reglas está implementada todavía en código — se documentan aquí como especificación para la siguiente fase.

### 11.1 Reglas de nivel de demanda

| Condición | Resultado |
|---|---|
| `pedidos_estimados > 200` | Mostrar **"Alta demanda esperada"** |
| `120 <= pedidos_estimados <= 200` | Mostrar **"Demanda media-alta"** |
| `pedidos_estimados < 80` | Mostrar **"Demanda baja o normal"** |
| `80 <= pedidos_estimados < 120` | *(rango no cubierto explícitamente por el enunciado — ver nota)* |

> **Nota de validación:** el enunciado no define qué mensaje corresponde al rango 80–119. Se recomienda definirlo explícitamente en la siguiente fase (ej. "Demanda moderada") para que las 4 franjas cubran el 100% del dominio de `pedidos_estimados` sin huecos ni solapamientos.

### 11.2 Reglas de recomendación por producto/categoría

| Condición | Recomendación |
|---|---|
| Un producto supera el 25% de la demanda estimada total | Preparar más unidades de ese producto específico |
| Categoría **Pollo** supera un umbral definido | Recomendar comprar más pollo |
| Categoría **Hamburguesas** supera un umbral definido | Recomendar comprar pan, carne y empaques |
| **Papas** o **Salchipapas** con alta demanda | Recomendar revisar stock de papas y aceite |
| **Delivery** supera determinado porcentaje del total de pedidos | Recomendar aumentar envases y reforzar repartidores |

> **Nota de validación:** "un umbral definido" y "determinado porcentaje" quedan como parámetros de configuración pendientes de definir numéricamente (ej. Pollo > 30% de las unidades vendidas, Delivery > 40% de los pedidos). Se recomienda parametrizarlos (no dejarlos como constantes fijas en código) para poder ajustarlos sin desplegar cambios.

### 11.3 Reglas de recomendación por franja horaria

| Condición | Recomendación |
|---|---|
| Franja de almuerzo con alta demanda | Reforzar cocina |
| Franja de noche con alta demanda | Coordinar delivery y producción anticipada |
| Alta demanda en **más de un turno** simultáneamente | Recomendar planificación de producción por lotes |

### 11.4 Trazabilidad regla → categoría del centro de recomendaciones

| Regla | Categoría (sección 20) |
|---|---|
| Producto > 25% de demanda | Cocina |
| Pollo > umbral | Abastecimiento |
| Hamburguesas > umbral | Abastecimiento |
| Papas/Salchipapas alta demanda | Abastecimiento |
| Delivery > umbral | Operación + Personal |
| Almuerzo con alta demanda | Cocina + Personal |
| Noche con alta demanda | Operación + Personal |
| Demanda alta en +1 turno | Cocina (planificación por lotes) |

Esta tabla es la que debe usar el motor de reglas (a construir) para decidir en qué categoría del Centro de Recomendaciones debe aparecer cada mensaje generado.

## 12. Diseño del dataset objetivo

> **Actualizado (2026-07-04):** esta sección reemplaza el dimensionamiento original (~3,000 registros / 18–24 meses / catálogo amplio) por un diseño ajustado al tamaño real del negocio: **Ruta del Sabor es una empresa pequeña**, no una cadena grande, y el dataset debe reflejar esa escala.
>
> **Procedencia:** el dataset oficial **será generado externamente y entregado más adelante como archivo CSV/XLSX** para incorporarlo al módulo Dataset. Esta sección **no genera datos** — únicamente define la estructura (esquema, variables, dimensionamiento esperado) que ese archivo deberá cumplir para poder ser cargado, validado y usado en el entrenamiento.

**Dimensionamiento oficial:**

| Parámetro | Valor |
|---|---|
| Rango recomendado de registros | **5,000 a 9,000** |
| Rango ideal para este proyecto | **6,000 a 8,000** |
| Periodo histórico | **~18 meses** |
| Catálogo activo | **10 a 15 productos** (catálogo sugerido: 12 — ver 12.1) |
| Franjas horarias | **Desayuno, Almuerzo, Cena** (3 franjas/día) |
| Granularidad de cada fila | **Venta agregada de un producto, en una fecha y una franja horaria** (no por transacción/pedido individual) |

**Nota de consistencia (dimensionamiento vs. granularidad):** con ~18 meses (≈ 548 días) × 3 franjas × 12 productos del catálogo sugerido, el máximo teórico si **todos** los productos vendieran en **todas** las franjas de **todos** los días sería de ≈ 19,700 filas. El rango objetivo de 6,000–8,000 filas implica una densidad de ~30–40% de ese máximo, lo cual es realista para una empresa pequeña: no todos los productos rotan en todas las franjas (ej. una gaseosa o un jugo tiene poca presencia en Desayuno; un producto de baja rotación puede no venderse todos los días). Este supuesto de "dataset disperso, no cartesiano completo" es solo un criterio de **validación de razonabilidad** para cuando llegue el archivo oficial — no implica que este proyecto deba generar los datos.

**Decisión pendiente de alinear con la UI ya construida:** el módulo Predicciones ya implementa visualmente una franja horaria de 9 barras por hora (12p a 8p) y "turnos" con las etiquetas **Mañana / Tarde / Noche**. El nuevo diseño de dataset usa **Desayuno / Almuerzo / Cena** como única franja horaria (sin desagregar por hora). Antes de recibir el archivo oficial e implementar la carga/entrenamiento real, hay que decidir una de estas dos rutas — no se resuelve en este documento, solo se deja registrada como pendiente:

1. Mantener `franja_horaria` (Desayuno/Almuerzo/Cena) como única granularidad temporal del dataset, y en la siguiente fase renombrar/adaptar los "turnos" y el gráfico por hora de Predicciones a estas 3 franjas (implica un ajuste visual menor, fuera del alcance de esta fase de documentación).
2. Mantener ambas granularidades (franja gruesa para el dataset de entrenamiento + una distribución horaria estimada solo para fines visuales del gráfico), aceptando que el gráfico por hora sería una interpolación, no un dato entrenado directamente.

### 12.1 Catálogo de productos

Catálogo sugerido (12 productos activos, dentro del rango de 10 a 15):

| Producto | Categoría |
|---|---|
| Hamburguesa Clásica | Hamburguesas |
| Hamburguesa BBQ | Hamburguesas |
| Cheeseburger | Hamburguesas |
| Pollo Broaster | Pollo |
| Alitas BBQ | Pollo |
| Salchipapa Clásica | Papas / Salchipapas |
| Salchipapa Especial | Papas / Salchipapas |
| Pizza Personal | Pizzas |
| Pizza Familiar | Pizzas |
| Sándwich de Pollo | Sándwiches |
| Gaseosa | Bebidas |
| Jugo Natural | Bebidas |

Esto da **5 categorías** (Hamburguesas, Pollo, Papas/Salchipapas, Pizzas, Sándwiches, Bebidas — 6 si se separa Sándwiches de Pollo, como se hizo aquí), catálogo "limitado pero variado" acorde a una empresa pequeña. Este catálogo alimenta directamente las reglas de recomendación por categoría de la sección 11.2 (Pollo, Hamburguesas, Papas/Salchipapas ya están cubiertas 1:1 por esta lista).

### 12.2 Variables temporales

| Variable | Tipo | Descripción |
|---|---|---|
| `fecha` | Fecha | Fecha del registro |
| `dia_semana` | Categórica | Lunes … Domingo |
| `mes` | Categórica/Numérica | Mes del año (estacionalidad) |
| `franja_horaria` | Categórica | **Desayuno / Almuerzo / Cena** (única granularidad horaria del dataset; ver nota de alineación arriba) |
| `es_fin_semana` | Booleana | Sábado/Domingo |
| `es_feriado` | Booleana | Feriado o fecha especial |

### 12.3 Variables comerciales

| Variable | Tipo | Descripción |
|---|---|---|
| `producto` | Categórica | Nombre del producto (catálogo de 12, sección 12.1) |
| `categoria` | Categórica | Categoría del producto (Hamburguesas, Pollo, Papas/Salchipapas, Pizzas, Sándwiches, Bebidas) |
| `cantidad` | Numérica | Unidades vendidas de ese producto, en esa fecha y franja (dato agregado, no por transacción) |
| `precio_unitario` | Numérica | Precio unitario del producto |
| `total_venta` | Numérica | `cantidad * precio_unitario` (o con descuento aplicado) |
| `canal_venta` | Categórica | Local / Delivery |
| `promocion_activa` | Booleana | Si hubo promoción vigente |
| `tipo_promocion` | Categórica | Combo / 2x1 / Descuento / Ninguna |
| `descuento` | Numérica | % de descuento aplicado |

### 12.4 Variables climáticas

| Variable | Tipo | Descripción |
|---|---|---|
| `clima` | Categórica | Soleado / Nublado / Lluvioso, etc. |
| `temperatura` | Numérica | Temperatura del día |
| `lluvia` | Booleana/Numérica | Si llovió / milímetros de lluvia |

### 12.5 Variables operativas

| Variable | Tipo | Descripción |
|---|---|---|
| `personal_disponible` | Numérica | Personal en turno |
| `tiempo_preparacion_promedio` | Numérica | Minutos promedio de preparación |
| `delivery_porcentaje` | Numérica | % de pedidos por delivery ese día/franja |
| `stock_disponible` | Numérica/Booleana | Disponibilidad de insumos clave |
| `pedidos_dia_anterior` | Numérica | Pedidos del día inmediatamente anterior |

### 12.6 Variables derivadas/calculadas

| Variable | Tipo | Descripción |
|---|---|---|
| `promedio_ultimos_7_dias` | Numérica | Promedio móvil de 7 días |
| `demanda_promedio_categoria` | Numérica | Promedio histórico de demanda por categoría |
| `demanda_promedio_producto` | Numérica | Promedio histórico de demanda por producto |
| `nivel_demanda` | Categórica | Baja / Media / Alta (derivada de reglas, sección 11.1) |
| `nivel_operacion` | Categórica | Normal / Exigente / Crítico |

### 12.7 Variables objetivo

El enfoque de Machine Learning se mantiene en dos frentes de predicción, alineados 1:1 con estas dos variables objetivo:

| Variable | Rol |
|---|---|
| `pedidos_estimados` (o `cantidad_pedidos`) | **Variable objetivo principal** — predicción de la **demanda total por franja horaria** (Desayuno/Almuerzo/Cena). |
| `cantidad` / `demanda_producto` por producto | **Variable objetivo secundaria** — predicción de la **cantidad vendida por producto**, para el ranking de "productos más demandados". |

### 12.8 Clasificación de variables: obligatorias vs. opcionales

> **Procedencia del dataset:** el dataset oficial **será generado externamente** (fuera de este proyecto) y luego entregado como archivo **CSV o XLSX** para ser incorporado al módulo Dataset. Este documento **no genera datos sintéticos** ni define un script generador — solo especifica la estructura (esquema) que ese archivo deberá cumplir, para que el módulo Dataset pueda validarlo al recibirlo.

Para que el validador de estructura del módulo Dataset (sección 8.3 / 21.1) tenga un criterio objetivo de aceptación/rechazo, cada variable de las secciones 12.2 a 12.6 se clasifica como **obligatoria** (el archivo se rechaza si falta) u **opcional** (el archivo se acepta igual, pero sin poder usar esa variable como feature de enriquecimiento):

**Obligatorias (mínimo viable para entrenar):**

| Variable | Bloque | Motivo por el que es obligatoria |
|---|---|---|
| `fecha` | Temporal | Ancla toda la serie histórica; sin ella no hay orden temporal. |
| `dia_semana` | Temporal | Insumo directo de reglas de negocio (fin de semana) y variable de alta importancia esperada. |
| `franja_horaria` | Temporal | Nivel de agregación oficial del dataset (Desayuno/Almuerzo/Cena); define la granularidad de cada fila. |
| `producto` | Comercial | Sin esta columna no existe la variable objetivo secundaria (demanda por producto). |
| `categoria` | Comercial | Necesaria para las reglas de recomendación por categoría (sección 11.2) y el catálogo (12.1). |
| `cantidad` | Comercial | Base de ambas variables objetivo (agregada = demanda total; desagregada por producto = demanda por producto). |
| `canal_venta` | Comercial | Necesaria para la regla de recomendación de Delivery (sección 11.2). |
| `promocion_activa` | Comercial | Necesaria para separar el efecto de promociones del comportamiento base de demanda. |
| `pedidos_estimados` / `cantidad_pedidos` (agregado) | Objetivo | Variable objetivo principal — sin ella no hay problema de regresión que resolver. |

**Opcionales (enriquecen el modelo pero no bloquean la carga):**

| Variable | Bloque | Motivo por el que es opcional |
|---|---|---|
| `mes`, `es_fin_semana`, `es_feriado` | Temporal | Pueden derivarse de `fecha` si no vienen explícitas (cálculo automático en el backend). |
| `precio_unitario`, `total_venta`, `tipo_promocion`, `descuento` | Comercial | Enriquecen el análisis económico, pero no son indispensables para predecir cantidades/demanda. |
| `clima`, `temperatura`, `lluvia` | Climática | Bloque completo opcional — muchas empresas pequeñas no llevan este registro; el modelo debe poder entrenarse sin él. |
| `personal_disponible`, `tiempo_preparacion_promedio`, `delivery_porcentaje`, `stock_disponible` | Operativa | Deseables para las recomendaciones de Personal/Operación (sección 20), pero no bloquean el entrenamiento del modelo de demanda. |
| `pedidos_dia_anterior`, `promedio_ultimos_7_dias`, `demanda_promedio_categoria`, `demanda_promedio_producto` | Derivada | Todas son **calculables por el propio sistema** a partir de `fecha` + `cantidad` si no vienen en el archivo original; no deberían exigirse como columnas de entrada. |
| `nivel_demanda`, `nivel_operacion` | Derivada | Son salidas de las reglas de negocio (sección 11.1), no entradas — el sistema las calcula, no se le exigen al archivo cargado. |

Esta tabla (obligatorias vs. opcionales) es la que debe usar el validador de estructura que se implemente en el módulo Dataset durante la siguiente fase técnica, reemplazando la validación actual (que solo revisa la extensión del archivo, sin mirar columnas).

## 13. Validación del dataset actual contra el dataset objetivo

Se comparó la tabla de columnas mostrada actualmente en `templates/datasets/index.html` contra el dataset objetivo de la sección 12. El resultado detallado, columna por columna, está en el **Anexo (sección 23)**. Resumen:

- El dataset **actual es una demostración visual de 14 columnas hardcodeadas en el HTML** (3 filas de ejemplo), no un dataset real cargado ni persistido. No existe archivo CSV/Excel real en el repositorio (`media/` está vacío) ni modelo de base de datos que lo represente.
- De las ~30 variables del dataset objetivo, el dataset actual **cubre parcialmente el bloque temporal y comercial**, pero **no cubre en absoluto** las variables climáticas, la mayoría de las operativas, ni las variables derivadas de nivel de demanda/operación.
- **Conclusión:** el dataset actual **no cumple** con el flujo completo del sistema tal como se especifica en esta fase. Es apto como *mockup visual* de la tabla de vista previa, pero no como base real de entrenamiento. Ver plan de columnas faltantes en el Anexo.

## 14. Arquitectura Machine Learning

- **Tipo de aprendizaje:** Supervisado.
- **Tipo de problema:** Regresión (variable objetivo numérica y continua: cantidad de pedidos / unidades).
- **Entrada (features):** subconjunto de las variables temporales, comerciales, climáticas y operativas del dataset objetivo (sección 12), según el modelo entrenado y su selección de variables.
- **Salida (target):** `pedidos_estimados` (nivel general/turno) y `demanda_producto` (nivel producto).
- **Selección de modelo:** automática, por comparación de métricas de error (MAE, RMSE) y ajuste (R²) entre los modelos oficiales.
- **Persistencia del modelo:** pendiente de diseño — hoy no existe capa de almacenamiento de modelos entrenados (ni en BD ni en archivo serializado). Es un requisito a definir en la siguiente fase técnica, fuera del alcance de este documento.

## 15. Modelos utilizados

### 15.1 Regresión Lineal Múltiple

- **Rol:** modelo base e interpretable.
- **Por qué se incluye:** permite entender relaciones lineales simples entre variables (ej. "a más pedidos el día anterior, más pedidos hoy") y sirve como piso de comparación (*baseline*) para justificar el uso de un modelo más complejo.
- **Limitación esperada:** no captura bien relaciones no lineales ni interacciones entre variables categóricas (producto × turno × promoción, por ejemplo).

### 15.2 Random Forest Regressor

- **Rol:** modelo principal candidato.
- **Por qué se incluye:** captura relaciones no lineales y interacciones entre variables como hora, día, producto, canal y promociones — exactamente el tipo de patrón esperado en demanda gastronómica (ej. el efecto de una promoción es distinto en la franja de almuerzo que en la de noche).
- **Ventaja adicional:** entrega **importancia de variables** de forma nativa, insumo directo para la sección "Variables más importantes" del módulo Modelo Predictivo.

### 15.3 Selección automática del mejor modelo

El sistema debe comparar ambos modelos con las métricas de la sección 16 y seleccionar automáticamente el de mejor desempeño (menor MAE/RMSE, mayor R²) como el modelo "activo" que consumirá el módulo Predicciones. Este comportamiento **ya está representado visualmente** en Modelo Predictivo (badge "Mejor modelo" sobre Random Forest), pero **no está implementado como lógica real** — es un valor de demostración fijo.

## 16. Métricas de evaluación

| Métrica | Qué mide | Por qué importa para este negocio |
|---|---|---|
| **MAE** (Error Absoluto Medio) | Promedio del error en unidades de pedidos, fácil de interpretar ("nos equivocamos en X pedidos en promedio"). | Traducible directamente a lenguaje de negocio para el administrador. |
| **RMSE** (Raíz del Error Cuadrático Medio) | Similar al MAE pero penaliza más los errores grandes. | Relevante porque un error grande en un día de alta demanda (ej. feriado) es más costoso operativamente que varios errores pequeños. |
| **R²** (Coeficiente de determinación) | Qué proporción de la variabilidad de la demanda explica el modelo. | Sirve como métrica resumen de "qué tan confiable es el modelo en general" para mostrar en Dashboard y Modelo Predictivo. |

El **tiempo de entrenamiento** se documenta como un dato adicional a mostrar (no es una métrica de calidad del modelo, sino de costo computacional/operativo), requerido explícitamente por el enunciado de esta fase.

## 17. Flujo de entrenamiento

```
1. El administrador entra a "Modelo Predictivo" y presiona "Entrenar modelo".
2. El sistema toma el dataset validado desde el módulo Dataset (no lo vuelve a pedir).
3. Se separan variables de entrada (features) y variable objetivo (target).
4. Se entrena Regresión Lineal Múltiple con el set de entrenamiento.
5. Se entrena Random Forest Regressor con el mismo set de entrenamiento.
6. Se evalúan ambos modelos sobre un set de prueba (holdout) con MAE, RMSE y R².
7. Se registra el tiempo de entrenamiento de cada modelo.
8. El sistema compara métricas y selecciona automáticamente el mejor modelo.
9. Se marca ese modelo como "disponible para Predicciones" junto con la fecha/hora del entrenamiento.
10. Se actualizan las cards de Modelo Predictivo y del Dashboard (estado, R², último entrenamiento).
```

**Estado actual:** los pasos 2 a 9 son simulados (sin backend real); el botón "Entrenar modelo" dispara un modal de JavaScript que cambia textos con `setTimeout`, sin tocar datos reales. Es el comportamiento correcto **para esta fase de documentación**, pero debe quedar explícito que **no hay entrenamiento real todavía**.

## 18. Flujo de predicción

```
1. El administrador entra a "Predicciones".
2. Selecciona fecha a consultar, rango de predicción y franja horaria.
3. (Opcional) Abre "Opciones avanzadas de simulación" y activa una promoción hipotética.
4. El sistema toma el modelo marcado como "mejor modelo disponible" (de Modelo Predictivo).
5. Genera la predicción de pedidos estimados para el rango/turno solicitado.
6. Calcula, a partir de esa predicción:
   - Franja horaria de mayor demanda.
   - Productos más demandados (vía demanda_promedio_producto y el propio modelo).
   - Nivel esperado de operación (regla de sección 11.1).
   - Predicción desagregada por turno (Mañana/Tarde/Noche).
7. Aplica el motor de reglas de negocio (sección 11) sobre el resultado.
8. Muestra el Centro de Recomendaciones Inteligentes, categorizado (sección 19-20).
```

**Importante (regla de arquitectura):** Predicciones **nunca** debe entrenar modelos ni leer el archivo de dataset directamente — solo debe consumir la salida ya entrenada/serializada del módulo Modelo Predictivo. Esto es lo que garantiza la separación de responsabilidades entre los 3 módulos centrales (Dataset → Modelo Predictivo → Predicciones).

## 19. Centro de recomendaciones inteligentes

El Centro de Recomendaciones es la traducción de la predicción numérica a lenguaje operativo accionable. Debe vivir principalmente en **Predicciones** (ya que depende de una consulta concreta de fecha/turno), y su versión resumida ("recomendaciones rápidas") puede aparecer también en **Dashboard**.

Reglas de diseño funcional del Centro:

1. Cada recomendación pertenece a **una o más** de las 4 categorías oficiales (sección 20).
2. Cada recomendación se dispara por una **regla de negocio** concreta (trazabilidad en sección 11.4), nunca por texto fijo sin condición.
3. Las recomendaciones deben poder filtrarse/agruparse visualmente por categoría (sin necesidad de rediseñar cards — puede ser tan simple como una etiqueta de categoría sobre el ítem de lista actual).
4. El módulo Predicciones es el único que debe mostrar el centro completo; Dashboard solo debe mostrar una versión resumida ("recomendaciones rápidas", ya existente).

## 20. Recomendaciones por categoría

### 20.1 Abastecimiento

- Comprar más pollo.
- Comprar más pan.
- Comprar más papas.
- Revisar bebidas.
- Aumentar envases.

### 20.2 Cocina

- Preparar ingredientes antes de la hora pico.
- Adelantar producción.
- Priorizar productos con alta demanda.
- Reforzar preparación de combos.

### 20.3 Personal

- Reforzar cocina.
- Reforzar delivery.
- Asignar apoyo en despacho.
- Aumentar personal en turno crítico.

### 20.4 Operación

- Preparar envases.
- Verificar stock.
- Organizar despacho.
- Coordinar delivery.
- Anticipar tiempos de preparación.

> Estas 4 categorías y sus ejemplos son la taxonomía oficial a implementar. La lista actual de "Recomendaciones operativas" en Predicciones (3 ítems sin categorizar) debe evolucionar hacia esta estructura en la siguiente fase de construcción (no en esta fase de documentación).

## 21. Ajustes necesarios en Dataset, Modelo Predictivo y Predicciones

Esta sección resume, módulo por módulo, los ajustes **funcionales** (no visuales) detectados al comparar el estado actual contra esta especificación. Ninguno de estos ajustes se implementó en esta fase — quedan documentados para la siguiente.

### 21.1 Dataset

| Requerido | Estado actual | Ajuste necesario |
|---|---|---|
| Cantidad de registros | ✅ Mostrado (KPI "Total de registros") | Ninguno |
| Cantidad de columnas | ❌ No mostrado | Agregar KPI o dato explícito |
| Periodo histórico | ✅ Mostrado como "Rango de fechas" | Ninguno |
| Valores faltantes | ❌ No mostrado | Agregar indicador de % o cantidad de valores faltantes |
| Vista previa | ✅ Tabla de ejemplo | Ninguno (falta que sea dinámica, no hardcodeada) |
| Estado de validación | ⚠️ Parcial (mensaje de éxito/error de carga, solo por extensión) | Ampliar a validación real de estructura/columnas |
| Columnas detectadas | ❌ No se listan explícitamente | Agregar listado de columnas detectadas en el archivo subido |
| Errores por columnas obligatorias faltantes | ❌ No existe | Definir columnas obligatorias (sección 12) y mostrar error específico si faltan |

### 21.2 Modelo Predictivo

| Requerido | Estado actual | Ajuste necesario |
|---|---|---|
| Entrenar modelos | ⚠️ Simulado (JS) | Ninguno visual; pendiente lógica real (fuera de esta fase) |
| Comparar modelos | ✅ Mostrado (Regresión Lineal vs. Random Forest) | Ninguno |
| Selección automática del mejor | ⚠️ Simulado (badge fijo) | Pendiente lógica real |
| MAE / RMSE / R² | ✅ Mostrado para ambos modelos | Ninguno |
| Tiempo de entrenamiento | ❌ No mostrado | Agregar dato explícito por modelo |
| Variables utilizadas | ✅ Mostrado ("Variables de entrada") | Ninguno |
| Importancia de variables | ✅ Mostrado (ranking con barras) | Ninguno |
| Mejor modelo seleccionado | ✅ Mostrado (badge "Mejor modelo") | Ninguno |
| Fecha del último entrenamiento | ✅ Mostrado | Ninguno |
| Estado del modelo | ✅ Mostrado | Ninguno |

**Conclusión:** Modelo Predictivo es el módulo más completo funcionalmente. Solo falta el dato de **tiempo de entrenamiento** como ajuste visual menor (nueva card o dato dentro de una card existente, a definir sin alterar el layout general).

### 21.3 Predicciones

| Requerido | Estado actual | Ajuste necesario |
|---|---|---|
| Formulario principal simple (fecha, rango, franja) | ✅ Ya ajustado en la fase anterior | Ninguno |
| Promociones como simulación avanzada opcional | ✅ Ya implementado (`<details>` colapsable) | Ninguno |
| Cantidad esperada de pedidos | ✅ Mostrado | Ninguno |
| Franja horaria con mayor demanda | ✅ Mostrado | Ninguno |
| Productos más demandados | ✅ Mostrado | Ninguno |
| Nivel esperado de operación | ⚠️ Parcial — hay badges tipo "Alta demanda"/"Hora pico" pero no un indicador explícito de "nivel de operación" (Normal/Exigente/Crítico) | Agregar indicador explícito de nivel de operación, alineado a la regla 11.1 |
| Predicción por turnos (Mañana/Tarde/Noche) | ✅ Ya implementado (3 cards con los 5 datos pedidos) | Ninguno |
| Gráfico de demanda por hora | ✅ Mostrado | Ninguno |
| Gráfico de productos más demandados | ✅ Mostrado (como lista con barras) | Ninguno |
| Centro de recomendaciones inteligentes categorizado | ❌ Existe solo una lista plana de 3 recomendaciones sin categoría | Reestructurar hacia las 4 categorías de la sección 20 |

**Elementos que deben moverse o eliminarse de Predicciones** (pregunta específica de esta fase): con el ajuste ya aplicado en la fase anterior, **ya no quedan elementos de configuración del modelo** dentro de Predicciones (no hay MAE/RMSE/R², no hay comparación de modelos, no hay entrenamiento). El único punto de mejora restante es transformar la lista plana de recomendaciones en el Centro de Recomendaciones categorizado — **no es algo que deba moverse a otro módulo**, sino una estructura a enriquecer dentro del mismo módulo Predicciones, ya que la categorización depende de la consulta puntual de fecha/turno, no del modelo en sí.

## 22. Conclusiones

1. **La estructura de módulos ya está correctamente ordenada.** Los 5 módulos oficiales (Inicio, Dashboard, Dataset, Modelo Predictivo, Predicciones) existen, están activos en el sidebar, y Reportes/Registro de Pedidos ya están correctamente deshabilitados/fuera del flujo principal — no se requiere ningún cambio de navegación ni de rutas.
2. **La separación de responsabilidades entre Dataset → Modelo Predictivo → Predicciones ya es conceptualmente correcta** tras el ajuste funcional de la fase anterior: Predicciones no entrena ni carga datos, Modelo Predictivo no carga dataset, Dataset no entrena ni predice.
3. **Todo el contenido actual es demostrativo (mock data), no real.** No hay modelos de base de datos, no hay dependencias de ML instaladas, no hay archivos de dataset reales. Esto es coherente con el alcance de esta fase (documentar y validar, no construir).
4. **El módulo con más brechas funcionales es Dataset** (validación real de estructura, columnas obligatorias, valores faltantes) seguido por el Centro de Recomendaciones de Predicciones (falta categorización).
5. **El dataset objetivo definido en esta fase es sustancialmente más rico** que el dataset de demostración actual — el esquema formal de columnas obligatorias vs. opcionales ya quedó definido en la sección 12.8, listo para usarse como criterio de validación en cuanto llegue el archivo oficial.
6. **Ambos modelos (Regresión Lineal y Random Forest) son adecuados para el objetivo de negocio**: el primero aporta interpretabilidad y sirve de línea base; el segundo captura las relaciones no lineales típicas de la demanda gastronómica y aporta importancia de variables. La estrategia de selección automática por métricas es la correcta.
7. **El dataset oficial será entregado externamente** (archivo CSV/XLSX) y no se genera en este proyecto ni en este documento. La siguiente fase técnica debe: (a) recibir ese archivo, (b) construir el validador de estructura del módulo Dataset contra la tabla de la sección 12.8, (c) resolver la decisión pendiente de `franja_horaria` (sección 12) antes de tocar las plantillas de Predicciones, y (d) diseñar el motor de reglas de negocio (sección 11) como una capa de servicio independiente (ej. dentro de `machine_learning/services/` o un nuevo módulo de reglas).

---

## 23. Anexo — Validación específica solicitada

### 23.1 ¿El dataset actual cumple con el flujo del sistema?

**No.** El dataset mostrado en `templates/datasets/index.html` es una tabla de demostración con 3 filas de ejemplo escritas directamente en el HTML. No existe un archivo real cargado (`media/` está vacío), ni un modelo de base de datos que lo represente (`datasets/models.py` está vacío). Cumple su función *visual* (mostrar cómo se vería la vista previa), pero no cumple el flujo funcional completo de carga → validación → entrenamiento real.

### 23.2 ¿Qué columnas faltan?

Comparando el dataset objetivo (sección 12, ~29 variables) contra las 14 columnas actuales (`fecha, dia_semana, hora, franja_horaria, producto, categoria, cantidad, canal_pedido, promocion_activa, tipo_promocion, descuento, pedidos_dia_anterior, promedio_ultimos_7_dias, demanda`):

**Presentes (parcial):** `fecha`, `dia_semana` (temporales); `producto`, `categoria`, `cantidad`, `canal_pedido` (≈ `canal_venta`), `promocion_activa`, `tipo_promocion`, `descuento` (comerciales); `pedidos_dia_anterior`, `promedio_ultimos_7_dias` (operativa/derivada); `demanda` (objetivo principal, aunque con nombre distinto al sugerido `pedidos_estimados`/`cantidad_pedidos`).

**Presentes pero con valores a reconciliar:** `franja_horaria` existe como columna en ambos, pero el mock actual usa valores tipo *Mañana/Mediodía/Noche* mientras que el dataset objetivo (sección 12.2) define oficialmente **Desayuno/Almuerzo/Cena**; y `hora` existe como columna suelta en el mock actual, pero el dataset objetivo la elimina como variable independiente (la granularidad pasa a ser por franja, no por hora exacta — ver nota de consistencia en sección 12). `cantidad` también sirve como base de la variable objetivo secundaria (`demanda_producto`), aunque todavía no está agregada como tal.

**Faltantes por completo:**

- Temporales: `mes`, `es_fin_semana`, `es_feriado`.
- Comerciales: `precio_unitario`, `total_venta`.
- Climáticas (las 3): `clima`, `temperatura`, `lluvia`.
- Operativas: `personal_disponible`, `tiempo_preparacion_promedio`, `delivery_porcentaje`, `stock_disponible`.
- Derivadas: `demanda_promedio_categoria`, `demanda_promedio_producto`, `nivel_demanda`, `nivel_operacion`.

**Recomendación:** la clasificación obligatorias/opcionales ya no queda abierta — se formalizó en la **sección 12.8** (`fecha`, `dia_semana`, `franja_horaria`, `producto`, `categoria`, `cantidad`, `canal_venta`, `promocion_activa` y la variable objetivo agregada son obligatorias; el resto es opcional/enriquecimiento). El validador de estructura del módulo Dataset (sección 8.3 / 21.1) debe implementarse contra esa tabla cuando se reciba el archivo oficial. También conviene decidir y documentar la reconciliación de valores de `franja_horaria` (Mañana/Tarde/Noche, ya usado en la UI de Predicciones, vs. Desayuno/Almuerzo/Cena, definido como oficial en 12.2) antes de construir ese validador o de tocar las plantillas.

### 23.3 ¿Regresión Lineal y Random Forest cumplen el objetivo del negocio?

**Sí, en conjunto.** Ver detalle en sección 15. Regresión Lineal aporta interpretabilidad y una línea base contra la cual medir mejoras; Random Forest está mejor preparado para capturar las interacciones no lineales entre hora, día, producto, canal, clima y promociones que son típicas del negocio gastronómico. La estrategia de comparar ambos con MAE/RMSE/R² y elegir automáticamente el mejor (sección 15.3) es la correcta y ya está representada visualmente en Modelo Predictivo.

### 23.4 ¿Qué debe mostrarse en Modelo Predictivo?

Ver sección 8.4 y tabla 21.2. En síntesis, ya se muestra casi todo lo requerido (estado, R², comparación MAE/RMSE/R², variables e importancia, mejor modelo, último entrenamiento). Único faltante: **tiempo de entrenamiento** por modelo.

### 23.5 ¿Qué debe mostrarse en Predicciones?

Ver sección 8.5 y tabla 21.3. Ya se muestra casi todo lo requerido tras el ajuste de la fase anterior (formulario simple, promociones como opción avanzada, KPIs, resultado, turnos, gráfico por hora, productos top). Único faltante estructural: el **Centro de Recomendaciones Inteligentes categorizado** (Abastecimiento/Cocina/Personal/Operación) en lugar de la lista plana actual, y un indicador explícito de **nivel esperado de operación**.

### 23.6 ¿Qué elementos actuales deberían moverse o eliminarse de Predicciones?

**Ninguno pendiente.** El ajuste funcional de la fase anterior ya sacó de Predicciones todo lo que correspondía a configuración/evaluación del modelo (no hay MAE/RMSE/R², no hay comparación de modelos, no hay botón de entrenamiento) y todo lo que correspondía a datos crudos del histórico (no hay tabla de dataset). Lo único que resta es **enriquecer** (no mover) la sección de recomendaciones hacia el formato categorizado del Centro de Recomendaciones Inteligentes, ya que esa lógica pertenece naturalmente a Predicciones (depende de la consulta puntual), no a Dataset ni a Modelo Predictivo.

---

*Fin del documento. Este archivo no modifica diseño visual, estilos, colores, layout ni funcionalidades del sistema — es exclusivamente una especificación funcional y un reporte de validación.*
