# notes/models.py

from django.db import models

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Note(models.Model):
    content = models.TextField()  # To store the content of the note in the database
    file_path = models.CharField(max_length=255)  # To store the file path where the note is saved
    tags = models.ManyToManyField(Tag, related_name='notes')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note {self.id} - {self.created_at.strftime('%Y-%m-%d')}"
