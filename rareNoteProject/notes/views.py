import os
import re
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from dotenv import load_dotenv
import google.generativeai as genai
from .models import Note, Tag
from sklearn.feature_extraction.text import TfidfVectorizer
from django.views.decorators.csrf import csrf_exempt
from sentence_transformers import SentenceTransformer, util
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification, AutoModelForQuestionAnswering

# Load environment variables
load_dotenv()

# Configure Gemini AI API
gemini_api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=gemini_api_key)

# Initialize Semantic Search Model
class SemanticSearchModel:
    def __init__(self):
        # Load pre-trained Sentence-BERT model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeddings = []
        self.notes = []

    def encode_corpus(self, notes):
        """
        Encode the corpus of notes to semantic vectors.
        """
        self.notes = notes
        self.embeddings = self.model.encode(notes, convert_to_tensor=True)

    def search(self, query, top_k=5):
        """
        Search the most relevant notes based on a query.
        """
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        # Calculate cosine similarity between query and stored notes
        cosine_scores = util.pytorch_cos_sim(query_embedding, self.embeddings)[0]
        # Get the top k results
        top_results = torch.topk(cosine_scores, k=top_k)
        results = [(self.notes[idx], score.item()) for idx, score in zip(top_results.indices, top_results.values)]
        return results

# Initialize the Semantic Search Model
search_model = SemanticSearchModel()

# Initialize QA models
qa_pipeline_distilbert = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")
model_name_roberta = "deepset/roberta-base-squad2"
qa_pipeline_roberta = pipeline('question-answering', model=model_name_roberta, tokenizer=model_name_roberta)

# Initialize the NER model
ner_pipeline = pipeline("ner", model="dslim/bert-base-NER")

def chat_interface(request):
    """
    Renders the chat interface template.
    """
    return render(request, 'notes/chat_interface.html')

@csrf_exempt
def search_notes_view(request):
    """
    Handles searching for relevant notes and providing answers based on user queries.
    """
    if request.method == 'POST':
        query = request.POST.get('message', '').strip()
        if not query:
            return JsonResponse({'response': 'Query cannot be empty.'})

        # Use the semantic search model to find the most relevant notes
        results = search_model.search(query)

        if results:
            # Prepare a context by combining relevant notes
            relevant_notes = " ".join([note for note, score in results])
            
            # Check for entity and relevant information using NER
            entities = ner_pipeline(relevant_notes)
            filtered_entities = [entity['word'] for entity in entities if 'API' in entity['word'] or 'key' in entity['word']]

            # Search for specific information using keywords and context
            for entity in filtered_entities:
                if query.lower() in entity.lower():
                    return JsonResponse({'response': entity})

            # Use the Roberta-based QA pipeline to get the answer from the combined context
            answer_roberta = qa_pipeline_roberta(question=query, context=relevant_notes)

            if answer_roberta and answer_roberta['score'] > 0.3:  # Only return answers with a reasonable confidence
                return JsonResponse({'response': answer_roberta['answer']})

            # If Roberta fails, fallback to DistilBERT QA model
            answer_distilbert = qa_pipeline_distilbert(question=query, context=relevant_notes)
            
            if answer_distilbert and answer_distilbert['score'] > 0.3:
                return JsonResponse({'response': answer_distilbert['answer']})

        return JsonResponse({'response': 'No relevant answer found in the notes.'})

    return JsonResponse({'response': 'Invalid request method.'}, status=400)

@csrf_exempt
def save_note_view(request):
    """
    Saves a new note into the database and updates the search model.
    """
    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        
        if content == '':
            return JsonResponse({'response': 'Note content cannot be empty.'})
        
        # Save the note to the database
        note = Note.objects.create(content=content)
        
        # Update the model with new content
        all_notes = list(Note.objects.all().values_list('content', flat=True))
        search_model.encode_corpus(all_notes)

        return JsonResponse({'response': 'Note saved successfully.'})

    return JsonResponse({'response': 'Invalid request method.'}, status=400)

def save_note_to_file(content):
    """
    Saves a note to a file in the specified directory.
    """
    notes_directory = os.path.join(settings.NOTES_DIR)
    if not os.path.exists(notes_directory):
        os.makedirs(notes_directory)

    date_str = timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_name = f"note_{date_str}.txt"
    file_path = os.path.join(notes_directory, file_name)

    try:
        with open(file_path, 'w') as file:
            file.write(content)
    except IOError as e:
        print(f"An error occurred while saving the file: {e}")

    return file_path

def extract_plain_text(response):
    """
    Extracts plain text from the Gemini response, removing any formatting, tags, or special characters.
    """
    plain_text = re.sub(r'[#*>\[\]\(\)_`]', '', response)  # Remove Markdown special characters
    plain_text = re.sub(r'<[^>]+>', '', plain_text)  # Remove HTML tags if any
    plain_text = re.sub(r'\s+', ' ', plain_text)  # Normalize whitespace
    return plain_text.strip()

def extract_tags(content):
    """
    Extracts the top 90 relevant tags from the content using TF-IDF.
    """
    max_tag_length = 255  # Ensure tags are within the length limit for the database
    
    # Initialize the TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(max_features=90, stop_words='english')
    
    # Fit and transform the content to extract TF-IDF features
    X = vectorizer.fit_transform([content])
    
    # Extract feature names (words)
    feature_names = vectorizer.get_feature_names_out()
    
    # Extract the TF-IDF scores for the words
    tfidf_scores = X.toarray()[0]
    
    # Combine the words and their TF-IDF scores
    word_scores = list(zip(feature_names, tfidf_scores))
    
    # Sort the words by their TF-IDF scores in descending order
    sorted_word_scores = sorted(word_scores, key=lambda x: x[1], reverse=True)
    
    # Get the top 90 words with the highest TF-IDF scores
    top_tags = [word for word, score in sorted_word_scores if len(word) <= max_tag_length][:90]

    # Fetch or create tags in the database
    tags = []
    for tag in top_tags:
        tag_obj, created = Tag.objects.get_or_create(name=tag)
        tags.append(tag_obj)
    
    return tags

@csrf_exempt
def save_plain_text_response_view(request):
    """
    Saves a plain text response from Gemini into the database as a Note.
    """
    if request.method == 'POST':
        # Get the plain text message from the request
        content = request.POST.get('message', '').strip()
        
        if content == '':
            return JsonResponse({'response': 'Note content cannot be empty.'})
        
        # Save note content to a file (if needed)
        file_path = save_note_to_file(content)

        # Create a new Note object in the database
        note = Note.objects.create(content=content, file_path=file_path)

        return JsonResponse({'response': 'Note saved successfully.'})

    return JsonResponse({'response': 'Invalid request method.'}, status=400)

def query_gemini_view(request):
    """
    Queries Gemini AI with the given input and returns the response.
    """
    if request.method == 'POST':
        query = request.POST.get('message', '').strip()
        response = query_gemini(query)
        return JsonResponse({'response': response})

    return JsonResponse({'response': 'Invalid request method.'}, status=400)

def query_gemini(query):
    """
    Sends a query to the Gemini AI model and retrieves the response.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        chat = model.start_chat(history=[])
        response = chat.send_message(query)

        # Structure the response to make it more readable and formatted
        formatted_response = format_response(response.text)

        return formatted_response
    except Exception as e:
        print(f"An error occurred while querying Gemini: {e}")
        return "<div class='error-message'>Error processing query due to network issues.</div>"

def format_response(response_text):
    """
    Format the response text to make it more structured and readable.
    """
    formatted_text = response_text.replace("\n", "<br><br>")
    formatted_text = f"<div class='gemini-response'><p>{formatted_text}</p></div>"
    
    return formatted_text

def load_existing_notes():
    """
    Load existing notes from the database and encode them.
    """
    notes = list(Note.objects.all().values_list('content', flat=True))
    search_model.encode_corpus(notes)

# Load notes when the server starts
load_existing_notes()