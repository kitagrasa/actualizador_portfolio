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

- **Columna A**: fechas (p. ej. `01/05`, `02/05/2025`). El año es opcional; el script asigna 2025 a la primera fecha y lo incrementa automáticamente cuando el mes/día retrocede.
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
