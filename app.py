import os
import uuid
import traceback
from datetime import datetime
import requests
from io import BytesIO
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, url_for, send_from_directory, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from PIL import Image
import numpy as np
import tensorflow as tf
from werkzeug.utils import secure_filename

# --- 1. Konfigurasi Aplikasi & Ekstensi ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ganti-dengan-kunci-rahasia-yang-sangat-aman-dan-unik' 
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


# --- 2. Model Database ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    predictions = db.relationship('ImagePrediction', backref='author', lazy=True)

class ImagePrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(200), nullable=False)
    saved_filename = db.Column(db.String(200), nullable=False, unique=True)
    predicted_label = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=True)
    upload_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_path = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    feedback_label = db.Column(db.String(50), nullable=True)
    feedback_timestamp = db.Column(db.DateTime, nullable=True)
    feedback_status = db.Column(db.String(20), nullable=True) 

# --- 3. Decorator & Model Loader ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

MODEL_FILENAME = 'transfer_resnet50_with_report.h5'
MODEL_PATH = os.path.join('models', MODEL_FILENAME)
model = None
try:
    if os.path.exists(MODEL_PATH):
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        print(f"[*] Model '{MODEL_PATH}' berhasil dimuat.")
    else:
        print(f"[!] Error: File model '{MODEL_FILENAME}' tidak ditemukan.")
except Exception as e:
    print(f"[!] Error saat memuat model Keras: {e}")

IMG_HEIGHT, IMG_WIDTH = 224, 224
CLASS_NAMES = ['AiArtData', 'RealArt']

# --- 4. Fungsi-fungsi Helper ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def preprocess_image_for_tf(image_path):
    try:
        img = Image.open(image_path).convert('RGB')
        img = img.resize((IMG_WIDTH, IMG_HEIGHT))
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        return np.expand_dims(img_array, axis=0)
    except Exception: return None

def _process_and_predict(image_stream, original_filename):
    image_path_absolute = None
    try:
        file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename and allowed_file(original_filename) else 'jpg'
        saved_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Path absolut untuk menyimpan file di server
        upload_folder_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_folder_path, exist_ok=True)
        image_path_absolute = os.path.join(upload_folder_path, saved_filename)
        
        # PERBAIKAN: Path relatif yang disimpan ke database, menggunakan '/'
        image_path_relative = f"{app.config['UPLOAD_FOLDER']}/{saved_filename}"

        with open(image_path_absolute, 'wb') as f: f.write(image_stream.read())
        
        processed_data = preprocess_image_for_tf(image_path_absolute)
        if processed_data is None: return {"error": "Preprocessing gambar gagal."}
        if model is None: return {"error": "Model machine learning tidak berhasil dimuat."}

        prediction_prob = model.predict(processed_data)[0][0]
        predicted_label_str = CLASS_NAMES[1] if prediction_prob >= 0.5 else CLASS_NAMES[0]
        confidence_score = (prediction_prob * 100) if prediction_prob >= 0.5 else ((1 - prediction_prob) * 100)
        
        new_prediction = ImagePrediction(
            original_filename=str(original_filename),
            saved_filename=str(saved_filename),
            predicted_label=str(predicted_label_str),
            confidence=round(float(confidence_score), 2),
            image_path=image_path_relative # Simpan path relatif yang ramah URL
        )
        if current_user.is_authenticated:
            new_prediction.author = current_user
        db.session.add(new_prediction)
        db.session.commit()
        return {'prediction_id': new_prediction.id, 'label': predicted_label_str, 'confidence': round(confidence_score, 2), 'image_filename': saved_filename}
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        if image_path_absolute and os.path.exists(image_path_absolute):
            try: os.remove(image_path_absolute)
            except OSError: pass
        return {"error": f"Exception: {type(e).__name__}", "message": str(e)}

# --- 5. Rute-rute Aplikasi ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/upload')
def upload_page(): return render_template('upload.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    # ... Logika tidak berubah
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        username, email, password = request.form.get('username'), request.form.get('email'), request.form.get('password')
        if User.query.filter_by(username=username).first(): flash('Username sudah digunakan.', 'danger')
        elif User.query.filter_by(email=email).first(): flash('Email sudah terdaftar.', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Akun Anda telah berhasil dibuat! Silakan login.', 'success')
            return redirect(url_for('login'))
        return redirect(url_for('register'))
    return render_template('register.html', title='Register')

@app.route("/login", methods=['GET', 'POST'])
def login():
    # ... Logika tidak berubah
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        email, password = request.form.get('email'), request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            flash('Login Berhasil!', 'success')
            return redirect(next_page or url_for('index'))
        else: flash('Login Gagal. Periksa kembali email dan password.', 'danger')
    return render_template('login.html', title='Login')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/history")
@login_required
def history():
    predictions = ImagePrediction.query.filter_by(author=current_user).order_by(ImagePrediction.upload_timestamp.desc()).all()
    return render_template('history.html', title='Riwayat Analisis', predictions=predictions)

@app.route('/result/<int:prediction_id>')
def show_result(prediction_id):
    prediction = db.session.get(ImagePrediction, prediction_id)
    if not prediction: abort(404)
    return render_template('result.html', prediction=prediction)

@app.route('/detect', methods=['POST'])
def detect_image():
    # ... Logika tidak berubah
    if request.is_json:
        data = request.get_json()
        image_url = data.get('imageUrl')
        if not image_url: return jsonify({'error': 'URL gambar tidak ditemukan.'}), 400
        try:
            response = requests.get(image_url, stream=True, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            result = _process_and_predict(BytesIO(response.content), image_url.split('/')[-1].split('?')[0] or "image_from_url.jpg")
        except requests.exceptions.RequestException as e: return jsonify({'error': f'Gagal mengunduh dari URL: {e}'}), 400
    elif 'fileInput' in request.files:
        file = request.files['fileInput']
        if file.filename == '': return jsonify({'error': 'Tidak ada file yang dipilih.'}), 400
        if file and allowed_file(file.filename): result = _process_and_predict(file.stream, secure_filename(file.filename))
        else: return jsonify({'error': 'Jenis file tidak diizinkan.'}), 400
    else: return jsonify({'error': 'Request tidak valid.'}), 400
    if result and result.get('error'): return jsonify(result), 500
    elif result: return jsonify(result)
    else: return jsonify({'error': 'Terjadi kesalahan tak terduga.'}), 500

@app.route('/feedback', methods=['POST'])
@login_required
def handle_feedback():
    data = request.get_json()
    prediction_id, correct_label = data.get('prediction_id'), data.get('correct_label')
    if not all([prediction_id, correct_label]): return jsonify({'status': 'error', 'message': 'Data tidak lengkap.'}), 400
    prediction = db.session.get(ImagePrediction, prediction_id)
    if not prediction: return jsonify({'status': 'error', 'message': 'Prediksi tidak ditemukan.'}), 404
    if prediction.author != current_user: return jsonify({'status': 'error', 'message': 'Anda tidak berhak memberi feedback.'}), 403
    if prediction.feedback_label is not None: return jsonify({'status': 'error', 'message': 'Feedback sudah pernah diberikan.'}), 400
    try:
        prediction.feedback_label, prediction.feedback_timestamp, prediction.feedback_status = correct_label, datetime.utcnow(), 'pending'
        
        target_subfolder = 'is_ai' if correct_label == 'AiArtData' else 'is_real'
        # PERBAIKAN: Membuat path relatif baru yang ramah URL
        new_path_relative = f"feedback_review/{target_subfolder}/{prediction.saved_filename}"

        target_dir_absolute = os.path.join(app.root_path, 'feedback_review', target_subfolder)
        os.makedirs(target_dir_absolute, exist_ok=True)
        
        original_path_absolute = os.path.join(app.root_path, prediction.image_path)
        new_path_absolute = os.path.join(target_dir_absolute, prediction.saved_filename)

        if os.path.exists(original_path_absolute):
            os.rename(original_path_absolute, new_path_absolute)
            prediction.image_path = new_path_relative # Simpan path relatif yang baru
        else:
            print(f"[!] File untuk feedback tidak ditemukan: {original_path_absolute}")

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Terima kasih atas masukan Anda!'})
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'Terjadi kesalahan di server.'}), 500

# Rute Admin
@app.route('/admin/verify')
@login_required
@admin_required
def admin_verify_page():
    pending_feedback = ImagePrediction.query.filter_by(feedback_status='pending').order_by(ImagePrediction.feedback_timestamp.asc()).all()
    return render_template('admin_verify.html', title='Verifikasi Feedback', predictions=pending_feedback)

@app.route('/admin/process_feedback/<int:prediction_id>', methods=['POST'])
@login_required
@admin_required
def process_feedback(prediction_id):
    prediction = db.session.get(ImagePrediction, prediction_id)
    if not prediction: flash('Prediksi tidak ditemukan.', 'danger')
    else:
        action = request.form.get('action')
        if action == 'confirm': prediction.feedback_status = 'confirmed'
        elif action == 'reject': prediction.feedback_status = 'rejected'
        db.session.commit()
        flash(f'Feedback untuk {prediction.original_filename} telah di-{action}.', 'success' if action == 'confirm' else 'warning')
    return redirect(url_for('admin_verify_page'))

# --- REVISI: Rute penyaji gambar yang lebih aman dan sederhana ---
@app.route('/serve_image/<path:filepath>')
def serve_image(filepath):
    """Menyajikan file dari direktori root proyek dengan aman."""
    # Keamanan dasar: cegah traversal direktori ke atas
    if '..' in filepath or filepath.startswith('/'):
        abort(404)
    # send_from_directory sudah aman dan akan menggabungkan path dengan benar
    return send_from_directory(app.root_path, filepath)

# --- 6. Perintah Kustom & Inisialisasi Aplikasi ---
@app.cli.command("init-db")
def init_db_command():
    db.create_all()
    print("Database telah diinisialisasi.")

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
