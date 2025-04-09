import os
import re
import logging
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .models import Note, Tag
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.db import OperationalError, ProgrammingError
from transformers import pipeline
question_answerer = pipeline("question-answering", model='distilbert-base-cased-distilled-squad')
# === Logger Setup ===
logger = logging.getLogger(__name__)
url = 'http://127.0.0.1:8000/notes/save/'
# === Semantic Search Setup (using TF-IDF + Cosine Similarity) ===
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
corpus_matrix = None
notes_corpus = []

def encode_corpus(notes):
    """
    Encodes the notes corpus into a TF-IDF matrix.
    Raises an error if the input is empty or contains only whitespace.
    """
    if not notes or all(not note.strip() for note in notes):
        raise ValueError("Input 'notes' is empty or contains only whitespace.")
    return tfidf_vectorizer.fit_transform(notes)

def semantic_search(query, top_k=5):
    """
    Performs a semantic search using cosine similarity.
    Returns the top-k most relevant notes along with their similarity scores.
    """
    global corpus_matrix
    if corpus_matrix is None:
        logger.warning("Corpus matrix is not initialized. Skipping search.")
        return []

    query_vec = tfidf_vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, corpus_matrix).flatten()
    top_indices = similarities.argsort()[::-1][:top_k]
    return [(notes_corpus[idx], similarities[idx]) for idx in top_indices if similarities[idx] > 0]

# === Views ===
@csrf_exempt
def save_note_view(request):
    """
    Saves a new note to the database and updates the corpus.
    """
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
    """
    Searches for notes semantically based on a query.
    """
    if request.method == 'POST':
        query = request.POST.get('message', '').strip()
        if not query:
            return JsonResponse({'response': 'Query cannot be empty.'}, status=400)

        # Lazy initialization of the corpus
        if corpus_matrix is None or not notes_corpus:
            load_existing_notes()

        try:
            results = semantic_search(query)
            if results:
                relevant_notes = "\n\n".join([f"{note}" for note, _ in results])
                result = question_answerer(question=query,context=relevant_notes)
                print(result['answer'])
                return JsonResponse({'response': result['answer']})
            return JsonResponse({'response': 'No relevant notes found.'})
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return JsonResponse({'response': 'An error occurred during the search.'}, status=500)

    return JsonResponse({'response': 'Invalid request method.'}, status=400)

@csrf_exempt
def save_plain_text_response_view(request):
    """
    Saves a note as plain text to both the database and the file system.
    """
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
    """
    Saves a note as a plain text file in the specified directory.
    """
    notes_directory = os.path.abspath(settings.NOTES_DIR)
    os.makedirs(notes_directory, exist_ok=True)

    timestamp = timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_name = f"note_{timestamp}.txt"
    file_path = os.path.join(notes_directory, file_name)

    # Validate file path
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
    """
    Extracts plain text from a response by removing special characters and HTML tags.
    """
    text = re.sub(r'[#*><\[\]\(\)_`]', '', response)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_tags(content):
    """
    Extracts tags from note content using TF-IDF.
    Limits tag names to 255 characters and ensures uniqueness.
    """
    vectorizer = TfidfVectorizer(max_features=90, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([content])
    features = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]
    word_scores = sorted(zip(features, scores), key=lambda x: x[1], reverse=True)
    top_tags = [word[:255] for word, _ in word_scores if len(word) <= 255][:90]

    tags = [Tag.objects.get_or_create(name=tag)[0] for tag in top_tags]
    return tags

def load_existing_notes():
    """
    Loads existing notes from the database and encodes the corpus.
    Skips encoding if no notes are found.
    """
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
            cache.set('notes_corpus', (corpus_matrix, notes_corpus), timeout=3600)  # Cache for 1 hour
        else:
            logger.info("No notes found in the database. Skipping corpus encoding.")
    except (OperationalError, ProgrammingError) as e:
        logger.warning(f"Database error: {e}")

def update_corpus():
    """
    Updates the corpus after a new note is added.
    """
    global corpus_matrix, notes_corpus
    try:
        notes = list(Note.objects.all().values_list('content', flat=True))
        if notes:
            corpus_matrix = encode_corpus(notes)
            notes_corpus = notes
            cache.set('notes_corpus', (corpus_matrix, notes_corpus), timeout=3600)  # Cache for 1 hour
    except Exception as e:
        logger.error(f"Error updating corpus: {e}")

def chat_interface(request):
    """
    Renders the chat interface for user interaction.
    """
    return render(request, 'notes/chat_interface.html')

# Initial load
load_existing_notes()

from .utils import *
from django.core.files.storage import default_storage
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.conf import settings
import json, os, re

def upload_and_search(request):
    """Handles file uploads and search queries."""
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
                    pdf_rel_path = default_storage.save("testing_file.pdf", file)
                    pdf_abs_path = default_storage.path(pdf_rel_path)

                    if not os.path.exists(pdf_abs_path):
                        raise FileNotFoundError(f"Saved file not found: {pdf_abs_path}")

                    try:
                        image_paths = extract_images_from_pdf(pdf_abs_path)
                        for img_path in image_paths:
                            text += " ".join(Obj_Detect_Name(img_path))
                    except Exception as e:
                        print(f"Error processing PDF: {e}")
                        raise
                    finally:
                        default_storage.delete(pdf_abs_path)

                elif file.name.endswith(('.doc', '.docx')):
                    text = doc_reader(file)

                elif file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    text = extract_text_from_image(file)
                    if file.name.lower().endswith('.png'):
                        file = convert_png_to_jpg(file)
                    text += " " + " ".join(Obj_Detect_Name(file))
                print(text)
                requests.post(url, data={'message': text})
                tags = generate_tags(text)
                save_file(file.name, file, tags)
                files = perform_search(query)
            else:
                print("Invalid upload form.")

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
    """Renames a file based on user input."""
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

        current_file_name_without_ext = os.path.splitext(file_instance.file_name)[0]
        if new_name_base == current_file_name_without_ext:
            return JsonResponse({'success': True, 'new_name': file_instance.file_name})

        old_file_path = file_instance.file_content.path
        new_file_path = os.path.join(os.path.dirname(old_file_path), new_file_name)

        if not os.path.exists(old_file_path):
            file_instance.refresh_from_db()
            old_file_path = file_instance.file_content.path
            if not os.path.exists(old_file_path):
                return JsonResponse({'success': False, 'message': f'Original file path does not exist: {old_file_path}'}, status=400)

        new_dir = os.path.dirname(new_file_path)
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)

        if os.path.exists(new_file_path):
            return JsonResponse({'success': False, 'message': 'File with the new name already exists.'}, status=400)

        os.rename(old_file_path, new_file_path)
        file_instance.file_name = new_file_name
        file_instance.file_content.name = os.path.relpath(new_file_path, settings.MEDIA_ROOT)
        file_instance.save()
        file_instance.refresh_from_db()

        if not os.path.exists(file_instance.file_content.path):
            return JsonResponse({'success': False, 'message': 'File not found after renaming.'}, status=500)

        return JsonResponse({'success': True, 'new_name': new_file_name})

    except Exception as e:
        print(f"Error renaming file: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_http_methods(["POST"])
def delete_file(request, file_id):
    """Deletes a specified file."""
    try:
        file_instance = get_object_or_404(File, id=file_id)
        file_path = file_instance.file_content.path

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                return JsonResponse({'success': False, 'message': f"Error deleting file from filesystem: {str(e)}"}, status=500)

        file_instance.delete()
        return JsonResponse({'success': True})

    except Exception as e:
        print(f"Error deleting file: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def download_file(request, file_id):
    """Handles file download requests."""
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
        print(f"Error downloading file: {e}")
        return HttpResponse(f"Error downloading file: {str(e)}", status=500)
