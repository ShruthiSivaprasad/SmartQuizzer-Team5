from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='ui_home'),
    path('upload/', views.upload_mcq, name='upload_mcq'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('api/questions/', views.get_questions, name='get_questions'),
    path('api/topics/', views.get_topics, name='get_topics'),
    path('api/quiz/', views.generate_quiz, name='generate_quiz'),
]




