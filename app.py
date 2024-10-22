from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import io
import base64
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import shutil

app = Flask(__name__)

# Configurations
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('upload.html')




@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return "Invalid file"

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Redirect to the sign_document route
    return redirect(url_for('sign_document', filename=filename))


@app.route('/sign/<filename>', methods=['GET'])
def sign_document(filename):
    return render_template('sign_document.html', filename=filename)


@app.route('/sign/<filename>', methods=['POST'])
def sign_document_and_save(filename):
    # Get the signature from the form
    signature_data = request.form['signature']

    # Decode the base64 image data
    signature_image = Image.open(io.BytesIO(base64.b64decode(signature_data.split(",")[1])))

    # Save the signature image as a temporary file
    signature_image.save("signature.png")

    # Open the existing PDF
    input_pdf = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    reader = PdfReader(input_pdf)

    # Create a new PDF to hold the signed version
    output_pdf = os.path.join(app.config['UPLOAD_FOLDER'], f"signed_{filename}")
    writer = PdfWriter()

    # For demonstration, let's assume we're adding the signature to the first page
    page = reader.pages[0]

    # Create a canvas to overlay the signature
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Set the position for the signature
    x = 100  # Adjust X position
    y = 100  # Adjust Y position
    can.drawImage("signature.png", x, y, 200, 50, mask='auto')  # Adjust size as needed
    can.save()

    packet.seek(0)
    overlay_pdf = PdfReader(packet)

    # Merge the original page with the signature
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    # Write the final signed PDF
    with open(output_pdf, 'wb') as output_file:
        writer.write(output_file)

    # After saving the signed PDF, return a download link
    return redirect(url_for('download_file', filename=f"signed_{filename}"))

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    app.run(debug=True)
