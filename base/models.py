from django.db import models

# base/models.py
class Profile(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    contact = models.CharField(max_length=15, default="0000000000")
    gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
        default="Other"
    )

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username

class TopicUpload(models.Model):
    topic_name = models.CharField(max_length=100)
    sub_topic_name = models.CharField(max_length=100, blank=True, null=True)
    difficulty_level = models.CharField(
        max_length=50,
        choices=[("Easy", "Easy"), ("Medium", "Medium"), ("Hard", "Hard")],
        default="Easy",
    )
    pdf = models.FileField(upload_to="pdfs/", blank=True, null=True)

    def __str__(self):
        return f"{self.topic_name} ({self.difficulty_level})"

class QuizResult(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    topic = models.CharField(max_length=100)
    sub_topic = models.CharField(max_length=100, blank=True, null=True)
    difficulty_level = models.CharField(max_length=50)
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    score_percentage = models.FloatField()
    time_taken = models.DurationField(blank=True, null=True)
    date_taken = models.DateTimeField(auto_now_add=True)
    questions_data = models.TextField(blank=True, null=True)  # Store quiz questions as JSON
    user_answers = models.TextField(blank=True, null=True)    # Store user answers as JSON

    class Meta:
        db_table = 'quiz_results'
        ordering = ['-date_taken']

    def __str__(self):
        return f"{self.user.username} - {self.topic} ({self.score_percentage}%)"
