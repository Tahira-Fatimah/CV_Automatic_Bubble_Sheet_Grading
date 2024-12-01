from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename
import subprocess

mcq_answers = {}

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
OUTPUT_FOLDER = 'static/output_images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"message": f"Image {filename} uploaded successfully"})
    
    return jsonify({"error": "File not allowed"})

@app.route('/run-script', methods=['GET'])
def run_script():
    try:
        uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
        if not uploaded_files:
            return jsonify({"error": "No files found in the upload directory"})

        uploaded_files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
        image_filename = uploaded_files[0]
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        mcq_answers_str = str(mcq_answers)
        result = subprocess.run(['python', 'omr.py', image_path,mcq_answers_str], capture_output=True, text=True)
        print("gfgf" + result.stdout)
        if result.returncode == 0:
            return redirect(url_for('answer_key'))
        else:
            return jsonify({"error": "Script execution failed", "output": result.stderr})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/answer-key', methods=['GET', 'POST'])
def answer_key():
    if request.method == 'POST':
        answers = {}
        for i in range(1, 11):
            answer = request.form.get(f'question_{i}')
            answers[f'question_{i}'] = answer
        print(answers)  # Process the answers here (e.g., store or validate them)
        return redirect(url_for('success', output="Answers submitted successfully!"))
    
    return render_template('answer_key.html')

@app.route('/success')
def success():
    output = request.args.get('output', 'No output available')
    return render_template('success.html', output=output)

# Route to handle the form submission
@app.route('/submit-answer-key', methods=['POST'])
def submit_answer_key():

    global mcq_answers
    # Extract data from the form submission
    mcq_answers = {
        0: int(request.form.get('mcq1')),
        1: int(request.form.get('mcq2')),
        2: int(request.form.get('mcq3')),
        3: int(request.form.get('mcq4')),
        4: int(request.form.get('mcq5')),
        5: int(request.form.get('mcq6')),
        6: int(request.form.get('mcq7')),
        7: int(request.form.get('mcq8')),
        8: int(request.form.get('mcq9')),
        9: int(request.form.get('mcq10'))
    }

    # Print the answers (you can replace this with saving the answers to a database or other logic)
    print("Received Answer Key:", mcq_answers)

    # Return a JSON response indicating success
    # return redirect(url_for('run_script'))
    return jsonify({
        'message': 'Answer key submitted successfully!',
        'received_data': mcq_answers
    })



if __name__ == '__main__':
    app.run(debug=True)
