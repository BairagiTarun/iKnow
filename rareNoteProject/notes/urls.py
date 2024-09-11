# urls.py
from django.urls import path
from . import views  # Import your views

urlpatterns = [
    path('', views.chat_interface, name='chat_interface'),  # Main interface
    path('search/', views.search_notes_view, name='search_notes'),
    path('save/', views.save_note_view, name='save_note'),
    path('gemini/', views.query_gemini_view, name='gemini_query'),
    path('save_response/', views.save_plain_text_response_view, name='save_plain_text_response'),  # Ensure this is correct
]
