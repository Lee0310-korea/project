from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import base64
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 꼭 바꿔주세요!

app.config['UPLOAD_FOLDER'] = 'uploads'

# 업로드 폴더 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 사용자 저장 (임시, 실제 DB 권장)
# 아이디 : 비밀번호 해시
users = {}

# --- 유틸 함수 ---
def save_user(username, password):
    hashed_pw = generate_password_hash(password)
    users[username] = hashed_pw

def verify_user(username, password):
    if username in users and check_password_hash(users[username], password):
        return True
    return False

# --- 라우트 ---

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('calendar_page'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if verify_user(username, password):
            session['username'] = username
            return redirect(url_for('calendar_page'))
        else:
            return render_template('login.html', error='아이디 또는 비밀번호가 잘못되었습니다.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if not username or not password or not confirm:
            return render_template('register.html', error='모든 필드를 입력해주세요.')
        if password != confirm:
            return render_template('register.html', error='비밀번호가 일치하지 않습니다.')
        if username in users:
            return render_template('register.html', error='이미 존재하는 아이디입니다.')
        save_user(username, password)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/calendar')
def calendar_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('project.html', username=session['username'])

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return jsonify({'status': 'fail', 'message': '로그인이 필요합니다.'}), 401
    
    username = session['username']

    if 'files[]' not in request.files:
        return jsonify({'status': 'fail', 'message': 'No file part'}), 400
    
    files = request.files.getlist('files[]')
    date = request.form.get('date')
    photo_type = request.form.get('photo_type')  # 'face' or 'work'
    
    if not date or not photo_type:
        return jsonify({'status': 'fail', 'message': 'No date or photo_type specified'}), 400

    # 사용자별 폴더 -> 날짜별 폴더 -> 사진 종류별 폴더
    base_path = os.path.join(app.config['UPLOAD_FOLDER'], username, date, photo_type)
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    saved_files = []
    for file in files:
        filename = file.filename
        filepath = os.path.join(base_path, filename)
        file.save(filepath)
        saved_files.append(filename)

    return jsonify({'status': 'success', 'message': f'{len(saved_files)} files uploaded for {date} ({photo_type}).'})

@app.route('/photos/<date>/<photo_type>', methods=['GET'])
def get_photos(date, photo_type):
    if 'username' not in session:
        return jsonify([]), 401
    
    username = session['username']
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], username, date, photo_type)
    
    if not os.path.exists(folder_path):
        return jsonify([])
    
    files = os.listdir(folder_path)
    photos = []
    for filename in files:
        filepath = os.path.join(folder_path, filename)
        with open(filepath, 'rb') as f:
            data = f.read()
            encoded = base64.b64encode(data).decode('utf-8')
            photos.append(f"data:image/jpeg;base64,{encoded}")
    return jsonify(photos)

@app.route('/delete_photo', methods=['POST'])
def delete_photo():
    if 'username' not in session:
        return jsonify({'status': 'fail', 'message': '로그인이 필요합니다.'}), 401
    
    username = session['username']
    date = request.form.get('date')
    photo_type = request.form.get('photo_type')
    filename = request.form.get('filename')

    if not date or not photo_type or not filename:
        return jsonify({'status': 'fail', 'message': '필수 정보가 부족합니다.'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], username, date, photo_type, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'status': 'success', 'message': '파일이 삭제되었습니다.'})
    else:
        return jsonify({'status': 'fail', 'message': '파일을 찾을 수 없습니다.'}), 404

if __name__ == '__main__':
    # 예시: admin 계정 생성 (비밀번호: 1234)
    if 'admin' not in users:
        save_user('admin', '1234')
    app.run(host='0.0.0.0', port=5000, debug=True)
