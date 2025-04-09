# urls.py
from django.urls import path
from . import views  # Import your views

urlpatterns = [
    path('', views.chat_interface, name='chat_interface'),  # Main interface
    path('search/', views.search_notes_view, name='search_notes'),
    path('save/', views.save_note_view, name='save_note'),
    path('save_response/', views.save_plain_text_response_view, name='save_plain_text_response'),  # Ensure this is correct
    path('upload/', views.upload_and_search, name='upload'),  # For uploading files and searching
    path('search/', views.upload_and_search, name='search'),  # For searching files
    path('download/<int:file_id>/', views.download_file, name='download_file'),  # For downloading files
    path('delete/<int:file_id>/', views.delete_file, name='delete_file'),  # For deleting files
    path('rename/<int:file_id>/', views.rename_file, name='rename_file'),  # For renaming files
    path('files/', views.upload_and_search, name='files'),  # To fetch the list of files

]
