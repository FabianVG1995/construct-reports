from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload settings
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

db = SQLAlchemy(app)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area_trabajo = db.Column(db.String(120), nullable=False)
    lugar_trabajo = db.Column(db.String(200), nullable=False)
    especialidad = db.Column(db.String(120), nullable=False)
    actividad = db.Column(db.Text, nullable=False)
    foto_antes = db.Column(db.String(300))
    foto_despues = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_row(self):
        return {
            "id": self.id,
            "fecha": self.created_at.strftime('%Y-%m-%d %H:%M'),
            "area_trabajo": self.area_trabajo,
            "lugar_trabajo": self.lugar_trabajo,
            "especialidad": self.especialidad,
            "actividad": self.actividad,
            "foto_antes": self.foto_antes or "",
            "foto_despues": self.foto_despues or "",
        }

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    area = request.form.get('area_trabajo', '').strip()
    lugar = request.form.get('lugar_trabajo', '').strip()
    especialidad = request.form.get('especialidad', '').strip()
    actividad = request.form.get('actividad', '').strip()

    if not all([area, lugar, especialidad, actividad]):
        flash('Por favor completa todos los campos obligatorios.', 'danger')
        return redirect(url_for('index'))

    # Manejo de fotos
    foto_antes_path = None
    foto_despues_path = None

    for field in ['foto_antes', 'foto_despues']:
        file = request.files.get(field)
        if file and file.filename and allowed_file(file.filename):
            filename = datetime.utcnow().strftime('%Y%m%d%H%M%S_') + secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            if field == 'foto_antes':
                foto_antes_path = url_for('uploaded_file', filename=filename)
            else:
                foto_despues_path = url_for('uploaded_file', filename=filename)
        elif file and file.filename:
            flash('Formato de imagen no permitido. Usa PNG, JPG, JPEG o WEBP.', 'warning')

    report = Report(
        area_trabajo=area,
        lugar_trabajo=lugar,
        especialidad=especialidad,
        actividad=actividad,
        foto_antes=foto_antes_path,
        foto_despues=foto_despues_path
    )
    db.session.add(report)
    db.session.commit()
    flash('¡Reporte guardado correctamente!', 'success')
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET'])
def admin():
    # Autenticación simple por query param ?key=
    key = request.args.get('key', '')
    if key != ADMIN_PASSWORD:
        return render_template('auth.html'), 401

    q = request.args.get('q', '').strip().lower()
    area = request.args.get('area', '').strip().lower()
    especialidad = request.args.get('esp', '').strip().lower()

    reports = Report.query.order_by(Report.created_at.desc()).all()

    def match(r):
        ok = True
        if q:
            ok = q in (r.actividad or '').lower() or q in (r.lugar_trabajo or '').lower()
        if ok and area:
            ok = area in (r.area_trabajo or '').lower()
        if ok and especialidad:
            ok = especialidad in (r.especialidad or '').lower()
        return ok

    filtered = [r for r in reports if match(r)]
    return render_template('dashboard.html', reports=filtered, key=key, q=q, area=area, esp=especialidad)

@app.route('/report/<int:rid>', methods=['GET'])
def report_detail(rid):
    key = request.args.get('key', '')
    if key != ADMIN_PASSWORD:
        return render_template('auth.html'), 401
    r = Report.query.get_or_404(rid)
    return render_template('detail.html', r=r, key=key)

@app.route('/export.csv', methods=['GET'])
def export_csv():
    key = request.args.get('key', '')
    if key != ADMIN_PASSWORD:
        return render_template('auth.html'), 401
    reports = Report.query.order_by(Report.created_at.desc()).all()
    # CSV manual
    import csv
    from io import StringIO
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['id','fecha','area_trabajo','lugar_trabajo','especialidad','actividad','foto_antes','foto_despues'])
    for r in reports:
        row = r.to_row()
        writer.writerow([row['id'],row['fecha'],row['area_trabajo'],row['lugar_trabajo'],row['especialidad'],row['actividad'],row['foto_antes'],row['foto_despues']])
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=reportes.csv'})


# Exportar a Excel
@app.route('/export.xlsx', methods=['GET'])
def export_xlsx():
    key = request.args.get('key', '')
    if key != ADMIN_PASSWORD:
        return render_template('auth.html'), 401

    import io
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Reportes"

    headers = ['ID','Fecha','Área','Lugar','Especialidad','Actividad','Foto Antes','Foto Después']
    ws.append(headers)

    reports = Report.query.order_by(Report.created_at.desc()).all()
    for r in reports:
        ws.append([
            r.id,
            r.created_at.strftime('%Y-%m-%d %H:%M'),
            r.area_trabajo,
            r.lugar_trabajo,
            r.especialidad,
            r.actividad,
            r.foto_antes or "",
            r.foto_despues or "",
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition":"attachment;filename=reportes.xlsx"}
    )


# Exportar a PDF

@app.route('/export.pdf', methods=['GET'])
def export_pdf():
    key = request.args.get('key', '')
    if key != ADMIN_PASSWORD:
        return render_template('auth.html'), 401

    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    import io, os

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()

    reports = Report.query.order_by(Report.created_at.desc()).all()
    data = [["ID","Fecha","Área","Lugar","Especialidad","Actividad","Antes","Después"]]

    for r in reports:
        actividad = (r.actividad[:60] + "...") if len(r.actividad or "") > 60 else (r.actividad or "")
        row = [
            r.id,
            r.created_at.strftime('%Y-%m-%d %H:%M'),
            r.area_trabajo,
            r.lugar_trabajo,
            r.especialidad,
            actividad
        ]

        # Thumbnail images if exist
        def make_img(path_url):
            if not path_url:
                return ""
            try:
                # path_url like /uploads/filename.jpg
                fname = path_url.split('/')[-1]
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                if os.path.exists(full_path):
                    return Image(full_path, width=60, height=45)
            except:
                pass
            return ""

        row.append(make_img(r.foto_antes))
        row.append(make_img(r.foto_despues))
        data.append(row)

    table = Table(data, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#0d6efd")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke, colors.lightgrey]),
        ('FONTSIZE',(0,0),(-1,-1),7),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))

    elements = [Paragraph("Reporte de Trabajos", styles['Title']), Spacer(1,8), table]
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition":"attachment;filename=reportes.pdf"}
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
