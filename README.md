# Construct-Reports (Flask)

Aplicación web simple para reportabilidad de trabajos en construcción. Permite registrar:
- Área de trabajo
- Lugar de trabajo
- Especialidad
- Actividad
- Fotos del ANTES y DESPUÉS

Incluye un panel para supervisores con filtros y exportación a CSV.

## Requisitos
- Python 3.10+
- Pip

## Instalación
```bash
# 1) Crear entorno e instalar dependencias
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

pip install -r requirements.txt

# 2) Variables de entorno
copy .env.example .env   # en Windows (cmd)
# o: cp .env.example .env  # Linux/Mac
# Edita .env y cambia ADMIN_PASSWORD y SECRET_KEY

# 3) Ejecutar
python app.py
# Visita: http://127.0.0.1:5000
```

## Panel de supervisión
Abre: `http://127.0.0.1:5000/admin?key=TU_PASSWORD`
- Filtra por texto, área, especialidad.
- Exporta a CSV desde el botón "Exportar CSV".

## Despliegue (opciones rápidas)
- **Railway / Render / Fly.io / Deta Space**: sube el repo y configura una variable de entorno `PORT` (si el proveedor la exige) y `ADMIN_PASSWORD`.
- **Gunicorn** (Linux): `pip install gunicorn && gunicorn -w 2 -b 0.0.0.0:5000 app:app`

## Notas
- Las imágenes se guardan en la carpeta `uploads/`. En despliegues serverless considera usar un bucket (S3, GCS) cambiando la lógica de guardado.
- Tipos permitidos: PNG, JPG, JPEG, WEBP.
- Base de datos: SQLite (`database.db`). Para instancias multiusuario considera Postgres.

## Estructura
```
construct_report_app/
  app.py
  requirements.txt
  .env.example
  templates/
    base.html
    index.html
    dashboard.html
    detail.html
    auth.html
  static/
    style.css
  uploads/
```
