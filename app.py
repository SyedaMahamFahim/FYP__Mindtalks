from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from utils.clean_eeg import process_subject_session
from utils.cloud_helper import upload_bdf_file_to_s3, upload_file_to_s3,get_data_for_arduino
from utils.model_utils import evaluate_model
from utils.extract_features_using_csp import extract_features_using_csp
import os
import json
from dotenv import load_dotenv




os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
app = Flask(__name__)

load_dotenv()  # Defaults to loading .env file from the root folder


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'bdf', 'png', 'pdf','fif','npz'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER










def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_file_to_s3', methods=['POST'])
def upload_file_to_s3_endpoint():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    folder_name = request.form.get('folder_name', 'default-folder')

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_file(file.filename):
        success = upload_file_to_s3(file, folder_name)
        if success:
            return jsonify({'status': 'success', 'message': 'File uploaded successfully to S3 api', 'filename': file.filename})
        else:
            return jsonify({'error': 'File upload failed'})
    
    return jsonify({'error': 'Invalid file format'})





@app.route('/extract-csp-features', methods=['POST'])
def extract_csp_features():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    folder_name = request.form.get('folder_name', 'default-folder')
    subject_no = request.form.get('subject', 'default-subject')
    session_no = request.form.get('session', 'default-session')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if subject_no == '' or session_no == '':
        return jsonify({'error': 'Subject or session number is empty'})
    
    if file and allowed_file(file.filename):
        print("File is uploading to cloud")
        filename = secure_filename(file.filename)
        local_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(local_file_path)
        
        
        s3_image_url = upload_bdf_file_to_s3(file, folder_name)
        print("File uploaded to cloud")
        print("this is the s3 url",s3_image_url)
        
        if s3_image_url:
            print("File uploaded to cloud")
        else:
            print("File not uploaded to cloud")

    try:
        print("Extracting features")
        root_dir = os.path.join("static")

        eeg_s3_url = extract_features_using_csp(local_file_path,root_dir, subject_no, session_no)


        return jsonify({'s3_url': eeg_s3_url}), 200
    except Exception as e:
            # os.remove(filepath)
        return jsonify({'error': str(e)}), 500



@app.route('/last-entry', methods=['GET'])
def get_last_entry():
    item = get_data_for_arduino('Model_Prediction')

    if not item:
        return jsonify({'error': 'No data found'}), 404
    
    # Parse class_distribution from JSON string to dictionary
    if 'class_distribution' in item:
        item['class_distribution'] = json.loads(item['class_distribution'])
    
    # Parse classification_report from JSON string to dictionary
    if 'classification_report' in item:
        item['classification_report'] = json.loads(item['classification_report'])
    
    return jsonify(item)




@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        print(file)
        print("this is the fiel path",file.filename)
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print("this is the file path after", filepath)
        # filepath = file.filename
        model_path = "./static/model_file/cnn_model.h5"
        scaler_path = "./static/model_file/training_scaler.pkl"
        
        try:
            results = evaluate_model(filepath, model_path, scaler_path)
            print("====================================")
            print("This is the result",results)
            print("====================================")

            # os.remove(filepath)
            return jsonify(results), 200
        except Exception as e:
            # os.remove(filepath)
            return jsonify({'error': str(e)}), 500

    else:
        return jsonify({'error': 'Invalid file format. Allowed extensions: {}'.format(ALLOWED_EXTENSIONS)}), 400




@app.route('/preprocess_eeg_data', methods=['POST'])
def preprocess_eeg_data():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    folder_name = request.form.get('folder_name', 'default-folder')
    subject_no = request.form.get('subject', 'default-subject')
    session_no = request.form.get('session', 'default-session')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if subject_no == '' or session_no == '':
        return jsonify({'error': 'Subject or session number is empty'})
    
    if file and allowed_file(file.filename):
        print("File is uploading to cloud")
        filename = secure_filename(file.filename)
        local_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(local_file_path)
        
        
        s3_image_url = upload_bdf_file_to_s3(file, folder_name)
        print("File uploaded to cloud")
        print("this is the s3 url",s3_image_url)
        
        if s3_image_url:
            print("File uploaded to cloud")
        else:
            print("File not uploaded to cloud")

    try:
        print("Processing subject session")

        eog_file_name,baseline_file_name,pickle_file_name, eeg_file_name,events_file_name = process_subject_session(local_file_path,subject_no, session_no)


        return jsonify({'eog_file': eog_file_name,
        'baseline_file': baseline_file_name,
        'pickle_file': pickle_file_name,
        'eeg_file': eeg_file_name,
        'events_file': events_file_name}), 200
    except Exception as e:
            # os.remove(filepath)
        return jsonify({'error': str(e)}), 500
  


################# Pages ################
@app.route('/extract-features')
def extract_features_page():
    return render_template('extract-features.html')

@app.route('/test-file')
def test_file_page():
    return render_template('test-file.html')

@app.route('/clean-file')
def clean_eeg_files_page():
    return render_template('clean-eeg-file.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/team')
def team():
    return render_template('team.html')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

