from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# 업로드 폴더 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('project.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files or 'date' not in request.form:
        return redirect(request.referrer)
    
    file = request.files['file']
    date = request.form.get('date')
    
    date_folder = os.path.join(app.config['UPLOAD_FOLDER'], date)
    if not os.path.exists(date_folder):
        os.makedirs(date_folder)
    
    filepath = os.path.join(date_folder, file.filename)
    file.save(filepath)
    
    return redirect(url_for('get_photos_page', date=date))

@app.route('/delete_photo', methods=['POST'])
def delete_photo():
    date = request.form.get('date')
    filename = request.form.get('filename')
    
    date_folder = os.path.join(app.config['UPLOAD_FOLDER'], date)
    filepath = os.path.join(date_folder, filename)
    
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return redirect(url_for('get_photos_page', date=date))

@app.route('/photos_page/<date>')
def get_photos_page(date):
    date_folder = os.path.join(app.config['UPLOAD_FOLDER'], date)
    photos = []
    
    if os.path.exists(date_folder):
        files = os.listdir(date_folder)
        for filename in files:
            filepath = os.path.join(date_folder, filename)
            with open(filepath, 'rb') as f:
                data = f.read()
                encoded = base64.b64encode(data).decode('utf-8')
                photos.append({'filename': filename, 'data': f"data:image/jpeg;base64,{encoded}"})
    
    return render_template('photos.html', date=date, photos=photos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
