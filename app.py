from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
import config
from description import get_latest_image_url, generate_description

app = Flask(__name__)

# Configure the upload folder and secret key
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = config.API_KEY

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the index.html template."""
    with app.app_context():
        return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """Handle image upload."""
    if 'image' not in request.files:
        return 'No file part in the request.', 400

    file = request.files['image']

    if file.filename == '':
        return 'No file selected.', 400

    if file and allowed_file(file.filename):
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            with app.app_context():
                # Get the latest image URL
                image_url = get_latest_image_url()
                
                if not image_url:
                    return 'No image found after upload.', 500
                
                # Generate description using the image URL
                response = generate_description()
                
                # Extract the description content
                description = response.choices[0].message.content
                
                # Return both image and description
                return render_template('index.html', 
                                    image_url=image_url, 
                                    description=description)
            
        except Exception as e:
            print(f"Error: {e}")
            return f"An error occurred: {str(e)}", 500
    
    return 'Unsupported file type.', 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve the uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)