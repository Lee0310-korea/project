from flask import Flask, render_template, request, jsonify
import os
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# 업로드 폴더 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('calendar.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'files[]' not in request.files:
        return jsonify({'status': 'fail', 'message': 'No file part'})
    
    files = request.files.getlist('files[]')
    date = request.form.get('date')
    
    if not date:
        return jsonify({'status': 'fail', 'message': 'No date specified'})
    
    date_folder = os.path.join(app.config['UPLOAD_FOLDER'], date)
    if not os.path.exists(date_folder):
        os.makedirs(date_folder)
    
    saved_files = []
    for file in files:
        filename = file.filename
        filepath = os.path.join(date_folder, filename)
        file.save(filepath)
        saved_files.append(filename)
    
    return jsonify({'status': 'success', 'message': f'{len(saved_files)} files uploaded for {date}.'})

@app.route('/photos/<date>', methods=['GET'])
def get_photos(date):
    date_folder = os.path.join(app.config['UPLOAD_FOLDER'], date)
    if not os.path.exists(date_folder):
        return jsonify([])
    
    files = os.listdir(date_folder)
    photos = []
    for filename in files:
        filepath = os.path.join(date_folder, filename)
        with open(filepath, 'rb') as f:
            data = f.read()
            encoded = base64.b64encode(data).decode('utf-8')
            photos.append(f"data:image/jpeg;base64,{encoded}")
    
    return jsonify(photos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
