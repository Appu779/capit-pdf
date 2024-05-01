from flask import Flask, request
from firebase_admin import initialize_app, storage
import fitz
import tempfile
import os

# Initialize Firebase app
initialize_app()

# Initialize Firebase Cloud Storage with your specific bucket name
bucket = storage.bucket(name='capit-reference')

app = Flask(__name__)

@app.route('/', methods=['POST'])
def on_request_example():
    # Check if the request contains a file
    if 'file' not in request.files:
        return "No file uploaded.", 400

    uploaded_file = request.files['file']

    # Check if the uploaded file is a PDF
    if not uploaded_file.filename.endswith(".pdf"):
        return "Uploaded file is not a PDF.", 400

    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
        temp_pdf.write(uploaded_file.read())
        pdf_path = temp_pdf.name

    # Open the uploaded PDF
    pdf_document = fitz.open(pdf_path)

    # Create a temporary directory to store generated images
    with tempfile.TemporaryDirectory() as temp_dir:
        # Iterate through each page
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)

            # Iterate through each image on the page
            for img_index, img in enumerate(page.get_images(full=True)):
                # Extract image data
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                # Save the image data to a file
                image_file_name = f"page{page_number}_image{img_index}.png"
                image_file_path = os.path.join(temp_dir, image_file_name)
                with open(image_file_path, "wb") as image_file:
                    image_file.write(image_bytes)

                # Upload the generated image to Firebase Cloud Storage
                blob = bucket.blob(image_file_name)
                blob.upload_from_filename(image_file_path)

    # Close the uploaded PDF
    pdf_document.close()

    # Delete the temporary PDF file
    os.remove(pdf_path)

    return "Images extracted from PDF and saved to Cloud Storage."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
