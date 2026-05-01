# Resumen técnico del proyecto

- **`scripts/export_sheets_to_json.py`**: Script principal. Lee `SHEET_ID` y `GOOGLE_CREDENTIALS_JSON` del entorno,
  se conecta a Google Sheets con `gspread` y autenticación vía `google-auth`. Extrae fechas (col A) y cotizaciones (col G),
  aplica lógica de año incremental (base 2025) y convierte números europeos a float. Genera `data/portfolio.json`
  ordenado de más reciente a más antiguo. Lanza mensajes claros ante errores o datos sucios.
- **`.github/workflows/update_portfolio.yml`**: Workflow de GitHub Actions. Se dispara manualmente o por cron,
  instala las dependencias, ejecuta el script y realiza commit + push solo si el JSON cambió. Usa `GITHUB_TOKEN`
  para la autenticación.
- **`requirements.txt`**: Dependencias `gspread==5.10.0` y `google-auth==2.22.0` (estables y suficientes).
- **`README.md`**: Instrucciones completas para configurar secretos, ejecutar el workflow y entender el resultado.
- **Conexión entre archivos**: El workflow inyecta los secretos como variables de entorno que el script Python utiliza.
  El JSON generado se almacena en `data/` y el workflow lo commitea al repositorio. GitHub Pages sirve el archivo
  directamente vía `raw.githubusercontent.com`. La lógica de fechas asume que los datos están cronológicamente
  ordenados en la hoja (sin años) y los completa incrementalmente; después se reordena en el JSON final.
