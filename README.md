# actualizador_portfolio
Actualiza la rentabilidad de mi Portfolio


# Portfolio Performance JSON Generator

Genera automáticamente un archivo `data/portfolio.json` a partir de una hoja de cálculo
de Google Sheets, y lo publica en GitHub Pages a través de `raw.githubusercontent.com`.

## Requisitos previos

- Cuenta de Google con acceso a Google Sheets.
- Repositorio público en GitHub.
- Python 3.10+ (solo para desarrollo local).

## Configuración paso a paso

### 1. Crear credenciales de Google Sheets

1. Ve a [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un proyecto (o selecciona uno existente).
3. Habilita la API de **Google Sheets**.
4. Crea una **cuenta de servicio** en "IAM y administración" > "Cuentas de servicio".
5. Genera una clave JSON y descárgala.
6. **Comparte tu hoja de cálculo** con el correo de la cuenta de servicio (aparece en el JSON) como **lector**.

### 2. Configurar secretos en GitHub

En tu repositorio, ve a **Settings > Secrets and variables > Actions** y crea estos secretos:

- `GOOGLE_CREDENTIALS_JSON`: Pega aquí todo el contenido del archivo JSON de la cuenta de servicio.
- `SHEET_ID`: El ID de tu hoja de cálculo (lo obtienes de la URL: `https://docs.google.com/spreadsheets/d/<ID>/edit`).

El workflow usará automáticamente `GITHUB_TOKEN` para hacer push, no necesitas secretos adicionales.

### 3. Estructura de la hoja de cálculo

- **Columna A**: fechas. Se aceptan dos formatos:
  - Numérico con separadores: `01/05`, `02/05/2025`, `15-03`, `31.12.25`.
  - Texto con mes abreviado o completo en español: `1  oct`, `15 ene`, `31 diciembre`.
  El año es opcional; el script asigna 2025 a la primera fecha y lo incrementa automáticamente cuando el mes/día retrocede.
- **Columna G**: cotizaciones con formato europeo (`.` para miles, `,` como decimal). Ejemplo: `33.830,002`.

Las filas sin fecha o con datos inválidos se ignoran con un aviso en los logs.

### 4. Probar el workflow

- Ve a la pestaña **Actions** de tu repositorio.
- Selecciona el workflow **Update Portfolio JSON**.
- Haz clic en **Run workflow** para ejecutarlo manualmente.

También se ejecutará según la programación definida en `update_portfolio.yml` (puedes cambiarla).

### 5. Formato del JSON generado

El archivo `data/portfolio.json` tendrá este aspecto:
```json
[
  { "close": 33.830002, "date": "2026-05-01" },
  { "close": 33.5625,   "date": "2026-04-30" }
]
´´´json
close: número decimal (float).
date: formato ISO 8601 (YYYY-MM-DD).
Los datos están ordenados de más reciente a más antiguo.

Desarrollo local
Clona el repositorio.
Crea un entorno virtual e instala las dependencias: pip install -r requirements.txt.
Define las variables de entorno SHEET_ID y GOOGLE_CREDENTIALS_JSON.
Ejecuta: python scripts/export_sheets_to_json.py.

Notas de seguridad
Ningún dato sensible aparece en el código.
Las credenciales se inyectan como secretos en el entorno de ejecución.
El token de GitHub para el push se gestiona automáticamente (GITHUB_TOKEN).

# Resumen técnico del proyecto (CONTEXT)
Estructura del proyecto
scripts/export_sheets_to_json.py
Script principal. Lee las variables de entorno SHEET_ID y GOOGLE_CREDENTIALS_JSON.
Se conecta a Google Sheets usando gspread y autenticación con google-auth.
Extrae fechas (columna A) y cotizaciones (columna G).
Soporta formatos de fecha numéricos (dd/mm/yyyy) y textuales en español (1 oct, 31 ene) mediante un mapeo de meses.
Aplica lógica de año incremental (base 2025) y convierte valores europeos a float.
Genera data/portfolio.json ordenado de más reciente a más antiguo.
Maneja errores con mensajes claros y omite filas inválidas.

.github/workflows/update_portfolio.yml
Workflow de GitHub Actions. Se ejecuta manualmente (workflow_dispatch) y por cron diario.
Usa actions/checkout@v5 y actions/setup-python@v6, compatibles con Node.js 24.
Instala dependencias, ejecuta el script Python y hace commit + push solo si data/portfolio.json cambió.
Usa GITHUB_TOKEN automático para el push (permiso contents: write).

requirements.txt
Dependencias estables: gspread==5.10.0, google-auth==2.22.0.

Flujo de datos
GitHub Actions inyecta los secretos SHEET_ID y GOOGLE_CREDENTIALS_JSON como variables de entorno.
El script Python se autentica con la cuenta de servicio, abre la hoja y procesa todas las filas.
Convierte los datos a objetos JSON (close: float, date: ISO 8601) y los guarda en data/portfolio.json.
El workflow commitea el archivo si hay cambios, dejándolo disponible vía raw.githubusercontent.com.

Dependencias principales
gspread: interfaz sencilla para Google Sheets.
google-auth: manejo de credenciales de cuenta de servicio.
GitHub Actions: para automatización y despliegue continuo.

Notas de seguridad (técnicas)
Las credenciales nunca se exponen en el código ni en el repositorio.
Todos los valores sensibles se pasan como secretos de entorno.
El token de publicación es gestionado por GitHub (GITHUB_TOKEN) y solo tiene alcance dentro del repositorio.
