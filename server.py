from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import base64
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['USER_FILE'] = 'users.json'

# 업로드 폴더 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 유저 정보 파일이 없으면 생성
if not os.path.exists(app.config['USER_FILE']):
    with open(app.config['USER_FILE'], 'w') as f:
        json.dump({}, f)

# 유저 정보 불러오기
def load_users():
    with open(app.config['USER_FILE'], 'r') as f:
        return json.load(f)

# 유저 정보 저장
def save_users(users):
    with open(app.config['USER_FILE'], 'w') as f:
        json.dump(users, f)

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('calendar_view'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']

        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            return redirect(url_for('calendar_view'))
        else:
            return render_template('login.html', error='아이디 또는 비밀번호가 틀렸습니다.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return render_template('register.html', error='이미 존재하는 아이디입니다.')

        users[username] = {
            'password': generate_password_hash(password)
        }
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/calendar')
def calendar_view():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('project.html', username=session['username'])

def get_user_date_folder(username, date):
    path = os.path.join(app.config['UPLOAD_FOLDER'], username, date)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

@app.route('/photos_page/<date>')
def photos_page(date):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    folder = get_user_date_folder(username, date)
    photos = []

    if os.path.exists(folder):
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            with open(filepath, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                photos.append({
                    'filename': filename,
                    'data': f"data:image/jpeg;base64,{encoded}"
                })

    return render_template('photos.html', date=date, photos=photos, username=username)

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return jsonify({'status': 'fail', 'message': '로그인 필요'})

    if 'file' not in request.files:
        return jsonify({'status': 'fail', 'message': '파일 없음'})

    file = request.files['file']
    date = request.form.get('date')
    photo_type = request.form.get('photo_type', 'default')

    if not date:
        return jsonify({'status': 'fail', 'message': '날짜 필요'})

    username = session['username']

    folder = os.path.join(app.config['UPLOAD_FOLDER'], username, date, photo_type)
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = file.filename
    filepath = os.path.join(folder, filename)
    file.save(filepath)

    return redirect(url_for('photos_page', date=date))

@app.route('/delete_photo', methods=['POST'])
def delete_photo():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    date = request.form['date']
    filename = request.form['filename']
    photo_type = request.form.get('photo_type', 'default')

    folder = os.path.join(app.config['UPLOAD_FOLDER'], username, date, photo_type)
    filepath = os.path.join(folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)

    return redirect(url_for('photos_page', date=date))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
