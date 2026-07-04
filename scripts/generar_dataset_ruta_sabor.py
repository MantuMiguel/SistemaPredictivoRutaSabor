from pathlib import Path
from datetime import datetime, timedelta
import random
import pandas as pd


random.seed(42)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CSV_PRINCIPAL = DATA_DIR / "ruta_del_sabor_dataset.csv"
XLSX_PRINCIPAL = DATA_DIR / "ruta_del_sabor_dataset.xlsx"
CSV_AGREGADO = DATA_DIR / "ruta_del_sabor_demanda_franja.csv"
README = DATA_DIR / "README_DATASET.md"


PRODUCTOS = [
    {"producto": "Hamburguesa Clásica", "categoria": "Hamburguesas", "precio_unitario": 12.00, "base": 18},
    {"producto": "Hamburguesa BBQ", "categoria": "Hamburguesas", "precio_unitario": 16.00, "base": 14},
    {"producto": "Cheeseburger", "categoria": "Hamburguesas", "precio_unitario": 14.00, "base": 13},
    {"producto": "Pollo Broaster", "categoria": "Pollos", "precio_unitario": 18.00, "base": 22},
    {"producto": "Alitas BBQ", "categoria": "Pollos", "precio_unitario": 20.00, "base": 15},
    {"producto": "Salchipapa Clásica", "categoria": "Salchipapas", "precio_unitario": 10.00, "base": 15},
    {"producto": "Salchipapa Especial", "categoria": "Salchipapas", "precio_unitario": 15.00, "base": 18},
    {"producto": "Pizza Personal", "categoria": "Pizzas", "precio_unitario": 13.00, "base": 12},
    {"producto": "Pizza Familiar", "categoria": "Pizzas", "precio_unitario": 32.00, "base": 10},
    {"producto": "Sándwich de Pollo", "categoria": "Sándwiches", "precio_unitario": 11.00, "base": 13},
    {"producto": "Gaseosa", "categoria": "Bebidas", "precio_unitario": 4.00, "base": 24},
    {"producto": "Jugo Natural", "categoria": "Bebidas", "precio_unitario": 6.00, "base": 15},
]

FRANJAS = {
    "Desayuno": {"hora_inicio": 7, "hora_fin": 11, "multiplicador": 0.65},
    "Almuerzo": {"hora_inicio": 12, "hora_fin": 16, "multiplicador": 1.55},
    "Cena": {"hora_inicio": 18, "hora_fin": 22, "multiplicador": 1.35},
}

PESOS_PRODUCTO_FRANJA = {
    "Desayuno": {
        "Sándwich de Pollo": 30,
        "Jugo Natural": 28,
        "Gaseosa": 20,
        "Cheeseburger": 12,
        "Hamburguesa Clásica": 10,
        "Salchipapa Clásica": 8,
        "Hamburguesa BBQ": 4,
        "Pollo Broaster": 3,
        "Alitas BBQ": 2,
        "Salchipapa Especial": 4,
        "Pizza Personal": 2,
        "Pizza Familiar": 1,
    },
    "Almuerzo": {
        "Pollo Broaster": 32,
        "Hamburguesa Clásica": 25,
        "Salchipapa Especial": 23,
        "Gaseosa": 28,
        "Salchipapa Clásica": 18,
        "Hamburguesa BBQ": 16,
        "Cheeseburger": 15,
        "Alitas BBQ": 15,
        "Pizza Personal": 12,
        "Sándwich de Pollo": 10,
        "Jugo Natural": 8,
        "Pizza Familiar": 7,
    },
    "Cena": {
        "Pizza Familiar": 28,
        "Hamburguesa BBQ": 24,
        "Pollo Broaster": 24,
        "Alitas BBQ": 23,
        "Salchipapa Especial": 25,
        "Gaseosa": 30,
        "Hamburguesa Clásica": 20,
        "Pizza Personal": 18,
        "Cheeseburger": 14,
        "Salchipapa Clásica": 14,
        "Jugo Natural": 7,
        "Sándwich de Pollo": 6,
    },
}

DIAS_SEMANA = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

MULT_DIA = {
    "Lunes": 0.85,
    "Martes": 0.90,
    "Miércoles": 0.95,
    "Jueves": 1.00,
    "Viernes": 1.15,
    "Sábado": 1.30,
    "Domingo": 1.20,
}

FERIADOS_MMDD = {
    "01-01",
    "05-01",
    "06-29",
    "07-28",
    "07-29",
    "10-08",
    "11-01",
    "12-08",
    "12-25",
}


def weighted_sample_without_replacement(items, weights, k):
    seleccionados = []
    pool_items = list(items)
    pool_weights = list(weights)

    for _ in range(min(k, len(pool_items))):
        elegido = random.choices(pool_items, weights=pool_weights, k=1)[0]
        idx = pool_items.index(elegido)
        seleccionados.append(elegido)
        pool_items.pop(idx)
        pool_weights.pop(idx)

    return seleccionados


def obtener_clima_y_temperatura(mes):
    if mes in [12, 1, 2, 3]:
        clima = random.choices(
            ["Soleado", "Nublado", "Lluvioso"],
            weights=[65, 25, 10],
            k=1
        )[0]
    elif mes in [6, 7, 8, 9]:
        clima = random.choices(
            ["Soleado", "Nublado", "Lluvioso"],
            weights=[20, 55, 25],
            k=1
        )[0]
    else:
        clima = random.choices(
            ["Soleado", "Nublado", "Lluvioso"],
            weights=[35, 50, 15],
            k=1
        )[0]

    if clima == "Soleado":
        temperatura = random.randint(23, 31)
    elif clima == "Nublado":
        temperatura = random.randint(18, 24)
    else:
        temperatura = random.randint(16, 22)

    lluvia = 1 if clima == "Lluvioso" else 0

    return clima, temperatura, lluvia


def generar_promocion(es_fin_semana, franja, producto):
    prob = 0.10

    if es_fin_semana:
        prob += 0.07

    if franja == "Cena":
        prob += 0.04

    if producto["categoria"] in ["Hamburguesas", "Pizzas", "Pollos"]:
        prob += 0.03

    promocion_activa = random.random() < prob

    if not promocion_activa:
        return "No", "Ninguna", 0

    tipo = random.choices(
        ["Combo", "2x1", "Descuento"],
        weights=[45, 25, 30],
        k=1
    )[0]

    descuento = random.choice([10, 15, 20, 25])

    return "Sí", tipo, descuento


def obtener_tiempo_preparacion(categoria):
    rangos = {
        "Bebidas": (2, 5),
        "Hamburguesas": (8, 14),
        "Pollos": (12, 20),
        "Salchipapas": (8, 15),
        "Pizzas": (15, 25),
        "Sándwiches": (6, 12),
    }

    minimo, maximo = rangos.get(categoria, (8, 15))
    return random.randint(minimo, maximo)


def obtener_personal_disponible(franja, es_fin_semana, es_feriado):
    if franja == "Desayuno":
        base = random.randint(2, 4)
    elif franja == "Almuerzo":
        base = random.randint(4, 7)
    else:
        base = random.randint(4, 8)

    if es_fin_semana:
        base += random.choice([0, 1])

    if es_feriado:
        base += random.choice([0, 1])

    return base


def obtener_porcentaje_delivery(franja, lluvia, es_fin_semana, promocion_activa):
    if franja == "Desayuno":
        base = random.randint(10, 25)
    elif franja == "Almuerzo":
        base = random.randint(25, 45)
    else:
        base = random.randint(40, 65)

    if lluvia:
        base += random.randint(10, 20)

    if es_fin_semana:
        base += random.randint(4, 10)

    if promocion_activa == "Sí":
        base += random.randint(2, 8)

    return max(5, min(base, 90))


def obtener_canal_venta(franja, porcentaje_delivery, lluvia):
    peso_delivery = porcentaje_delivery
    peso_web = porcentaje_delivery * 0.45
    peso_presencial = max(10, 100 - porcentaje_delivery)

    if franja == "Desayuno":
        peso_presencial += 30
        peso_web *= 0.5

    if franja == "Cena":
        peso_delivery += 15
        peso_web += 10

    if lluvia:
        peso_delivery += 20
        peso_presencial *= 0.7

    return random.choices(
        ["Presencial", "Delivery", "Web"],
        weights=[peso_presencial, peso_delivery, peso_web],
        k=1
    )[0]


def obtener_multiplicador_promocion(tipo_promocion):
    if tipo_promocion == "Combo":
        return 1.18
    if tipo_promocion == "2x1":
        return 1.30
    if tipo_promocion == "Descuento":
        return 1.15
    return 1.00


def obtener_multiplicador_mes(mes):
    if mes in [1, 2, 7, 12]:
        return 1.08
    if mes in [3, 4, 8, 11]:
        return 1.03
    return 1.00


def calcular_cantidad_vendida(producto, franja, dia_semana, es_feriado, clima, tipo_promocion, mes):
    base = producto["base"]
    mult_franja = FRANJAS[franja]["multiplicador"]
    mult_dia = MULT_DIA[dia_semana]
    mult_feriado = 1.18 if es_feriado else 1.00
    mult_promo = obtener_multiplicador_promocion(tipo_promocion)
    mult_mes = obtener_multiplicador_mes(mes)

    if clima == "Lluvioso":
        mult_clima = 1.06
    elif clima == "Soleado":
        mult_clima = 1.02
    else:
        mult_clima = 0.98

    ruido = random.normalvariate(1.0, 0.18)

    cantidad = base * mult_franja * mult_dia * mult_feriado * mult_promo * mult_mes * mult_clima * ruido

    return max(1, int(round(cantidad)))


def calcular_nivel_demanda(total):
    if total <= 79:
        return "Baja demanda"
    if total <= 119:
        return "Demanda moderada"
    if total <= 179:
        return "Alta demanda"
    return "Demanda crítica"


def main():
    registros = []

    fecha_inicio = datetime(2024, 1, 1)
    fecha_fin = datetime(2025, 6, 30)

    fecha_actual = fecha_inicio

    while fecha_actual <= fecha_fin:
        dia_semana = DIAS_SEMANA[fecha_actual.weekday()]
        mes = fecha_actual.month
        anio = fecha_actual.year
        es_fin_semana = 1 if dia_semana in ["Sábado", "Domingo"] else 0
        es_feriado = 1 if fecha_actual.strftime("%m-%d") in FERIADOS_MMDD else 0

        clima, temperatura, lluvia = obtener_clima_y_temperatura(mes)

        for franja, config_franja in FRANJAS.items():
            cantidad_productos = random.choices(
                [3, 4, 5, 6],
                weights=[15, 35, 35, 15],
                k=1
            )[0]

            pesos_franja = PESOS_PRODUCTO_FRANJA[franja]
            productos_dict = {p["producto"]: p for p in PRODUCTOS}

            nombres_productos = list(pesos_franja.keys())
            pesos = list(pesos_franja.values())

            productos_seleccionados = weighted_sample_without_replacement(
                nombres_productos,
                pesos,
                cantidad_productos
            )

            personal_disponible = obtener_personal_disponible(
                franja,
                es_fin_semana,
                es_feriado
            )

            for nombre_producto in productos_seleccionados:
                producto = productos_dict[nombre_producto]

                promocion_activa, tipo_promocion, descuento_pct = generar_promocion(
                    es_fin_semana,
                    franja,
                    producto
                )

                porcentaje_delivery = obtener_porcentaje_delivery(
                    franja,
                    lluvia,
                    es_fin_semana,
                    promocion_activa
                )

                canal_venta = obtener_canal_venta(
                    franja,
                    porcentaje_delivery,
                    lluvia
                )

                cantidad_vendida = calcular_cantidad_vendida(
                    producto,
                    franja,
                    dia_semana,
                    es_feriado,
                    clima,
                    tipo_promocion,
                    mes
                )

                precio_unitario = producto["precio_unitario"]
                total_venta = cantidad_vendida * precio_unitario * (1 - descuento_pct / 100)
                total_venta = round(total_venta, 2)

                tiempo_preparacion = obtener_tiempo_preparacion(producto["categoria"])

                if producto["categoria"] == "Bebidas":
                    stock_disponible = cantidad_vendida + random.randint(15, 60)
                else:
                    stock_disponible = cantidad_vendida + random.randint(5, 35)

                registros.append({
                    "fecha": fecha_actual.strftime("%Y-%m-%d"),
                    "dia_semana": dia_semana,
                    "mes": mes,
                    "anio": anio,
                    "es_fin_semana": es_fin_semana,
                    "es_feriado": es_feriado,
                    "franja_horaria": franja,
                    "hora_inicio": config_franja["hora_inicio"],
                    "hora_fin": config_franja["hora_fin"],
                    "producto": producto["producto"],
                    "categoria": producto["categoria"],
                    "cantidad_vendida": cantidad_vendida,
                    "precio_unitario": precio_unitario,
                    "total_venta": total_venta,
                    "canal_venta": canal_venta,
                    "promocion_activa": promocion_activa,
                    "tipo_promocion": tipo_promocion,
                    "descuento_pct": descuento_pct,
                    "clima": clima,
                    "temperatura": temperatura,
                    "lluvia": lluvia,
                    "personal_disponible": personal_disponible,
                    "tiempo_preparacion_min": tiempo_preparacion,
                    "stock_disponible": stock_disponible,
                    "porcentaje_delivery": porcentaje_delivery,
                })

        fecha_actual += timedelta(days=1)

    df = pd.DataFrame(registros)

    df_agregado = (
        df.groupby([
            "fecha",
            "dia_semana",
            "mes",
            "anio",
            "es_fin_semana",
            "es_feriado",
            "franja_horaria",
            "hora_inicio",
            "hora_fin",
        ])
        .agg(
            total_pedidos_franja=("cantidad_vendida", "sum"),
            total_venta_franja=("total_venta", "sum"),
            clima=("clima", "first"),
            temperatura=("temperatura", "mean"),
            lluvia=("lluvia", "first"),
            porcentaje_delivery=("porcentaje_delivery", "mean"),
            personal_disponible=("personal_disponible", "max"),
        )
        .reset_index()
    )

    productos_lideres = (
        df.sort_values(["fecha", "franja_horaria", "cantidad_vendida"], ascending=[True, True, False])
        .groupby(["fecha", "franja_horaria"])
        .first()
        .reset_index()[["fecha", "franja_horaria", "producto", "categoria"]]
        .rename(columns={
            "producto": "producto_lider",
            "categoria": "categoria_lider"
        })
    )

    canal_predominante = (
        df.groupby(["fecha", "franja_horaria"])["canal_venta"]
        .agg(lambda x: x.value_counts().index[0])
        .reset_index()
        .rename(columns={"canal_venta": "canal_predominante"})
    )

    promocion_franja = (
        df.groupby(["fecha", "franja_horaria"])["promocion_activa"]
        .agg(lambda x: "Sí" if (x == "Sí").any() else "No")
        .reset_index()
    )

    df_agregado = df_agregado.merge(productos_lideres, on=["fecha", "franja_horaria"], how="left")
    df_agregado = df_agregado.merge(canal_predominante, on=["fecha", "franja_horaria"], how="left")
    df_agregado = df_agregado.merge(promocion_franja, on=["fecha", "franja_horaria"], how="left")

    df_agregado["total_venta_franja"] = df_agregado["total_venta_franja"].round(2)
    df_agregado["temperatura"] = df_agregado["temperatura"].round(1)
    df_agregado["porcentaje_delivery"] = df_agregado["porcentaje_delivery"].round(1)
    df_agregado["nivel_demanda"] = df_agregado["total_pedidos_franja"].apply(calcular_nivel_demanda)

    columnas_agregado = [
        "fecha",
        "dia_semana",
        "mes",
        "anio",
        "es_fin_semana",
        "es_feriado",
        "franja_horaria",
        "hora_inicio",
        "hora_fin",
        "total_pedidos_franja",
        "total_venta_franja",
        "producto_lider",
        "categoria_lider",
        "canal_predominante",
        "promocion_activa",
        "clima",
        "temperatura",
        "lluvia",
        "porcentaje_delivery",
        "personal_disponible",
        "nivel_demanda",
    ]

    df_agregado = df_agregado[columnas_agregado]

    df.to_csv(CSV_PRINCIPAL, index=False, encoding="utf-8-sig")
    df_agregado.to_csv(CSV_AGREGADO, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(XLSX_PRINCIPAL, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="dataset_producto")
        df_agregado.to_excel(writer, index=False, sheet_name="demanda_franja")

        workbook = writer.book

        for sheet_name in workbook.sheetnames:
            ws = workbook[sheet_name]
            ws.freeze_panes = "A2"

            for column_cells in ws.columns:
                max_length = 0
                col_letter = column_cells[0].column_letter

                for cell in column_cells:
                    value = str(cell.value) if cell.value is not None else ""
                    max_length = max(max_length, len(value))

                ws.column_dimensions[col_letter].width = min(max_length + 2, 35)

    readme_text = f"""# Dataset Sintético - Ruta del Sabor

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

- Registros dataset principal: {len(df)}
- Registros dataset agregado por franja: {len(df_agregado)}

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
"""

    README.write_text(readme_text, encoding="utf-8")

    print("Dataset oficial generado correctamente.")
    print(f"CSV principal: {CSV_PRINCIPAL}")
    print(f"XLSX principal: {XLSX_PRINCIPAL}")
    print(f"CSV agregado: {CSV_AGREGADO}")
    print(f"README: {README}")
    print(f"Registros dataset principal: {len(df)}")
    print(f"Registros dataset agregado: {len(df_agregado)}")
    print(f"Periodo histórico: {df['fecha'].min()} al {df['fecha'].max()}")


if __name__ == "__main__":
    main()