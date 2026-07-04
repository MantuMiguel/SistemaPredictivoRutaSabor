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
    └── charts/           # PLANEADO, no creado todavía — guardará los 9 gráficos Matplotlib (sección 14.1)
```

Características actuales de la arquitectura (estado real verificado en el código):

- **Sin modelos de base de datos propios**: los 4 archivos `models.py` de las apps están vacíos (solo el boilerplate de Django). No existe persistencia de dataset, entrenamientos ni predicciones — todo lo mostrado en las plantillas es **contenido de demostración estático**.
- **Sin dependencias de Machine Learning instaladas**: no hay `pandas`, `numpy`, `scikit-learn` ni `matplotlib` en el entorno virtual. El módulo `machine_learning/services/` existe como carpeta pero solo contiene un `__init__.py` vacío.
- **`media/charts/` todavía no existe**: es la carpeta planeada para los 9 gráficos generados con Matplotlib (sección 14.1); no se crea en esta fase porque no hay lógica de entrenamiento real que la use todavía.
- **El dataset oficial se generará externamente**: no se produce dentro de este proyecto ni con un script propio; se recibirá como archivo CSV/XLSX y se cargará a través del módulo Dataset una vez implementada la validación real (sección 12.6).
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

**Estado actual:** ya cubre visualmente casi todo lo requerido — carga de archivo `.csv`/`.xlsx`, botón "Validar dataset", estado vacío amigable, 5 cards de resumen (estado del dataset, registros detectados, columnas detectadas, periodo histórico, valores faltantes), sección de columnas esperadas (obligatorias y opcionales, sección 12.2/12.3), advertencia de ejemplo por columnas opcionales faltantes, y vista previa con las 10 columnas obligatorias oficiales. **Brecha identificada:** la validación sigue siendo **solo de extensión** (JavaScript, sin backend); falta implementar con Pandas la lectura real de encabezados y la lógica de aceptación/rechazo de la sección 12.6 — pendiente para cuando se reciba el archivo oficial (ver sección 21).

### 8.4 Modelo Predictivo

**Propósito:** único módulo responsable del ciclo de Machine Learning.

**Debe permitir:** entrenar modelos, compararlos, seleccionar automáticamente el mejor, y marcarlo como disponible para Predicciones.

**Modelos oficiales:** Regresión Lineal Múltiple y Random Forest Regressor.

**Debe mostrar:** MAE, RMSE, R², tiempo de entrenamiento, variables utilizadas, importancia de variables, mejor modelo seleccionado, fecha del último entrenamiento, estado del modelo, y los **9 gráficos generados con Matplotlib** (procesamiento con Pandas) descritos en la sección 14.1: demanda por franja horaria, productos más vendidos, comparación de modelos por MAE/RMSE/R², reales vs. predichos (Regresión Lineal y Random Forest), importancia de variables (Random Forest) y coeficientes (Regresión Lineal).

**No debe:** cargar dataset ni ofrecer la consulta de predicciones futuras como función principal.

**Estado actual:** este es el módulo **más alineado** con la especificación en cuanto a métricas y flujo. Ya muestra estado del modelo, R², variable más influyente, último entrenamiento, botón "Entrenar modelo" (simulado con un modal JS), comparación Regresión Lineal vs. Random Forest con MAE/RMSE/R², ranking de importancia de variables y un flujo visual Dataset → Procesamiento → Entrenamiento → Predicción. **Brechas identificadas:** (1) no muestra explícitamente el **tiempo de entrenamiento** como dato independiente; (2) no existe todavía ningún **gráfico Matplotlib** — los 9 gráficos de la sección 14.1 están **especificados pero no implementados**, y no existe la carpeta `media/charts/` ni la dependencia de Pandas/Matplotlib instalada en el entorno.

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

### 12.2 Columnas obligatorias del archivo importado

> **Actualizado (2026-07-04, v2):** esta lista es ahora la **oficial y definitiva** para la lógica de importación real (reemplaza el listado tentativo de la versión anterior de este documento, que incluía `dia_semana` como obligatoria y dejaba `precio_unitario`/`tipo_promocion`/`descuento` como opcionales). Ya está reflejada 1:1 en `templates/datasets/index.html`.

Si el archivo **no** incluye alguna de estas 10 columnas, debe **rechazarse** por completo (no se procesa ni parcialmente):

| # | Variable | Tipo | Descripción |
|---|---|---|---|
| 1 | `fecha` | Fecha | Fecha de la venta agregada |
| 2 | `franja_horaria` | Categórica | **Desayuno / Almuerzo / Cena** — granularidad horaria oficial del dataset (ver nota de alineación arriba) |
| 3 | `producto` | Categórica | Nombre del producto (catálogo de 12, sección 12.1) |
| 4 | `categoria` | Categórica | Categoría del producto (Hamburguesas, Pollo, Papas/Salchipapas, Pizzas, Sándwiches, Bebidas) |
| 5 | `cantidad_vendida` | Numérica | Unidades vendidas de ese producto, en esa fecha y franja (dato agregado, no por transacción) |
| 6 | `canal_venta` | Categórica | Local / Delivery |
| 7 | `promocion_activa` | Booleana | Si hubo promoción vigente |
| 8 | `tipo_promocion` | Categórica | Combo / 2x1 / Descuento / Ninguna |
| 9 | `descuento_pct` | Numérica | % de descuento aplicado |
| 10 | `precio_unitario` | Numérica | Precio unitario del producto |

### 12.3 Columnas opcionales del archivo importado

Si faltan una o más de estas 7 columnas, el archivo **se acepta igual**, pero el sistema debe mostrar una **advertencia** indicando cuáles faltan y que el modelo se entrenará con menos variables de enriquecimiento:

| # | Variable | Tipo | Descripción |
|---|---|---|---|
| 1 | `clima` | Categórica | Soleado / Nublado / Lluvioso, etc. |
| 2 | `temperatura` | Numérica | Temperatura del día |
| 3 | `lluvia` | Booleana/Numérica | Si llovió / milímetros de lluvia |
| 4 | `personal_disponible` | Numérica | Personal en turno |
| 5 | `tiempo_preparacion_min` | Numérica | Minutos promedio de preparación |
| 6 | `stock_disponible` | Numérica/Booleana | Disponibilidad de insumos clave |
| 7 | `porcentaje_delivery` | Numérica | % de pedidos por delivery ese día/franja |

### 12.4 Variables calculadas por el sistema (no se piden en el archivo)

Estas variables **no deben exigirse** en el CSV/XLSX importado — el sistema las calcula automáticamente a partir de las columnas de las secciones 12.2/12.3, antes o durante el entrenamiento:

| Variable | Se calcula a partir de |
|---|---|
| `dia_semana`, `mes`, `es_fin_semana`, `es_feriado` | `fecha` |
| `total_venta` | `cantidad_vendida * precio_unitario` (con `descuento_pct` aplicado) |
| `pedidos_dia_anterior`, `promedio_ultimos_7_dias` | Serie histórica agregada por `fecha` |
| `demanda_promedio_categoria`, `demanda_promedio_producto` | Histórico agregado por `categoria` / `producto` |
| `nivel_demanda`, `nivel_operacion` | Reglas de negocio (sección 11.1), aplicadas sobre la predicción, no sobre el archivo cargado |

### 12.5 Variables objetivo

El enfoque de Machine Learning se mantiene en dos frentes de predicción, alineados 1:1 con estas dos variables objetivo:

| Variable | Rol |
|---|---|
| `pedidos_estimados` (o `cantidad_pedidos`, agregado a partir de `cantidad_vendida`) | **Variable objetivo principal** — predicción de la **demanda total por franja horaria** (Desayuno/Almuerzo/Cena). |
| `cantidad_vendida` por producto (`demanda_producto`) | **Variable objetivo secundaria** — predicción de la **cantidad vendida por producto**, para el ranking de "productos más demandados". |

### 12.6 Lógica de importación y validación (especificación para el backend)

Esta es la regla formal que debe implementar el backend del módulo Dataset (con Pandas) al recibir un archivo real — **todavía no implementada**, solo especificada aquí y ya simulada visualmente en la plantilla:

1. Verificar extensión (`.csv` o `.xlsx`). Si no corresponde → **rechazar**, mensaje de formato no soportado.
2. Leer los encabezados del archivo (sin cargar todo el contenido a memoria si el archivo es grande).
3. Comparar los encabezados contra las **10 columnas obligatorias** (sección 12.2).
   - Si falta **una o más** → **rechazar el dataset completo**, listando exactamente qué columnas obligatorias faltan.
4. Comparar los encabezados contra las **7 columnas opcionales** (sección 12.3).
   - Si falta una o más → **aceptar igual**, pero mostrar una advertencia listando cuáles faltan (tal como ya se simula en `templates/datasets/index.html`).
5. Si pasa 3 y 4 → marcar el dataset como **"Válido"**, calcular el resumen (registros, columnas detectadas, periodo histórico, % de valores faltantes) y dejarlo disponible para el módulo Modelo Predictivo.
6. El sistema **acepta cualquier archivo** que cumpla este esquema — no depende de nombres de archivo, tamaño exacto de filas ni de un generador específico, ya que el dataset oficial se producirá **externamente** y se cargará después.

## 13. Validación del dataset actual contra el dataset objetivo

Se comparó la tabla de columnas mostrada actualmente en `templates/datasets/index.html` contra el esquema oficial de la sección 12. El resultado detallado está en el **Anexo (sección 23)**. Resumen:

- El módulo Dataset **ya refleja visualmente el esquema oficial**: la vista previa usa exactamente las 10 columnas obligatorias de la sección 12.2 (`fecha, franja_horaria, producto, categoria, cantidad_vendida, canal_venta, promocion_activa, tipo_promocion, descuento_pct, precio_unitario`), la sección "Columnas esperadas" lista las 7 opcionales de 12.3, y existe un estado vacío + una advertencia de ejemplo por columnas opcionales faltantes. Esto es **coherente en estructura** con el dataset objetivo.
- Sigue siendo, sin embargo, **una demostración**: no hay archivo real cargado (`media/` está vacío), no hay backend con Pandas leyendo el archivo, y la validación de JavaScript solo revisa la **extensión** (`.csv`/`.xlsx`), no el contenido ni los encabezados reales. La lógica de importación real (sección 12.6) está **especificada pero no implementada**.
- **Conclusión:** el dataset actual **no cumple todavía** con el flujo funcional completo (falta el backend de carga/validación real), pero la plantilla ya está **estructuralmente lista** para recibir el archivo oficial y aplicar la lógica de la sección 12.6 en cuanto se implemente.

## 14. Arquitectura Machine Learning

- **Tipo de aprendizaje:** Supervisado.
- **Tipo de problema:** Regresión (variable objetivo numérica y continua: cantidad de pedidos / unidades).
- **Entrada (features):** subconjunto de las columnas obligatorias y opcionales del dataset oficial (secciones 12.2/12.3), más las variables calculadas por el sistema (12.4), según el modelo entrenado y su selección de variables.
- **Salida (target):** `pedidos_estimados` (nivel general/franja horaria) y `demanda_producto` (nivel producto).
- **Selección de modelo:** automática, por comparación de métricas de error (MAE, RMSE) y ajuste (R²) entre los modelos oficiales.
- **Persistencia del modelo:** pendiente de diseño — hoy no existe capa de almacenamiento de modelos entrenados (ni en BD ni en archivo serializado). Es un requisito a definir en la siguiente fase técnica, fuera del alcance de este documento.
- **Librería de procesamiento:** **Pandas** — leerá el archivo importado (CSV/XLSX), aplicará la validación de la sección 12.6, calculará las variables derivadas (12.4) y preparará las matrices de entrenamiento/prueba para ambos modelos. **Todavía no está instalada** en el entorno (`venv`) ni usada en ningún `views.py`.
- **Librería de visualización:** **Matplotlib** — generará los 9 gráficos oficiales (sección 14.1) como imágenes estáticas, no como gráficos interactivos en el navegador. **Todavía no está instalada** ni integrada.

### 14.1 Generación de gráficos (Pandas + Matplotlib)

> **Estado: especificado, no implementado.** Esta subsección documenta el enfoque a construir en una fase técnica posterior. No se ha escrito código de generación de gráficos, no se ha instalado Matplotlib, y no se ha creado la carpeta `media/charts/`.

**Flujo previsto:** durante el entrenamiento (sección 17), el módulo Modelo Predictivo usará Pandas para preparar los datos y Matplotlib para renderizar cada gráfico como imagen (`.png`), guardándolas en `media/charts/` con un nombre de archivo estable (ej. `demanda_por_franja.png`, `mae_comparacion.png`). Las vistas Django las mostrarán luego con una etiqueta `<img>` apuntando a la URL de `MEDIA_URL` (`/media/charts/...`) — no se generan en el navegador ni con librerías JS de gráficos.

| # | Gráfico | Tipo sugerido | Fuente de datos | Módulo donde se muestra |
|---|---|---|---|---|
| 1 | Demanda por franja horaria | Barras (Desayuno/Almuerzo/Cena) | Dataset agregado por `franja_horaria` | Modelo Predictivo (exploratorio) y/o Predicciones |
| 2 | Productos más vendidos | Barras horizontales, top N | Dataset agregado por `producto` | Modelo Predictivo (exploratorio) y/o Predicciones |
| 3 | Comparación de modelos por MAE | Barras (Regresión Lineal vs. Random Forest) | Resultado de evaluación de ambos modelos | Modelo Predictivo |
| 4 | Comparación de modelos por RMSE | Barras (Regresión Lineal vs. Random Forest) | Resultado de evaluación de ambos modelos | Modelo Predictivo |
| 5 | Comparación de modelos por R² | Barras (Regresión Lineal vs. Random Forest) | Resultado de evaluación de ambos modelos | Modelo Predictivo |
| 6 | Reales vs. predichos — Regresión Lineal | Dispersión (scatter) | Predicciones del modelo sobre el set de prueba | Modelo Predictivo |
| 7 | Reales vs. predichos — Random Forest | Dispersión (scatter) | Predicciones del modelo sobre el set de prueba | Modelo Predictivo |
| 8 | Importancia de variables — Random Forest | Barras horizontales | `feature_importances_` del modelo entrenado | Modelo Predictivo |
| 9 | Coeficientes — Regresión Lineal | Barras horizontales (positivo/negativo) | `coef_` del modelo entrenado | Modelo Predictivo |

**Notas de diseño para la implementación futura:**

- Los gráficos #1 y #2 son de **exploración de datos** (no dependen de haber entrenado un modelo) — podrían generarse apenas el Dataset se valide, no solo durante el entrenamiento.
- Los gráficos #3 a #9 son de **evaluación de modelo** — solo tienen sentido después de un entrenamiento completo, y deben regenerarse (sobrescribiendo el archivo anterior) cada vez que se reentrena.
- `media/charts/` no existe todavía en el repositorio; deberá crearse junto con la lógica de entrenamiento, y `MEDIA_ROOT`/`MEDIA_URL` (ya configurados en `settings.py`) son suficientes para servirla sin cambios adicionales de configuración.
- Ninguno de estos 9 gráficos se muestra hoy en ninguna plantilla — es trabajo pendiente completo para la fase de implementación real del entrenamiento.

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
3. Con Pandas: se calculan las variables derivadas (sección 12.4) y se separan
   variables de entrada (features) y variable objetivo (target).
4. Se entrena Regresión Lineal Múltiple con el set de entrenamiento.
5. Se entrena Random Forest Regressor con el mismo set de entrenamiento.
6. Se evalúan ambos modelos sobre un set de prueba (holdout) con MAE, RMSE y R².
7. Se registra el tiempo de entrenamiento de cada modelo.
8. El sistema compara métricas y selecciona automáticamente el mejor modelo.
9. Con Matplotlib: se generan y guardan en media/charts/ los 9 gráficos
   oficiales (sección 14.1), sobrescribiendo los de la corrida anterior.
10. Se marca ese modelo como "disponible para Predicciones" junto con la fecha/hora del entrenamiento.
11. Se actualizan las cards de Modelo Predictivo y del Dashboard (estado, R², último entrenamiento)
    y se muestran los gráficos recién generados en la vista de Modelo Predictivo.
```

**Estado actual:** los pasos 2 a 11 son simulados (sin backend real); el botón "Entrenar modelo" dispara un modal de JavaScript que cambia textos con `setTimeout`, sin tocar datos reales ni generar gráficos. Es el comportamiento correcto **para esta fase de documentación**, pero debe quedar explícito que **no hay entrenamiento real ni generación de gráficos todavía** — ambos (Pandas y Matplotlib) están únicamente especificados (secciones 12.6 y 14.1).

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
| Cantidad de registros | ✅ Mostrado ("Registros detectados") | Ninguno visual; pendiente cálculo real |
| Cantidad de columnas | ✅ Mostrado ("Columnas detectadas", ej. "14/17") | Ninguno visual; pendiente cálculo real |
| Periodo histórico | ✅ Mostrado ("Periodo histórico") | Ninguno |
| Valores faltantes | ✅ Mostrado (% en card de resumen) | Ninguno visual; pendiente cálculo real |
| Vista previa | ✅ Tabla con las 10 columnas obligatorias oficiales | Ninguno visual (falta que sea dinámica, no hardcodeada) |
| Estado de validación | ✅ Mostrado (card "Estado del dataset" + estado vacío) | Ninguno visual |
| Columnas detectadas (listado) | ✅ Sección "Columnas esperadas" (obligatorias/opcionales) | Ninguno visual; falta marcar cuáles de esas SÍ vinieron en el archivo real |
| Advertencia por columnas opcionales faltantes | ✅ Mostrado (ejemplo estático) | Ninguno visual; pendiente cálculo real |
| Errores por columnas obligatorias faltantes | ⚠️ Solo valida extensión, no columnas | Implementar con Pandas la lógica de la sección 12.6 (leer encabezados y comparar contra 12.2) |

**Conclusión:** el módulo Dataset ya está **visualmente completo y estructurado** según el esquema oficial (secciones 12.2/12.3). El único ajuste pendiente es de backend, no de vista: reemplazar la validación de solo-extensión por la lógica real de la sección 12.6 usando Pandas, cuando se reciba el archivo oficial.

### 21.2 Modelo Predictivo

| Requerido | Estado actual | Ajuste necesario |
|---|---|---|
| Entrenar modelos | ⚠️ Simulado (JS) | Ninguno visual; pendiente lógica real (fuera de esta fase) |
| Comparar modelos | ✅ Mostrado (Regresión Lineal vs. Random Forest) | Ninguno |
| Selección automática del mejor | ⚠️ Simulado (badge fijo) | Pendiente lógica real |
| MAE / RMSE / R² | ✅ Mostrado para ambos modelos | Ninguno |
| Tiempo de entrenamiento | ❌ No mostrado | Agregar dato explícito por modelo |
| Variables utilizadas | ✅ Mostrado ("Variables de entrada") | Ninguno |
| Importancia de variables | ✅ Mostrado (ranking con barras, solo texto) | Complementar con el gráfico Matplotlib #8 (sección 14.1) |
| Mejor modelo seleccionado | ✅ Mostrado (badge "Mejor modelo") | Ninguno |
| Fecha del último entrenamiento | ✅ Mostrado | Ninguno |
| Estado del modelo | ✅ Mostrado | Ninguno |
| 9 gráficos Matplotlib (sección 14.1) | ❌ No existen — ni la lógica de generación ni la carpeta `media/charts/` | Implementar generación con Pandas + Matplotlib y mostrarlas como `<img>` en la vista |

**Conclusión:** Modelo Predictivo sigue siendo el módulo más completo en cuanto a métricas y flujo. Los dos pendientes reales son: (1) el dato de **tiempo de entrenamiento**, y (2) los **9 gráficos Matplotlib** — ambos documentados (secciones 14.1 y 17) pero **no implementados**.

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
3. **Todo el contenido actual es demostrativo (mock data), no real.** No hay modelos de base de datos, no hay `pandas`/`matplotlib`/`scikit-learn` instalados, no hay archivos de dataset reales, no existe `media/charts/`. Esto es coherente con el alcance de esta fase (documentar y preparar, no construir ni generar datos).
4. **El módulo Dataset ya está visualmente completo** según el esquema oficial (secciones 12.2/12.3): carga, estado vacío, 5 cards de resumen, columnas esperadas y vista previa. Su único pendiente real es de backend (Pandas + lógica de la sección 12.6), no de vista.
5. **El esquema del dataset oficial (10 columnas obligatorias + 7 opcionales) ya quedó definido y es el mismo que usa la plantilla de Dataset** (secciones 12.2/12.3) — listo para usarse como criterio de validación real en cuanto llegue el archivo externo.
6. **Ambos modelos (Regresión Lineal y Random Forest) son adecuados para el objetivo de negocio**: el primero aporta interpretabilidad y sirve de línea base; el segundo captura las relaciones no lineales típicas de la demanda gastronómica y aporta importancia de variables. La estrategia de selección automática por métricas es la correcta.
7. **La arquitectura de visualización queda especificada, no implementada:** Pandas para el procesamiento y Matplotlib para los 9 gráficos oficiales (sección 14.1), guardados como imágenes en `media/charts/` y mostrados con `<img>` en las vistas — no como gráficos interactivos en el navegador.
8. **El dataset oficial será entregado externamente** (archivo CSV/XLSX) y no se genera en este proyecto ni en este documento. La siguiente fase técnica debe: (a) recibir ese archivo, (b) construir el validador de estructura del módulo Dataset contra las tablas de las secciones 12.2/12.3 siguiendo la lógica de 12.6, (c) resolver la decisión pendiente de `franja_horaria` (sección 12) antes de tocar las plantillas de Predicciones, (d) implementar el entrenamiento real y la generación de gráficos (secciones 17 y 14.1), y (e) diseñar el motor de reglas de negocio (sección 11) como una capa de servicio independiente (ej. dentro de `machine_learning/services/` o un nuevo módulo de reglas).

---

## 23. Anexo — Validación específica solicitada

### 23.1 ¿El dataset actual cumple con el flujo del sistema?

**Parcialmente, y solo en estructura visual.** Tras el último ajuste, `templates/datasets/index.html` ya usa exactamente las 10 columnas obligatorias oficiales (sección 12.2) en su vista previa, y lista las 7 opcionales (sección 12.3) en la sección "Columnas esperadas". Sin embargo, sigue siendo una demostración: las filas de la vista previa están escritas directamente en el HTML, no existe un archivo real cargado (`media/` está vacío), no existe un modelo de base de datos que lo represente (`datasets/models.py` está vacío), y la validación real de encabezados (sección 12.6) **no está implementada** — el JavaScript actual solo revisa la extensión del archivo. En síntesis: **la vista ya está lista para recibir el archivo oficial; el backend que lo procese todavía no existe.**

### 23.2 ¿Qué columnas faltan?

Ya no hay columnas faltantes que definir — el esquema quedó cerrado en las secciones 12.2 (10 obligatorias) y 12.3 (7 opcionales), y la plantilla de Dataset ya lo refleja 1:1. Lo que falta es exclusivamente **backend**, no definición de columnas:

- Implementar con Pandas la lectura real de encabezados del archivo importado.
- Comparar esos encabezados contra las listas de 12.2/12.3 y aplicar la regla de rechazo/advertencia de la sección 12.6.
- Calcular, a partir de las columnas importadas, las variables derivadas de la sección 12.4 (`dia_semana`, `mes`, `total_venta`, `pedidos_dia_anterior`, etc.) — estas **no se piden en el archivo**, se calculan.

**Pendiente de reconciliación (no es una columna faltante, es una decisión de diseño):** el módulo Predicciones usa las etiquetas **Mañana/Tarde/Noche** para sus "turnos", mientras que `franja_horaria` en el dataset oficial usa **Desayuno/Almuerzo/Cena** (sección 12.2). Antes de conectar Predicciones al modelo real entrenado con el dataset oficial, hay que decidir cuál de las dos rutas de la sección 12 se sigue (renombrar los turnos de Predicciones, o mantener una capa de traducción entre ambas).

### 23.3 ¿Regresión Lineal y Random Forest cumplen el objetivo del negocio?

**Sí, en conjunto.** Ver detalle en sección 15. Regresión Lineal aporta interpretabilidad y una línea base contra la cual medir mejoras; Random Forest está mejor preparado para capturar las interacciones no lineales entre franja horaria, producto, canal y promociones que son típicas del negocio gastronómico. La estrategia de comparar ambos con MAE/RMSE/R² y elegir automáticamente el mejor (sección 15.3) es la correcta y ya está representada visualmente en Modelo Predictivo.

### 23.4 ¿Qué debe mostrarse en Modelo Predictivo?

Ver sección 8.4 y tabla 21.2. En síntesis, ya se muestra casi todo lo requerido a nivel de métricas y flujo (estado, R², comparación MAE/RMSE/R², variables e importancia en texto, mejor modelo, último entrenamiento). Faltan dos cosas, ambas ya especificadas pero no implementadas: **tiempo de entrenamiento** por modelo, y los **9 gráficos Matplotlib** de la sección 14.1 (demanda por franja, productos más vendidos, comparación MAE/RMSE/R², reales vs. predichos por modelo, importancia de variables y coeficientes), que deberán guardarse en `media/charts/` y mostrarse como imágenes en esta misma vista.

### 23.5 ¿Qué debe mostrarse en Predicciones?

Ver sección 8.5 y tabla 21.3. Ya se muestra casi todo lo requerido tras el ajuste de la fase anterior (formulario simple, promociones como opción avanzada, KPIs, resultado, turnos, gráfico por hora, productos top). Único faltante estructural: el **Centro de Recomendaciones Inteligentes categorizado** (Abastecimiento/Cocina/Personal/Operación) en lugar de la lista plana actual, y un indicador explícito de **nivel esperado de operación**.

### 23.6 ¿Qué elementos actuales deberían moverse o eliminarse de Predicciones?

**Ninguno pendiente.** El ajuste funcional de la fase anterior ya sacó de Predicciones todo lo que correspondía a configuración/evaluación del modelo (no hay MAE/RMSE/R², no hay comparación de modelos, no hay botón de entrenamiento) y todo lo que correspondía a datos crudos del histórico (no hay tabla de dataset). Lo único que resta es **enriquecer** (no mover) la sección de recomendaciones hacia el formato categorizado del Centro de Recomendaciones Inteligentes, ya que esa lógica pertenece naturalmente a Predicciones (depende de la consulta puntual), no a Dataset ni a Modelo Predictivo.

---

*Fin del documento. Este archivo no modifica diseño visual, estilos, colores, layout ni funcionalidades del sistema — es exclusivamente una especificación funcional y un reporte de validación.*
