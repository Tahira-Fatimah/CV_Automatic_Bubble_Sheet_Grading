from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import subprocess

app = Flask(__name__)

# Set the folder where uploaded images will be saved
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check if file is an allowed image type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template("index.html")

# Route to upload the image
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Ensure the upload directory exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"message": f"Image {filename} uploaded successfully"})
    
    return jsonify({"error": "File not allowed"})



@app.route('/run-script', methods=['GET'])
def run_script():
    try:
        # Get the latest uploaded file from the 'uploads' folder
        uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
        if not uploaded_files:
            return jsonify({"error": "No files found in the upload directory"})

        # Sort files by modification time and take the most recent one
        uploaded_files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
        image_filename = uploaded_files[0]
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)

        # Run the script with the image path
        result = subprocess.run(['python', 'omr.py', image_path], capture_output=True, text=True)

        # Log the script's output
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        
        if result.returncode == 0:
            return jsonify({"message": "Script executed successfully!", "output": result.stdout})
        else:
            return jsonify({"error": "Script execution failed", "output": result.stderr})

    except Exception as e:
        return jsonify({"error": str(e)})




if __name__ == '__main__':
    app.run(debug=True)
