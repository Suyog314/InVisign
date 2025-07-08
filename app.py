
from flask import Flask, render_template, request, send_file
import os
from utils.pdf_utils import sign_pdf, verify_pdf
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'signed_pdfs'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

# DB model
class SignedPDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    signature = db.Column(db.String(256), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/sign', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        file = request.files['pdf']
        unique_name = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(filepath)

        sig, ts, new_path = sign_pdf(filepath)

        record = SignedPDF(filename=unique_name, signature=sig, timestamp=ts)
        db.session.add(record)
        db.session.commit()

        return f'''
        ✅ PDF signed and saved.<br>
        Signature: {sig[:10]}...<br>
        <a href="/download/{os.path.basename(new_path)}" target="_blank">Download signed PDF</a>
        '''
    return render_template('sign.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        file = request.files['pdf']
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        sig = verify_pdf(filepath)
        if not sig:
            return "❌ Invalid or unsigned document."

        record = SignedPDF.query.filter_by(signature=sig).first()
        if record:
            return f"✅ Verified! Signed on {record.timestamp}."
        else:
            return "❌ Invalid or unsigned document."
    return render_template('verify.html')

@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(path):
        return "❌ File not found.", 404
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    os.makedirs('signed_pdfs', exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
