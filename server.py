from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# 업로드 폴더 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 메인 : 로그인 페이지
@app.route('/')
def home():
    return render_template('login.html')

#  로그인 처리
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # 예시 검증 (추후 DB 연동 가능)
    if username == 'admin' and password == '1234':
        return redirect(url_for('calendar'))
    else:
        return "로그인 실패. 다시 시도하세요."

#  달력 페이지
@app.route('/calendar')
def calendar():
    return render_template('project.html')

#  사진 업로드 API (두 종류: face, real)
@app.route('/upload', methods=['POST'])
def upload():
    date = request.form.get('date')
    category = request.form.get('category')  # face or real

    if 'file' not in request.files:
        return jsonify({'status': 'fail', 'message': 'No file part'})

    file = request.files['file']

    if not date or not category:
        return jsonify({'status': 'fail', 'message': 'No date or category specified'})

    # 날짜별 + 카테고리별 폴더 생성
    category_folder = os.path.join(app.config['UPLOAD_FOLDER'], date, category)
    os.makedirs(category_folder, exist_ok=True)

    filepath = os.path.join(category_folder, file.filename)
    file.save(filepath)

    return jsonify({'status': 'success', 'message': f'File uploaded for {date} ({category}).'})

#  특정 날짜 사진 조회 페이지
@app.route('/photos_page/<date>')
def get_photos_page(date):
    photos = {'face': [], 'real': []}
    for category in ['face', 'real']:
        category_folder = os.path.join(app.config['UPLOAD_FOLDER'], date, category)
        if os.path.exists(category_folder):
            for filename in os.listdir(category_folder):
                filepath = os.path.join(category_folder, filename)
                with open(filepath, 'rb') as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode('utf-8')
                    photos[category].append({
                        'filename': filename,
                        'data': f"data:image/jpeg;base64,{encoded}",
                        'category': category
                    })
    return render_template('photos.html', date=date, photos=photos)
#  파일 삭제
@app.route('/delete_photo', methods=['POST'])
def delete_photo():
    date = request.form.get('date')
    category = request.form.get('category')
    filename = request.form.get('filename')

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], date, category, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'status': 'success', 'message': 'File deleted'})
    else:
        return jsonify({'status': 'fail', 'message': 'File not found'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
