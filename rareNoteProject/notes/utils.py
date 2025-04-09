import io
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, FileResponse, JsonResponse
from .models import File, Tag, FileTag
from .forms import UploadFileForm, SearchForm
from hashlib import sha256
import pdfplumber
import textract
import docx2txt
import spacy
from PIL import Image
import pytesseract
import os
import uuid
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from collections import defaultdict
import re
import json
from django.conf import settings
from transformers import YolosImageProcessor, YolosForObjectDetection
import torch
import fitz
import tempfile

# Lazy model loading
def get_yolos_model():
    if not hasattr(get_yolos_model, "model") or not hasattr(get_yolos_model, "image_processor"):
        get_yolos_model.model = YolosForObjectDetection.from_pretrained('hustvl/yolos-tiny')
        get_yolos_model.image_processor = YolosImageProcessor.from_pretrained('hustvl/yolos-tiny')
    return get_yolos_model.model, get_yolos_model.image_processor

# Conditional Tesseract path for Windows
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load spaCy NLP model
nlp = spacy.load('en_core_web_sm')

import tempfile

def extract_images_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    image_paths = []

    with tempfile.TemporaryDirectory() as temp_dir:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img_path = os.path.join(temp_dir, f"page_{page_num + 1}.jpg")
            pix.save(img_path)
            # Immediately process the image and keep data in memory
            image_paths.append(img_path)

        # Move or copy images out of the temp directory before it closes
        persistent_paths = []
        for path in image_paths:
            final_path = os.path.join(settings.MEDIA_ROOT, "pdf_images", os.path.basename(path))
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            with open(path, "rb") as src, open(final_path, "wb") as dst:
                dst.write(src.read())
            persistent_paths.append(final_path)

        return persistent_paths


def Obj_Detect_Name(image_path):
    image = Image.open(image_path)
    model, image_processor = get_yolos_model()
    inputs = image_processor(images=image, return_tensors="pt")
    outputs = model(**inputs)
    target_sizes = torch.tensor([image.size[::-1]])
    results = image_processor.post_process_object_detection(outputs, threshold=0.9, target_sizes=target_sizes)[0]
    return [model.config.id2label[label.item()] for label in results["labels"]]

def convert_png_to_jpg(png_path):
    img = Image.open(png_path)
    rgb_img = img.convert("RGB")
    jpg_image_io = io.BytesIO()
    rgb_img.save(jpg_image_io, format="JPEG")
    jpg_image_io.seek(0)
    return jpg_image_io

def extract_text_from_image(image):
    try:
        img = Image.open(image)
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"Error extracting text from image: {e}"

def pdf_reader(file):
    try:
        with pdfplumber.open(file) as pdf:
            all_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                all_text += text + "\n" if text else ""
            return all_text
    except Exception as e:
        return f"Error reading PDF: {e}"

def doc_reader(file):
    try:
        if file.name.endswith('.doc'):
            text = textract.process(file).decode('utf-8')
        else:
            text = docx2txt.process(file)
        return text
    except Exception as e:
        return f"Error reading document: {e}"

def generate_tags(content):
    try:
        doc = nlp(content)
        tags = {token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop and len(token) > 2}
        return tags
    except Exception as e:
        print(f"Error generating tags: {e}")
        return set()

def rename_file_if_too_long(file_name, max_length=50):
    name, ext = os.path.splitext(file_name)
    if len(file_name) > max_length:
        trimmed_name = name[:max_length - len(ext) - 4] + "_" + str(uuid.uuid4())[:4] + ext
        return trimmed_name
    return file_name

def save_file(file_name, file_content, tags):
    try:
        file_name = rename_file_if_too_long(file_name, max_length=50)
        content_hash = sha256(file_content.read()).hexdigest()
        file_content.seek(0)

        file_instance = File(file_name=file_name, file_content=file_content, content_hash=content_hash)
        file_instance.save()
        # After saving file_instance
        print(f"Associating tags: {tags} with file: {file_instance.file_name}")  # DEBUG


        saved_file_path = file_instance.file_content.path
        print(f"File saved at: {saved_file_path}")

        if not os.path.exists(saved_file_path):
            print(f"Error: File was saved but does not exist at path: {saved_file_path}")
            return

        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            FileTag.objects.create(file=file_instance, tag=tag)
    except Exception as e:
        print(f"Error saving file: {e}")

def perform_search(query):
    search_tags = generate_tags(query)
    print(f"Generated tags from query: {search_tags}") 
    file_hit_count = defaultdict(int)
    for tag in search_tags:
        tag_file_hits = FileTag.objects.filter(tag__name=tag).values_list('file', flat=True).distinct()
        for file_hit in tag_file_hits:
            file_hit_count[file_hit] += 1
    sorted_file_hits = sorted(file_hit_count.items(), key=lambda x: x[1], reverse=True)
    print(sorted_file_hits)
    return [File.objects.get(id=file_id) for file_id, _ in sorted_file_hits]