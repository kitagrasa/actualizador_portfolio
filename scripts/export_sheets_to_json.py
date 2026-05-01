#!/usr/bin/env python3
"""
Exporta datos de Google Sheets a JSON para Portfolio Performance.

Lee la hoja de cálculo especificada, extrae fechas (columna A) y cotizaciones
(columna G), les asigna un año base (2025) y genera un archivo data/portfolio.json
con el formato requerido.
"""
import json
import os
import re
import sys
from datetime import date
from typing import List, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials


def cargar_credenciales(credentials_json: str) -> Credentials:
    """
    Crea un objeto Credentials a partir de la cadena JSON almacenada en la variable de entorno.
    """
    info = json.loads(credentials_json)
    return Credentials.from_service_account_info(info, scopes=[
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ])


def parsear_partes_fecha(cadena: str) -> Optional[Tuple[int, int]]:
    """
    Intenta extraer día y mes de una cadena de fecha.

    Se ignoran los años si existen. Acepta formatos como:
    - dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy
    - dd/mm/yy
    - dd/mm
    - d/m

    Retorna (dia, mes) si la conversión es exitosa, None en caso contrario.
    """
    # Limpiar espacios y reemplazar separadores comunes por '/'
    limpia = cadena.strip()
    # Reemplazar guiones, puntos y barras por '/'
    limpia = re.sub(r'[-./]', '/', limpia)
    partes = [p for p in limpia.split('/') if p.strip().isdigit()]

    if len(partes) < 2:
        return None

    # Si hay tres partes, tomamos las dos primeras como día y mes (formato dd/mm/aa)
    try:
        dia = int(partes[0])
        mes = int(partes[1])
    except ValueError:
        return None

    # Validación básica
    if not (1 <= dia <= 31 and 1 <= mes <= 12):
        return None

    return dia, mes


def convertir_cotizacion(cotizacion_str: str) -> Optional[float]:
    """
    Convierte una cadena con formato europeo (punto como miles, coma decimal)
    a float.

    Ejemplo: "33.830,002" -> 33830.002
    """
    if not cotizacion_str or cotizacion_str.strip() == '':
        return None

    try:
        # Eliminar todos los puntos (separadores de miles)
        sin_puntos = cotizacion_str.replace('.', '')
        # Reemplazar coma decimal por punto
        con_punto = sin_puntos.replace(',', '.')
        return float(con_punto)
    except ValueError:
        print(f"Error al convertir cotización: {cotizacion_str!r}")
        return None


def procesar_filas(datos: List[List[str]]) -> List[dict]:
    """
    Procesa las filas obtenidas de la hoja de cálculo (todas las celdas como str)
    y retorna una lista de diccionarios con las claves 'date' y 'close'.

    Asigna el año 2025 a la primera fecha y luego incrementalmente si el
    mes/día retrocede.
    """
    filas_procesadas = []
    anio_actual = 2025
    dia_anterior: Optional[int] = None
    mes_anterior: Optional[int] = None

    for num_fila, fila in enumerate(datos, start=1):
        # Ignorar filas vacías o sin fecha (columna A)
        if len(fila) < 7 or not fila[0].strip():
            continue

        fecha_str = fila[0]
        cotizacion_str = fila[6]  # Columna G (índice 6)

        partes = parsear_partes_fecha(fecha_str)
        if partes is None:
            print(f"Fila {num_fila} ignorada: no se pudo interpretar la fecha '{fecha_str}'")
            continue

        cotizacion = convertir_cotizacion(cotizacion_str)
        if cotizacion is None:
            print(f"Fila {num_fila} ignorada: cotización no válida '{cotizacion_str}'")
            continue

        dia, mes = partes

        # Lógica de incremento de año
        if dia_anterior is None:
            # Primera fila válida
            anio_actual = 2025
        else:
            # Si la fecha retrocede en el calendario (mes menor o mismo mes pero día menor)
            if mes < mes_anterior or (mes == mes_anterior and dia < dia_anterior):
                anio_actual += 1

        dia_anterior = dia
        mes_anterior = mes

        # Construir objeto date
        try:
            fecha_obj = date(anio_actual, mes, dia)
        except ValueError:
            print(f"Fila {num_fila} ignorada: fecha inválida {dia}/{mes}/{anio_actual}")
            continue

        filas_procesadas.append({
            "close": cotizacion,
            "date": fecha_obj.isoformat()
        })

    # Ordenar de más reciente a más antiguo
    filas_procesadas.sort(key=lambda x: x["date"], reverse=True)
    return filas_procesadas


def principal() -> None:
    """
    Punto de entrada: lee variables de entorno, conecta con Google Sheets y
    genera el JSON de salida.
    """
    sheet_id = os.getenv("SHEET_ID")
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if not sheet_id:
        sys.exit("ERROR: Debe definir la variable de entorno SHEET_ID")
    if not creds_json:
        sys.exit("ERROR: Debe definir la variable de entorno GOOGLE_CREDENTIALS_JSON")

    print("Conectando con Google Sheets...")
    creds = cargar_credenciales(creds_json)
    cliente = gspread.authorize(creds)

    try:
        hoja = cliente.open_by_key(sheet_id).sheet1
        print(f"Leyendo hoja: {hoja.title}")
    except Exception as e:
        sys.exit(f"Error al abrir la hoja: {e}")

    # Obtener todos los valores como cadenas (tal cual se ven en Sheets)
    datos = hoja.get_all_values()
    print(f"Filas leídas (incluyendo cabeceras): {len(datos)}")

    # Procesar datos
    portfolio = procesar_filas(datos)
    if not portfolio:
        sys.exit("No se encontraron filas válidas. Revisa la hoja de cálculo.")

    # Escribir archivo JSON
    ruta_salida = os.path.join("data", "portfolio.json")
    os.makedirs("data", exist_ok=True)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)

    print(f"Archivo generado: {ruta_salida} con {len(portfolio)} registros.")
    print("Primeros 3 registros del JSON:")
    for item in portfolio[:3]:
        print(f"  {item['date']}: {item['close']}")


if __name__ == "__main__":
    principal()
