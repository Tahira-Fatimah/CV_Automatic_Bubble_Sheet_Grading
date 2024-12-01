from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename
import subprocess

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
        # Check uploaded files in the directory
        uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
        if not uploaded_files:
            return jsonify({"error": "No files found in the upload directory"}), 400

        # Sort the files by modification time and select the most recent one
        uploaded_files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
        image_filename = uploaded_files[0]
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)

        # Execute the script
        result = subprocess.run(['python', 'omr.py', image_path], capture_output=True, text=True)

        # Check if the script executed successfully
        if result.returncode == 0:
            # Strip any extra newlines from the output
            output = result.stdout.strip()
            return jsonify({"message": "Script executed successfully", "output": output}), 200
        else:
            return jsonify({"error": "Script execution failed", "output": result.stderr}), 500

    except Exception as e:
        # Handle any unexpected errors and return a 500 error
        return jsonify({"error": f"Unexpected error occurred: {str(e)}"}), 500

@app.route('/success')
def success():
    output = request.args.get('output', 'No output available')
    print(f"Output received in success route: {output}")
    return render_template("success.html",output = output)


if __name__ == '__main__':
    app.run(debug=True)
