from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Profile, TopicUpload, QuizResult
from .forms import ProfileRegisterForm, AdminTopicForm, UserTopicForm
from ui.models import MCQ
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Max
import random
from datetime import timedelta, datetime
from django.db import models
from django.utils import timezone
from .ai import SuggestionEngine

def home_view(request):
    return render(request, "home.html")

def register_view(request):
    if request.method == "POST":
        form = ProfileRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful! Please login.")
            return redirect("login")
        else:
            messages.error(request, "Registration failed. Please check your details.")
    else:
        form = ProfileRegisterForm()
    return render(request, "register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        try:
            user = Profile.objects.get(username=username, password=password)
            # simple session login
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("userdashboard")
        except Profile.DoesNotExist:
            messages.error(request, "Invalid credentials. Please try again.")
            return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")

def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect("home")

def admin_view(request):
    # Check if user is already logged in as admin
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect("admindashboard")
    return render(request, "admin.html")

def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # Use Django's built-in authentication
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            messages.success(request, f"Welcome, Admin {user.username}!")
            return redirect("admindashboard")
        else:
            messages.error(request, "Invalid admin credentials or insufficient privileges!")
            return render(request, "admin.html", {"error": "Invalid admin credentials or insufficient privileges"})
    
    return render(request, "admin.html")

def admin_logout_view(request):
    logout(request)
    messages.success(request, "Admin logged out successfully.")
    return redirect("home")

def dashboard_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please login to access your dashboard.")
        return redirect("login")
    user = Profile.objects.get(id=user_id)
    
    # Get recent quiz results for this user
    recent_results = QuizResult.objects.filter(user=user).order_by('-date_taken')[:5]
    
    # Calculate stats
    total_quizzes = QuizResult.objects.filter(user=user).count()
    if total_quizzes > 0:
        avg_score = QuizResult.objects.filter(user=user).aggregate(
            avg_score=models.Avg('score_percentage')
        )['avg_score'] or 0
        best_score = QuizResult.objects.filter(user=user).aggregate(
            best_score=models.Max('score_percentage')
        )['best_score'] or 0
    else:
        avg_score = 0
        best_score = 0
    
    # Calculate total time spent
    total_time = QuizResult.objects.filter(user=user).aggregate(
        total=models.Sum('time_taken')
    )['total']
    
    if total_time:
        total_minutes = int(total_time.total_seconds() / 60)
        total_time_str = f"{total_minutes}m"
    else:
        total_time_str = "0m"
    
    # AI-based suggestions for next step (multiple suggestions)
    engine = SuggestionEngine()
    suggestions = engine.get_multiple_suggestions(user, max_suggestions=3)

    context = {
        "user": user,
        "recent_results": recent_results,
        "total_quizzes": total_quizzes,
        "avg_score": round(avg_score, 1),
        "best_score": round(best_score, 1),
        "total_time_spent": total_time_str,
        "ai_suggestions": [s.to_dict() for s in suggestions],
    }
    return render(request, "user_dashboard.html", context)

def admin_dashboard_view(request):
    # Check if user is authenticated as superuser
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, "Access denied. Admin authentication required.")
        return redirect("admin")
    
    # Get MCQ topics with question counts for display
    from django.db.models import Count
    mcq_topics = MCQ.objects.values('topic', 'difficulty_level').annotate(
        question_count=Count('id')
    ).order_by('topic', 'difficulty_level')
    
    # Get all data for admin dashboard
    topics = TopicUpload.objects.all().order_by('-id')
    users = Profile.objects.all().order_by('-id')
    
    # Calculate statistics from MCQ table (actual uploaded questions)
    total_topics = MCQ.objects.values('topic').distinct().count()
    total_users = users.count()
    topics_with_pdfs = topics.filter(pdf__isnull=False).count()
    
    # Get difficulty distribution from MCQ table
    easy_topics = MCQ.objects.filter(difficulty_level='Easy').values('topic').distinct().count()
    medium_topics = MCQ.objects.filter(difficulty_level='Medium').values('topic').distinct().count()
    hard_topics = MCQ.objects.filter(difficulty_level='Hard').values('topic').distinct().count()
    
    context = {
        "topics": topics,
        "mcq_topics": mcq_topics,
        "users": users,
        "total_topics": total_topics,
        "total_users": total_users,
        "topics_with_pdfs": topics_with_pdfs,
        "easy_topics": easy_topics,
        "medium_topics": medium_topics,
        "hard_topics": hard_topics,
        "admin_username": request.user.username,
    }
    
    return render(request, "admin_dashboard.html", context)


@csrf_exempt
def quiz_details_view(request, quiz_id):
    """API endpoint to get detailed quiz results for review"""
    try:
        print(f"DEBUG: Fetching quiz details for ID: {quiz_id}")
        print(f"DEBUG: Session data: {dict(request.session)}")
        
        # Get user from session instead of request.user for consistency
        user_id = request.session.get('user_id')
        if not user_id:
            print("DEBUG: No user_id in session")
            # Try to get any quiz result with this ID for debugging
            try:
                any_quiz = QuizResult.objects.get(id=quiz_id)
                print(f"DEBUG: Quiz exists but belongs to user: {any_quiz.user}")
            except QuizResult.DoesNotExist:
                print("DEBUG: Quiz result doesn't exist at all")
            return JsonResponse({'error': 'Not authenticated - no session'}, status=401)
        
        try:
            user = Profile.objects.get(id=user_id)
            print(f"DEBUG: Session user: {user}")
        except Profile.DoesNotExist:
            print(f"DEBUG: User with ID {user_id} not found")
            return JsonResponse({'error': 'User not found'}, status=404)
        
        try:
            quiz_result = QuizResult.objects.get(id=quiz_id, user=user)
            print(f"DEBUG: Found quiz result: {quiz_result}")
        except QuizResult.DoesNotExist:
            print(f"DEBUG: Quiz result {quiz_id} not found for user {user}")
            # Check if quiz exists for any user
            try:
                other_quiz = QuizResult.objects.get(id=quiz_id)
                print(f"DEBUG: Quiz exists but belongs to: {other_quiz.user}")
            except QuizResult.DoesNotExist:
                print("DEBUG: Quiz doesn't exist at all")
            return JsonResponse({'error': 'Quiz not found'}, status=404)
        
        # Get the questions that were in this quiz
        questions_data = []
        if quiz_result.questions_data:
            # Parse the stored questions data
            import json
            print(f"DEBUG: Questions data exists: {quiz_result.questions_data[:100]}...")
            stored_questions = json.loads(quiz_result.questions_data)
            user_answers = json.loads(quiz_result.user_answers) if quiz_result.user_answers else {}
            print(f"DEBUG: Parsed {len(stored_questions)} questions and {len(user_answers)} answers")
            
            for i, q_data in enumerate(stored_questions):
                # Handle case where user_answers might be a list instead of dict
                if isinstance(user_answers, list):
                    user_answer = user_answers[i] if i < len(user_answers) else ''
                else:
                    user_answer = user_answers.get(str(i), '') if user_answers else ''
                
                question_info = {
                    'question': q_data['question'],
                    'option_a': q_data['option_a'],
                    'option_b': q_data['option_b'], 
                    'option_c': q_data['option_c'],
                    'option_d': q_data['option_d'],
                    'correct_answer': q_data['correct_answer'],
                    'user_answer': user_answer
                }
                questions_data.append(question_info)
        else:
            print("DEBUG: No questions_data found in quiz result")
        
        response_data = {
            'topic': quiz_result.topic,
            'difficulty_level': quiz_result.difficulty_level,
            'total_questions': quiz_result.total_questions,
            'correct_answers': quiz_result.correct_answers,
            'score_percentage': quiz_result.score_percentage,
            'time_taken': quiz_result.time_taken.total_seconds() if quiz_result.time_taken else 0,
            'date_taken': quiz_result.date_taken.isoformat(),
            'questions': questions_data
        }
        
        print(f"DEBUG: Returning response with {len(questions_data)} questions")
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"DEBUG: Error in quiz_details_view: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

def upload_topic_view(request):
    if request.method == "POST":
        form = AdminTopicForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a new TopicUpload instance and save it to the database
            topic = TopicUpload.objects.create(
                topic_name=form.cleaned_data['topic_name'],
                sub_topic_name=form.cleaned_data['sub_topic_name'],
                difficulty_level=form.cleaned_data['difficulty_level'],
                pdf=form.cleaned_data['document'] if 'document' in form.cleaned_data else None
            )
            
            # Extract MCQs from the uploaded PDF if it exists
            if 'document' in form.cleaned_data and form.cleaned_data['document']:
                from ui.utils import extract_mcqs_from_pdf
                from ui.models import MCQ
                
                pdf_file = form.cleaned_data['document']
                # Reset file pointer to the beginning before extraction
                pdf_file.seek(0)
                mcqs = extract_mcqs_from_pdf(pdf_file)
                
                # Save extracted MCQs to the database (with duplicate prevention)
                for mcq in mcqs:
                    # Check if question already exists
                    existing = MCQ.objects.filter(
                        topic=form.cleaned_data['topic_name'].strip(),
                        question=mcq["question"].strip(),
                        difficulty_level=form.cleaned_data['difficulty_level']
                    ).first()
                    
                    if not existing:
                        MCQ.objects.create(
                            topic=form.cleaned_data['topic_name'].strip(),
                            sub_topic=form.cleaned_data['sub_topic_name'].strip() if form.cleaned_data['sub_topic_name'] else '',
                            difficulty_level=form.cleaned_data['difficulty_level'],
                            question=mcq["question"].strip(),
                            option_a=mcq["option_a"].strip(),
                            option_b=mcq["option_b"].strip(),
                            option_c=mcq["option_c"].strip(),
                            option_d=mcq["option_d"].strip(),
                            correct_answer=mcq["correct_answer"],
                        )
                
                messages.success(request, f"Topic '{topic.topic_name}' uploaded successfully with {len(mcqs)} MCQs extracted!")
            else:
                messages.success(request, f"Topic '{topic.topic_name}' uploaded successfully!")
            return redirect('admindashboard')
        else:
            messages.error(request, "Upload failed. Please check your details.")
    else:
        form = AdminTopicForm()

    # Get all topics
    topics = TopicUpload.objects.all().order_by('-id')

    # Split counts by difficulty
    easy_topics = TopicUpload.objects.filter(difficulty_level="Easy").count()
    medium_topics = TopicUpload.objects.filter(difficulty_level="Medium").count()
    hard_topics = TopicUpload.objects.filter(difficulty_level="Hard").count()

    # Total topics
    total_topics = topics.count()

    # Get all users
    users = Profile.objects.all()
    total_users = users.count()

    # Topics with PDFs
    topics_with_pdfs = TopicUpload.objects.exclude(pdf="").count()

    return render(request, "admin_dashboard.html", {
        "form": form,
        "topics": topics,
        "easy_topics": easy_topics,
        "medium_topics": medium_topics,
        "hard_topics": hard_topics,
        "total_topics": total_topics,
        "users": users,
        "total_users": total_users,
        "topics_with_pdfs": topics_with_pdfs,
        "admin_username": request.user.username,  # if using auth
    })


def user_topic_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please login to submit topics.")
        return redirect("login")
    
    if request.method == "POST":
        form = UserTopicForm(request.POST)
        if form.is_valid():
            # Create topic without PDF for user submissions
            topic = TopicUpload.objects.create(
                topic_name=form.cleaned_data['topic_name'],
                sub_topic_name=form.cleaned_data['sub_topic_name'],
                difficulty_level=form.cleaned_data['difficulty_level']
            )
            messages.success(request, f"Topic '{topic.topic_name}' submitted successfully!")
            return redirect("userdashboard")
        else:
            messages.error(request, "Submission failed. Please check your details.")
    else:
        form = UserTopicForm()
    
    user = Profile.objects.get(id=user_id)
    return render(request, "user_dashboard.html", {"user": user, "form": form})

def quiz_view(request):
    """Display quiz page with questions"""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please login to take a quiz.")
        return redirect("login")
    
    topic = request.GET.get('topic')
    difficulty = request.GET.get('difficulty')
    num_questions = int(request.GET.get('num_questions', 10))
    
    if not topic or not difficulty:
        messages.error(request, "Please select both topic and difficulty.")
        return redirect("userdashboard")
    
    # Get questions from database
    questions = MCQ.objects.filter(topic=topic, difficulty_level=difficulty)
    
    if questions.count() < num_questions:
        num_questions = questions.count()
    
    if num_questions > 0:
        # Randomly select questions
        question_ids = list(questions.values_list('id', flat=True))
        selected_ids = random.sample(question_ids, num_questions)
        selected_questions = MCQ.objects.filter(id__in=selected_ids)
        
        # Convert to list for JSON serialization
        questions_list = []
        for q in selected_questions:
            questions_list.append({
                'id': q.id,
                'question': q.question,
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d,
                'correct_answer': q.correct_answer
            })
    else:
        questions_list = []
    
    context = {
        'topic': topic,
        'sub_topic': '',
        'difficulty': difficulty,
        'total_questions': len(questions_list),
        'questions': json.dumps(questions_list)
    }
    
    return render(request, 'quiz.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def submit_quiz_result(request):
    """Submit quiz results to database"""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        user = Profile.objects.get(id=user_id)
        
        # Create quiz result with questions and answers data
        quiz_result = QuizResult.objects.create(
            user=user,
            topic=data['topic'],
            sub_topic=data.get('sub_topic', ''),
            difficulty_level=data['difficulty_level'],
            total_questions=data['total_questions'],
            correct_answers=data['correct_answers'],
            score_percentage=data['score_percentage'],
            time_taken=timedelta(seconds=data['time_taken']),
            questions_data=json.dumps(data.get('questions', [])),
            user_answers=json.dumps(data.get('user_answers', {}))
        )
        
        print(f"DEBUG: Saved quiz result with {len(data.get('questions', []))} questions and {len(data.get('user_answers', {}))} answers")
        
        return JsonResponse({'success': True, 'result_id': quiz_result.id})
    
    except Exception as e:
        print(f"DEBUG: Error saving quiz result: {e}")
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def analytics_data_view(request):
    """API endpoint to get analytics data for charts"""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        user = Profile.objects.get(id=user_id)
        
        # Get user's quiz results
        quiz_results = QuizResult.objects.filter(user=user).order_by('date_taken')
        
        # Topic performance data
        topic_performance = quiz_results.values('topic').annotate(
            avg_score=Avg('score_percentage'),
            quiz_count=Count('id')
        ).order_by('-avg_score')[:6]  # Top 6 topics
        
        topic_data = {
            'topics': [item['topic'] for item in topic_performance],
            'scores': [float(item['avg_score']) for item in topic_performance]
        }
        
        
        # Quiz history analytics - topic/subtopic summary
        quiz_history_analytics = quiz_results.values('topic', 'sub_topic').annotate(
            quiz_count=Count('id'),
            avg_score=Avg('score_percentage'),
            best_score=Max('score_percentage'),
            latest_date=Max('date_taken')
        ).order_by('-quiz_count', '-avg_score')
        
        # Format quiz history data
        history_data = []
        for item in quiz_history_analytics:
            history_data.append({
                'topic': item['topic'],
                'sub_topic': item['sub_topic'] or '',
                'quiz_count': item['quiz_count'],
                'avg_score': round(float(item['avg_score']), 1),
                'best_score': round(float(item['best_score']), 1),
                'latest_date': item['latest_date'].strftime('%Y-%m-%d')
            })
        
        # Additional stats for the dashboard
        best_score = quiz_results.aggregate(Max('score_percentage'))['score_percentage__max'] or 0
        total_time = quiz_results.aggregate(
            total=models.Sum('time_taken')
        )['total']
        
        # Format total time
        if total_time:
            total_minutes = int(total_time.total_seconds() / 60)
            total_time_str = f"{total_minutes}m"
        else:
            total_time_str = "0m"
        
        # Include AI suggestions as part of analytics payload for dynamic UI usage
        engine = SuggestionEngine()
        suggestions = engine.get_multiple_suggestions(user, max_suggestions=3)

        response_data = {
            'topic_performance': topic_data,
            'quiz_history_analytics': history_data,
            'best_score': float(best_score),
            'total_time_spent': total_time_str,
            'ai_suggestions': [s.to_dict() for s in suggestions],
        }

        return JsonResponse(response_data)
        
    except Profile.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        print(f"DEBUG: Error in analytics_data_view: {e}")
        return JsonResponse({'error': str(e)}, status=500)
