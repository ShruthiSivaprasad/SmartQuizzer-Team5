from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.contrib import messages
from .utils import extract_mcqs_from_pdf
from .models import MCQ
import json
import random


def home(request):
    return render(request, "home.html")


def user_dashboard(request):
    """Render the user dashboard for quiz generation"""
    return render(request, "user_dashboard.html")


def upload_mcq(request):
    if request.method == "POST" and request.FILES.get("pdf"):
        pdf_file = request.FILES["pdf"]
        topic = request.POST.get("topic", "")
        sub_topic = request.POST.get("sub_topic", "")
        difficulty_level = request.POST.get("difficulty_level", "Medium")
        
        mcqs = extract_mcqs_from_pdf(pdf_file)
        print(f"DEBUG: Extracted {len(mcqs)} MCQs from PDF")

        saved_count = 0
        for mcq in mcqs:
            # Check if question already exists to prevent duplicates
            existing = MCQ.objects.filter(
                topic=topic.strip(),
                question=mcq["question"].strip(),
                difficulty_level=difficulty_level
            ).first()
            
            if not existing:
                try:
                    MCQ.objects.create(
                        topic=topic.strip(),
                        sub_topic=sub_topic.strip() if sub_topic else '',
                        difficulty_level=difficulty_level,
                        question=mcq["question"].strip(),
                        option_a=mcq["option_a"].strip(),
                        option_b=mcq["option_b"].strip(),
                        option_c=mcq["option_c"].strip(),
                        option_d=mcq["option_d"].strip(),
                        correct_answer=mcq["correct_answer"],
                    )
                    saved_count += 1
                    print(f"DEBUG: Saved question {saved_count}: {mcq['question'][:50]}...")
                except Exception as e:
                    print(f"DEBUG: Failed to save question: {e}")
            else:
                print(f"DEBUG: Duplicate question skipped: {mcq['question'][:50]}...")
        
        print(f"DEBUG: Total questions saved: {saved_count} out of {len(mcqs)}")
        messages.success(request, f"PDF uploaded successfully! {saved_count} questions added to database.")
        return redirect('/admindashboard/')

    return render(request, "home.html")


def get_questions(request):
    """API endpoint to get questions for a specific topic"""
    topic = request.GET.get('topic', '')
    
    if not topic:
        return JsonResponse([], safe=False)
    
    # Query MCQs with the given topic
    questions = MCQ.objects.filter(topic=topic)
    
    # Convert queryset to list of dictionaries
    questions_list = [{
        'id': q.id,
        'question': q.question,
        'option_a': q.option_a,
        'option_b': q.option_b,
        'option_c': q.option_c,
        'option_d': q.option_d,
        'correct_answer': q.correct_answer,
        'difficulty_level': q.difficulty_level,
        'sub_topic': q.sub_topic
    } for q in questions]
    
    return JsonResponse(questions_list, safe=False)


def get_topics(request):
    """API endpoint to get all available topics"""
    # Get distinct topics from the MCQ model
    topics = MCQ.objects.values_list('topic', flat=True).distinct().order_by('topic')
    # Filter out empty topics and convert to set to remove duplicates, then back to sorted list
    topics_set = set(topic.strip() for topic in topics if topic and topic.strip())
    topics_list = sorted(list(topics_set))
    return JsonResponse(topics_list, safe=False)


def generate_quiz(request):
    """API endpoint to generate a quiz based on topic and difficulty"""
    topic = request.GET.get('topic', '')
    difficulty_level = request.GET.get('difficulty_level', '')
    num_questions = int(request.GET.get('num_questions', 5))
    
    # Build the filter query
    query = Q(topic=topic)
    if difficulty_level:
        query &= Q(difficulty_level=difficulty_level)
    
    # Get questions matching the criteria
    questions = MCQ.objects.filter(query)
    
    # If we have more questions than requested, randomly select the required number
    if questions.count() > num_questions:
        question_ids = list(questions.values_list('id', flat=True))
        selected_ids = random.sample(question_ids, num_questions)
        questions = MCQ.objects.filter(id__in=selected_ids)
    
    # Convert queryset to list of dictionaries
    questions_list = [{
        'id': q.id,
        'question': q.question,
        'option_a': q.option_a,
        'option_b': q.option_b,
        'option_c': q.option_c,
        'option_d': q.option_d,
        'correct_answer': q.correct_answer,
        'difficulty_level': q.difficulty_level,
        'sub_topic': q.sub_topic
    } for q in questions]
    
    return JsonResponse(questions_list, safe=False)
