#!/usr/bin/env python3
"""
Exporta datos de Google Sheets a JSON para Portfolio Performance.

Lee la hoja de cálculo especificada, extrae fechas (columna A) y cotizaciones
(columna G), les asigna un año base (2025) y genera un archivo data/portfolio.json
con el formato requerido.

Soporta fechas en formato numérico (dd/mm, dd/mm/yyyy, etc.) y en texto
con mes abreviado en español (por ejemplo "1  oct", "15 ene").
"""
import json
import os
import re
import sys
from datetime import date
from typing import Dict, List, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials

# Mapeo de nombres de mes (español) a número
MES_ES: Dict[str, int] = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11,
    "diciembre": 12,
    # Abreviaturas comunes
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12,
}

def cargar_credenciales(credentials_json: str) -> Credentials:
    """Crea un objeto Credentials a partir de la cadena JSON de la variable de entorno."""
    info = json.loads(credentials_json)
    return Credentials.from_service_account_info(info, scopes=[
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ])


def _extraer_dia_mes_texto(cadena: str) -> Optional[Tuple[int, int]]:
    """
    Intenta parsear un formato como '1  oct', '31  dic', etc.
    Busca un número (día) y una palabra que represente el mes.
    """
    patron = re.compile(r"(\d{1,2})\s+([a-zA-Záéíóúñ]+)", re.IGNORECASE)
    match = patron.search(cadena.strip())
    if not match:
        return None

    dia = int(match.group(1))
    nombre_mes = match.group(2).lower()
    mes = MES_ES.get(nombre_mes)
    if mes is None:
        return None
    if not (1 <= dia <= 31 and 1 <= mes <= 12):
        return None
    return dia, mes


def _extraer_dia_mes_numerico(cadena: str) -> Optional[Tuple[int, int]]:
    """Intenta parsear formatos numéricos: dd/mm, dd/mm/yy, dd-mm-yyyy, etc."""
    limpia = cadena.strip()
    # Reemplazar separadores comunes por '/'
    limpia = re.sub(r'[-./]', '/', limpia)
    partes = [p for p in limpia.split('/') if p.strip().isdigit()]

    if len(partes) < 2:
        return None

    try:
        dia = int(partes[0])
        mes = int(partes[1])
    except ValueError:
        return None

    if not (1 <= dia <= 31 and 1 <= mes <= 12):
        return None

    return dia, mes


def parsear_partes_fecha(cadena: str) -> Optional[Tuple[int, int]]:
    """
    Intenta extraer día y mes de una cadena de fecha.
    Soporta:
      - Numérico: "15/03", "15-03-2025", "15.03.25"
      - Textual en español: "1  oct", "31  dic", "15 ene"
    Retorna (dia, mes) o None.
    """
    # Primero intentar formato textual (día seguido de palabra)
    resultado = _extraer_dia_mes_texto(cadena)
    if resultado is not None:
        return resultado

    # Si no, intentar el numérico
    resultado = _extraer_dia_mes_numerico(cadena)
    if resultado is not None:
        return resultado

    return None


def convertir_cotizacion(cotizacion_str: str) -> Optional[float]:
    """
    Convierte una cadena con formato europeo (punto como miles, coma decimal) a float.
    Ejemplo: "33.830,002" -> 33830.002
    """
    if not cotizacion_str or cotizacion_str.strip() == '':
        return None

    try:
        sin_puntos = cotizacion_str.replace('.', '')
        con_punto = sin_puntos.replace(',', '.')
        return float(con_punto)
    except ValueError:
        print(f"Error al convertir cotización: {cotizacion_str!r}")
        return None


def procesar_filas(datos: List[List[str]]) -> List[dict]:
    """
    Procesa las filas y retorna una lista de diccionarios con 'date' y 'close'.
    Asigna el año 2025 a la primera fecha y luego incrementalmente si el
    mes/día retrocede.
    """
    filas_procesadas = []
    anio_actual = 2025
    dia_anterior: Optional[int] = None
    mes_anterior: Optional[int] = None

    for num_fila, fila in enumerate(datos, start=1):
        # Solo procesar si hay al menos 7 columnas (A a G)
        if len(fila) < 7 or not fila[0].strip():
            continue

        fecha_str = fila[0].strip()
        cotizacion_str = fila[6].strip()  # Columna G

        # Saltar fila de cabecera si contiene texto típico
        if num_fila == 1 and re.search(r'(fecha|date)', fecha_str, re.IGNORECASE):
            print(f"Fila {num_fila} ignorada: probable cabecera '{fecha_str}'")
            continue

        partes = parsear_partes_fecha(fecha_str)
        if partes is None:
            print(f"Fila {num_fila} ignorada: fecha no reconocida '{fecha_str}'")
            continue

        cotizacion = convertir_cotizacion(cotizacion_str)
        if cotizacion is None:
            print(f"Fila {num_fila} ignorada: cotización no válida '{cotizacion_str}'")
            continue

        dia, mes = partes

        # Lógica de incremento de año
        if dia_anterior is None:
            anio_actual = 2025
        else:
            if mes < mes_anterior or (mes == mes_anterior and dia < dia_anterior):
                anio_actual += 1

        dia_anterior = dia
        mes_anterior = mes

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
    """Punto de entrada: lee variables de entorno, conecta con Sheets y genera JSON."""
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

    datos = hoja.get_all_values()
    print(f"Filas leídas (incluyendo cabeceras): {len(datos)}")

    portfolio = procesar_filas(datos)
    if not portfolio:
        sys.exit("No se encontraron filas válidas. Revisa la hoja de cálculo.")

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
