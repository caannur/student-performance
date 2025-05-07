from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('notifications/', views.notifications, name='notifications'),
    path('support/', views.support, name='support'),
    path('settings/', views.settings, name='settings'),
    
    # Маршруты для администраторов
    path('admin/courses/', views.admin_courses, name='admin_courses'),
    path('admin/students/', views.admin_students, name='admin_students'),
    path('admin/run-predictions/', views.run_predictions, name='run_predictions'),
    path('admin/courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('admin/students/edit/', views.edit_student, name='edit_student'),   
    # Новые маршруты для работы с курсами, оценками и посещаемостью
    path('course/<int:course_id>/', views.course_details, name='course_details'),
    path('course/<int:course_id>/add-assignment/', views.add_assignment, name='add_assignment'),
    path('assignment/<int:assignment_id>/student/<int:student_id>/add-grade/', views.add_grade, name='add_grade'),
    path('course/<int:course_id>/attendance/', views.record_attendance, name='record_attendance'),
    path('course/<int:course_id>/participation/', views.record_participation, name='record_participation'),
    path('student/<int:student_id>/', views.student_details, name='student_details'),
    
]