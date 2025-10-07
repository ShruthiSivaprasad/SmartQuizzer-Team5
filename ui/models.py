from django.db import models

# Create your models here.

class MCQ(models.Model):
    id = models.BigAutoField(primary_key=True)
    topic = models.CharField(max_length=100, blank=True, null=True)
    sub_topic = models.CharField(max_length=150, blank=True, null=True)
    difficulty_level = models.CharField(
        max_length=20, 
        choices=[('Easy','Easy'),('Medium','Medium'),('Hard','Hard')],
        default='Medium'
    )
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(
        max_length=1,
        choices=[
            ('A', 'Option A'),
            ('B', 'Option B'),
            ('C', 'Option C'),
            ('D', 'Option D'),
        ]
    )

    class Meta:
        indexes = [
            models.Index(fields=['topic', 'sub_topic', 'difficulty_level'])
        ]

    def __str__(self):
        return f"{self.topic or 'Untitled'} - {self.question[:50]}..."

