# === Standard Library Imports ===
import os
import re
import json
import logging
from datetime import datetime

# === Django Imports ===
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.conf import settings

# === Third-Party Libraries ===
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.db import OperationalError, ProgrammingError

from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import google.generativeai as genai

# === App-Specific Imports ===
from .models import Note, Tag, File
from .utils import (
    UploadFileForm,
    SearchForm,
    pdf_reader,
    doc_reader,
    extract_text_from_image,
    extract_images_from_pdf,
    Obj_Detect_Name,
    generate_tags,
    save_file,
    perform_search,
    convert_png_to_jpg,
    rename_file_if_too_long,
)

# === Configuration ===
GEMINI_API_KEY = "GeminiKey"
now = datetime.now().strftime("%B %d, %Y %H:%M:%S")
logger = logging.getLogger(__name__)
url = 'http://127.0.0.1:8000/notes/save/'

# === Setup Gemini API ===
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")

def ask_gemini(query, context):
    prompt = f"Today's date and time is: {now}\n{context}\n\nBased on the above information, {query}"
    response = gemini_model.generate_content(prompt)
    return response.text

# === HuggingFace QA Model ===
question_answerer = pipeline("question-answering", model='distilbert-base-cased-distilled-squad')

# === Semantic Search Setup ===
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
corpus_matrix = None
notes_corpus = []

def encode_corpus(notes):
    if not notes or all(not note.strip() for note in notes):
        raise ValueError("Input 'notes' is empty or contains only whitespace.")
    return tfidf_vectorizer.fit_transform(notes)

def semantic_search(query, top_k=5):
    global corpus_matrix
    if corpus_matrix is None:
        logger.warning("Corpus matrix is not initialized. Skipping search.")
        return []
    query_vec = tfidf_vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, corpus_matrix).flatten()
    top_indices = similarities.argsort()[::-1][:top_k]
    return [(notes_corpus[idx], similarities[idx]) for idx in top_indices if similarities[idx] > 0]

# === Notes Views ===
@csrf_exempt
def save_note_view(request):
    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        if not content:
            return JsonResponse({'response': 'Note content cannot be empty.'}, status=400)

        try:
            Note.objects.create(content=content)
            update_corpus()
            return JsonResponse({'response': 'Note saved successfully.'})
        except Exception as e:
            logger.error(f"Error saving note: {e}")
            return JsonResponse({'response': 'An error occurred while saving the note.'}, status=500)

    return JsonResponse({'response': 'Invalid request method.'}, status=400)

@csrf_exempt
def search_notes_view(request):
    if request.method == 'POST':
        query = request.POST.get('message', '').strip()
        if not query:
            return JsonResponse({'response': 'Query cannot be empty.'}, status=400)

        if corpus_matrix is None or not notes_corpus:
            load_existing_notes()

        try:
            results = semantic_search(query)
            if results:
                relevant_notes = "\n\n".join([f"{note}" for note, _ in results])
                response = ask_gemini(query, relevant_notes)
                result = question_answerer(question=query, context=response)
                return JsonResponse({'response': result['answer']})
            return JsonResponse({'response': 'No relevant notes found.'})
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return JsonResponse({'response': 'An error occurred during the search.'}, status=500)

    return JsonResponse({'response': 'Invalid request method.'}, status=400)

@csrf_exempt
def save_plain_text_response_view(request):
    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        if not content:
            return JsonResponse({'response': 'Note content cannot be empty.'}, status=400)

        try:
            file_path = save_note_to_file(content)
            Note.objects.create(content=content, file_path=file_path)
            return JsonResponse({'response': 'Note saved successfully.'})
        except Exception as e:
            logger.error(f"Error saving plain text note: {e}")
            return JsonResponse({'response': 'An error occurred while saving the note.'}, status=500)

    return JsonResponse({'response': 'Invalid request method.'}, status=400)

def save_note_to_file(content):
    notes_directory = os.path.abspath(settings.NOTES_DIR)
    os.makedirs(notes_directory, exist_ok=True)

    timestamp = timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_name = f"note_{timestamp}.txt"
    file_path = os.path.join(notes_directory, file_name)

    if not file_path.startswith(notes_directory):
        raise ValueError("Invalid file path.")

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except IOError as e:
        logger.error(f"Error saving file: {e}")
        raise

    return file_path

def extract_plain_text(response):
    text = re.sub(r'[#*><\[\]\(\)_`]', '', response)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_tags(content):
    vectorizer = TfidfVectorizer(max_features=90, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([content])
    features = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]
    word_scores = sorted(zip(features, scores), key=lambda x: x[1], reverse=True)
    top_tags = [word[:255] for word, _ in word_scores if len(word) <= 255][:90]
    return [Tag.objects.get_or_create(name=tag)[0] for tag in top_tags]

def load_existing_notes():
    global corpus_matrix, notes_corpus
    cached_corpus = cache.get('notes_corpus')
    if cached_corpus:
        corpus_matrix, notes_corpus = cached_corpus
        return

    try:
        notes = list(Note.objects.all().values_list('content', flat=True))
        if notes:
            corpus_matrix = encode_corpus(notes)
            notes_corpus = notes
            cache.set('notes_corpus', (corpus_matrix, notes_corpus), timeout=3600)
        else:
            logger.info("No notes found in the database. Skipping corpus encoding.")
    except (OperationalError, ProgrammingError) as e:
        logger.warning(f"Database error: {e}")

def update_corpus():
    global corpus_matrix, notes_corpus
    try:
        notes = list(Note.objects.all().values_list('content', flat=True))
        if notes:
            corpus_matrix = encode_corpus(notes)
            notes_corpus = notes
            cache.set('notes_corpus', (corpus_matrix, notes_corpus), timeout=3600)
    except Exception as e:
        logger.error(f"Error updating corpus: {e}")

def chat_interface(request):
    return render(request, 'notes/chat_interface.html')

# === File Upload and Search Views ===
def upload_and_search(request):
    upload_form = UploadFileForm()
    search_form = SearchForm()
    files = []
    query = ""

    if request.method == 'POST':
        query = request.POST.get('query', '')
        action = request.POST.get('action')

        if action == 'upload':
            upload_form = UploadFileForm(request.POST, request.FILES)
            if upload_form.is_valid():
                file = request.FILES['file']
                text = ""

                if file.name.endswith('.pdf'):
                    text = pdf_reader(file)
                    pdf_rel_path = default_storage.save("temp_uploaded.pdf", file)
                    pdf_abs_path = default_storage.path(pdf_rel_path)

                    try:
                        image_paths = extract_images_from_pdf(pdf_abs_path)
                        for img_path in image_paths:
                            text += " " + " ".join(Obj_Detect_Name(img_path))
                    except Exception as e:
                        logger.error(f"Error processing PDF: {e}")
                    finally:
                        default_storage.delete(pdf_abs_path)

                elif file.name.endswith(('.doc', '.docx')):
                    text = doc_reader(file)

                elif file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    text = extract_text_from_image(file)
                    if file.name.lower().endswith('.png'):
                        file = convert_png_to_jpg(file)
                    text += " " + " ".join(Obj_Detect_Name(file))

                elif file.name.endswith('.txt'):
                    try:
                        text = file.read().decode('utf-8')
                    except UnicodeDecodeError:
                        text = file.read().decode('latin-1')

                requests.post(url, data={'message': text})
                tags = generate_tags(text)
                save_file(file.name, file, tags)
                files = perform_search(query)

        elif action == 'search':
            search_form = SearchForm(request.POST)
            if search_form.is_valid():
                query = search_form.cleaned_data['query']
                files = perform_search(query)

    return render(request, 'notes/upload.html', {
        'upload_form': upload_form,
        'search_form': SearchForm(initial={'query': query}),
        'files': files,
        'query': query,
    })

@require_http_methods(["POST"])
def rename_file(request, file_id):
    try:
        file_instance = get_object_or_404(File, id=file_id)
        data = json.loads(request.body)
        new_name_base = data.get('new_name_base')

        if not new_name_base:
            return JsonResponse({'success': False, 'message': 'New name is required.'}, status=400)

        if not re.match(r'^[\w\-. ]+$', new_name_base):
            return JsonResponse({'success': False, 'message': 'Invalid new name. It must not contain special characters.'}, status=400)

        old_ext = os.path.splitext(file_instance.file_content.name)[1]
        new_file_name = rename_file_if_too_long(new_name_base + old_ext)

        old_file_path = file_instance.file_content.path
        new_file_path = os.path.join(os.path.dirname(old_file_path), new_file_name)

        if os.path.exists(new_file_path):
            return JsonResponse({'success': False, 'message': 'File with the new name already exists.'}, status=400)

        os.rename(old_file_path, new_file_path)
        file_instance.file_name = new_file_name
        file_instance.file_content.name = os.path.relpath(new_file_path, settings.MEDIA_ROOT)
        file_instance.save()

        return JsonResponse({'success': True, 'new_name': new_file_name})
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@require_http_methods(["POST"])
def delete_file(request, file_id):
    try:
        file_instance = get_object_or_404(File, id=file_id)
        file_path = file_instance.file_content.path

        if os.path.exists(file_path):
            os.remove(file_path)

        file_instance.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def download_file(request, file_id):
    try:
        file_instance = get_object_or_404(File, id=file_id)
        file_path = file_instance.file_content.path
        file_name = file_instance.file_name

        if not os.path.exists(file_path):
            return HttpResponse(f"Error: The requested file does not exist at path: {file_path}", status=404)

        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return HttpResponse(f"Error downloading file: {str(e)}", status=500)

# Load notes into memory on server start
load_existing_notes()