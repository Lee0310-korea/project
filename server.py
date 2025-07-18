from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import base64
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

USERS_FILE = 'users.json'

# 🔴 1. users.json 읽기
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 파일 없으면 기본 admin 계정 생성 후 저장
        users = {'admin': generate_password_hash('1234')}
        save_users(users)
        return users

# 🔴 2. users.json 저장하기
def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ✅ 3. users 딕셔너리 초기화
users = load_users()

# 업로드 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('project.html', username=session['user_id'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username], password):
            session['user_id'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='아이디 또는 비밀번호가 틀렸습니다.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return render_template('register.html', error='이미 존재하는 아이디입니다.')
        # 비밀번호 해시 후 저장
        users[username] = generate_password_hash(password)
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        return jsonify({'status': 'fail', 'message': '로그인 필요'})
    user_id = session['user_id']

    if 'file' not in request.files:
        return jsonify({'status': 'fail', 'message': '파일이 없습니다.'})
    
    file = request.files['file']
    date = request.form.get('date')
    photo_type = request.form.get('photo_type', 'face')

    if not date:
        return jsonify({'status': 'fail', 'message': '날짜가 없습니다.'})

    save_folder = os.path.join(app.config['UPLOAD_FOLDER'], user_id, date, photo_type)
    os.makedirs(save_folder, exist_ok=True)

    filepath = os.path.join(save_folder, file.filename)
    file.save(filepath)

    return redirect(url_for('photos_page', date=date))

@app.route('/delete_photo', methods=['POST'])
def delete_photo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']

    date = request.form.get('date')
    filename = request.form.get('filename')
    photo_type = request.form.get('photo_type', 'face')

    if not date or not filename:
        return redirect(url_for('index'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_id, date, photo_type, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        os.remove(file_path)

    return redirect(url_for('photos_page', date=date))

@app.route('/photos_page/<date>')
def photos_page(date):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']

    categories = ['face', 'real']
    photos = []

    for category in categories:
        date_folder = os.path.join(app.config['UPLOAD_FOLDER'], user_id, date, category)
        if os.path.exists(date_folder):
            files = os.listdir(date_folder)
            for filename in files:
                filepath = os.path.join(date_folder, filename)
                if os.path.isfile(filepath):
                    with open(filepath, 'rb') as f:
                        data = f.read()
                        encoded = base64.b64encode(data).decode('utf-8')
                        photos.append({
                            'filename': filename,
                            'data': f"data:image/jpeg;base64,{encoded}",
                            'photo_type': category
                        })

    return render_template('photos.html', date=date, photos=photos, username=user_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
