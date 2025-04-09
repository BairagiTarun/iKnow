from django.db import models

class Note(models.Model):
    content = models.TextField()
    file_path = models.TextField(blank=True, null=True)

class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.name

class File(models.Model):
    file_name = models.CharField(max_length=255)
    file_content = models.FileField(upload_to='')
    content_hash = models.CharField(max_length=64)

    def __str__(self):
        return self.file_name

class FileTag(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.file} - {self.tag}"
