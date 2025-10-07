from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', views.admin_view, name='admin'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),
    path('userdashboard/', views.dashboard_view, name='userdashboard'),
    path('admindashboard/', views.admin_dashboard_view, name='admindashboard'),
    path('upload-topic/', views.upload_topic_view, name='upload_topic'),
    path('user-topic/', views.user_topic_view, name='user_topic'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('submit-quiz-result/', views.submit_quiz_result, name='submit_quiz_result'),
    path('quiz-details/<int:quiz_id>/', views.quiz_details_view, name='quiz_details'),
    path('analytics-data/', views.analytics_data_view, name='analytics_data'),
]
