from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count, Sum, F, ExpressionWrapper, FloatField
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from .models import Course, Assignment, Grade, Attendance, Participation, Prediction
from .forms import CourseForm, AssignmentForm, GradeForm, AttendanceForm, ParticipationForm, PasswordChangeForm
from accounts.models import User
from ml_model.predictor import predict_student_performance
import datetime

@login_required
def dashboard(request):
    if request.user.role == 'student':
        # Данные для студентов
        courses = request.user.enrolled_courses.all()
        
        # Получаем оценки с деталями о заданиях и курсах
        recent_grades = Grade.objects.filter(student=request.user).select_related('assignment', 'assignment__course').order_by('-submitted_at')[:5]
        
        # Расчет посещаемости для каждого курса
        attendance_rates = {}
        for course in courses:
            total_classes = Attendance.objects.filter(course=course, student=request.user).count()
            if total_classes > 0:
                present_count = Attendance.objects.filter(course=course, student=request.user, is_present=True).count()
                attendance_rates[course.name] = (present_count / total_classes) * 100
            else:
                attendance_rates[course.name] = 0
        
        # Получаем последние прогнозы
        predictions = Prediction.objects.filter(student=request.user)
        predictions_data = {p.course.name: p.predicted_score for p in predictions}
        
        # Расчет средней оценки студента
        avg_grade = Grade.objects.filter(student=request.user).aggregate(avg_score=Avg('score'))
        
        context = {
            'courses': courses,
            'recent_grades': recent_grades,
            'attendance_rates': attendance_rates,
            'predictions': predictions_data,
            'avg_grade': avg_grade['avg_score'] if avg_grade['avg_score'] else 0,
        }
        return render(request, 'dashboard/student_dashboard.html', context)
    
    elif request.user.role == 'admin':
        # Данные для администраторов
        total_students = User.objects.filter(role='student').count()
        # Удаляем подсчет преподавателей
        # total_teachers = User.objects.filter(role='teacher').count() if hasattr(User, 'teacher') else 0
        total_courses = Course.objects.count()
        
        # Получаем последние прогнозы с информацией о студентах и курсах
        recent_predictions = Prediction.objects.all().select_related('student', 'course').order_by('-created_at')[:10]
        
        # Группировка прогнозов по оценочным категориям для графика
        prediction_stats = {
            '90-100': Prediction.objects.filter(predicted_score__gte=90).count(),
            '80-89': Prediction.objects.filter(predicted_score__gte=80, predicted_score__lt=90).count(),
            '70-79': Prediction.objects.filter(predicted_score__gte=70, predicted_score__lt=80).count(),
            '60-69': Prediction.objects.filter(predicted_score__gte=60, predicted_score__lt=70).count(),
            '<60': Prediction.objects.filter(predicted_score__lt=60).count(),
        }
        
        context = {
            'total_students': total_students,
            # Удаляем total_teachers из контекста
            'total_courses': total_courses,
            'recent_predictions': recent_predictions,
            'prediction_stats': prediction_stats,
        }
        return render(request, 'dashboard/admin_dashboard.html', context)
    
    # По умолчанию возвращаем обычную панель управления
    return render(request, 'dashboard/dashboard.html')

@login_required
def notifications(request):
    # Получаем недавние оценки для отображения в уведомлениях
    recent_grades = Grade.objects.filter(student=request.user).select_related('assignment', 'assignment__course').order_by('-submitted_at')[:3]
    
    # Проверяем низкую посещаемость
    courses_with_low_attendance = []
    for course in request.user.enrolled_courses.all():
        total_classes = Attendance.objects.filter(course=course, student=request.user).count()
        if total_classes > 0:
            present_count = Attendance.objects.filter(course=course, student=request.user, is_present=True).count()
            attendance_rate = (present_count / total_classes) * 100
            if attendance_rate < 75:
                courses_with_low_attendance.append(course)
    
    # Проверяем новые задания
    # Новые задания - созданные за последние 7 дней
    new_assignments = Assignment.objects.filter(
        course__in=request.user.enrolled_courses.all(), 
        created_at__gte=timezone.now() - datetime.timedelta(days=7)
    ).select_related('course')
    
    # Получаем недавние прогнозы
    recent_predictions = Prediction.objects.filter(student=request.user).select_related('course').order_by('-created_at')[:3]
    
    context = {
        'recent_grades': recent_grades,
        'courses_with_low_attendance': courses_with_low_attendance,
        'new_assignments': new_assignments,
        'recent_predictions': recent_predictions,
        'courses': request.user.enrolled_courses.all(),
    }
    
    return render(request, 'dashboard/notifications.html', context)

@login_required
def support(request):
    context = {
        'courses': request.user.enrolled_courses.all() if request.user.role == 'student' else Course.objects.all(),
    }
    return render(request, 'dashboard/support.html', context)

@login_required
def settings(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data.get('current_password')
            new_password = form.cleaned_data.get('new_password')
            
            # Проверяем текущий пароль
            if request.user.check_password(current_password):
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Пароль успешно изменен. Пожалуйста, войдите снова.')
                return redirect('login')
            else:
                messages.error(request, 'Текущий пароль неверен.')
    else:
        form = PasswordChangeForm()
    
    context = {
        'form': form,
    }
    return render(request, 'dashboard/settings.html', context)

@staff_member_required
def admin_courses(request):
    courses = Course.objects.all()
    form = CourseForm()
    
    # Добавить список студентов
    students = User.objects.filter(role='student')
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_courses')
    
    context = {
        'courses': courses,
        'form': form,
        'students': students,  # Добавляем студентов в контекст
    }
    return render(request, 'dashboard/admin_courses.html', context)

@staff_member_required
def admin_students(request):
    students = User.objects.filter(role='student').annotate(
        course_count=Count('enrolled_courses'),
        avg_score=ExpressionWrapper(
            Avg('grades__score'), 
            output_field=FloatField()
        )
    )
    
    # Получение списка всех курсов для фильтрации
    courses = Course.objects.all()
    
    context = {
        'students': students,
        'courses': courses,
    }
    return render(request, 'dashboard/admin_students.html', context)

@staff_member_required
def run_predictions(request):
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        if course_id:
            course = get_object_or_404(Course, id=course_id)
            
            # Обновляем прогнозы для выбранного курса
            for student in course.students.all():
                # Получение данных для прогнозирования
                grades = Grade.objects.filter(student=student, assignment__course=course)
                avg_grade = grades.aggregate(Avg('score'))['score__avg'] or 0
                
                attendance = Attendance.objects.filter(student=student, course=course)
                attendance_rate = (attendance.filter(is_present=True).count() / attendance.count()) * 100 if attendance.count() > 0 else 0
                
                participation = Participation.objects.filter(student=student, course=course)
                avg_participation = participation.aggregate(Avg('level'))['level__avg'] or 0
                
                # Вызов функции прогнозирования
                prediction, confidence = predict_student_performance(avg_grade, attendance_rate, avg_participation)
                
                # Сохранение результата
                Prediction.objects.update_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'predicted_score': prediction,
                        'confidence': confidence,
                    }
                )
            
            messages.success(request, f'Прогнозы для курса "{course.name}" успешно обновлены.')
        else:
            # Если не указан конкретный курс, обновляем прогнозы для всех курсов
            for course in Course.objects.all():
                for student in course.students.all():
                    # Получение данных для прогнозирования
                    grades = Grade.objects.filter(student=student, assignment__course=course)
                    avg_grade = grades.aggregate(Avg('score'))['score__avg'] or 0
                    
                    attendance = Attendance.objects.filter(student=student, course=course)
                    attendance_rate = (attendance.filter(is_present=True).count() / attendance.count()) * 100 if attendance.count() > 0 else 0
                    
                    participation = Participation.objects.filter(student=student, course=course)
                    avg_participation = participation.aggregate(Avg('level'))['level__avg'] or 0
                    
                    # Вызов функции прогнозирования
                    prediction, confidence = predict_student_performance(avg_grade, attendance_rate, avg_participation)
                    
                    # Сохранение результата
                    Prediction.objects.update_or_create(
                        student=student,
                        course=course,
                        defaults={
                            'predicted_score': prediction,
                            'confidence': confidence,
                        }
                    )
            
            messages.success(request, 'Прогнозы для всех курсов успешно обновлены.')
    
    # После обработки перенаправляем на страницу курсов
    referrer = request.META.get('HTTP_REFERER')
    if referrer and 'admin_courses' in referrer:
        return redirect('admin_courses')
    else:
        return redirect('dashboard')

# Новые представления для работы с оценками, заданиями и посещаемостью

@staff_member_required
def course_details(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    assignments = Assignment.objects.filter(course=course).order_by('due_date')
    students = course.students.all()
    
    context = {
        'course': course,
        'assignments': assignments,
        'students': students,
    }
    return render(request, 'dashboard/course_details.html', context)

@staff_member_required
def add_assignment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        # Создаем форму с данными POST, но не включаем поле course
        form = AssignmentForm(request.POST)
        
        if form.is_valid():
            # Создаем объект задания, но не сохраняем его в базу данных
            assignment = form.save(commit=False)
            # Устанавливаем курс
            assignment.course = course
            # Сохраняем задание
            assignment.save()
            messages.success(request, 'Задание успешно добавлено.')
            return redirect('course_details', course_id=course.id)
    else:
        # При GET-запросе просто инициализируем форму
        form = AssignmentForm()
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'dashboard/add_assignment.html', context)

@staff_member_required
def add_grade(request, assignment_id, student_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = get_object_or_404(User, id=student_id)
    
    # Проверка, существует ли уже оценка
    existing_grade = Grade.objects.filter(student=student, assignment=assignment).first()
    
    if request.method == 'POST':
        print("POST данные:", request.POST)  # для отладки
        
        # Если оценка уже существует, обновляем её, иначе создаём новую
        if existing_grade:
            form = GradeForm(request.POST, instance=existing_grade)
        else:
            form = GradeForm(request.POST)
        
        if form.is_valid():
            print("Форма валидна")  # для отладки
            grade = form.save(commit=False)
            grade.student = student
            grade.assignment = assignment
            grade.save()
            print("Оценка сохранена:", grade.id, grade.score)  # для отладки
            messages.success(request, 'Оценка успешно сохранена.')
            return redirect('course_details', course_id=assignment.course.id)
        else:
            print("Ошибки формы:", form.errors)  # для отладки
            messages.error(request, 'Ошибка при сохранении оценки. Пожалуйста, проверьте введенные данные.')
    else:
        # При GET-запросе инициализируем форму
        if existing_grade:
            form = GradeForm(instance=existing_grade)
        else:
            # Используем начальные значения
            form = GradeForm(initial={'student': student, 'assignment': assignment})
    
    context = {
        'form': form,
        'student': student,
        'assignment': assignment,
    }
    return render(request, 'dashboard/add_grade.html', context)

@staff_member_required
def record_attendance(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    students = course.students.all()
    
    if request.method == 'POST':
        date = request.POST.get('date')
        
        for student in students:
            is_present = request.POST.get(f'student_{student.id}') == 'on'
            
            # Обновить или создать запись о посещаемости
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                course=course,
                date=date,
                defaults={'is_present': is_present}
            )
        
        messages.success(request, 'Данные о посещаемости успешно сохранены.')
        return redirect('course_details', course_id=course.id)
    
    context = {
        'course': course,
        'students': students,
        'today': timezone.now().date(),
    }
    return render(request, 'dashboard/record_attendance.html', context)

@staff_member_required
def record_participation(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    students = course.students.all()
    
    if request.method == 'POST':
        date = request.POST.get('date')
        
        for student in students:
            level = request.POST.get(f'level_{student.id}')
            notes = request.POST.get(f'notes_{student.id}', '')
            
            if level:
                # Обновить или создать запись об участии
                participation, created = Participation.objects.update_or_create(
                    student=student,
                    course=course,
                    date=date,
                    defaults={
                        'level': int(level),
                        'notes': notes
                    }
                )
        
        messages.success(request, 'Данные об участии успешно сохранены.')
        return redirect('course_details', course_id=course.id)
    
    context = {
        'course': course,
        'students': students,
        'today': timezone.now().date(),
        'participation_levels': Participation.PARTICIPATION_CHOICES,
    }
    return render(request, 'dashboard/record_participation.html', context)

@staff_member_required
def student_details(request, student_id):
    student = get_object_or_404(User, id=student_id)
    courses = student.enrolled_courses.all()
    grades = Grade.objects.filter(student=student).select_related('assignment', 'assignment__course')
    
    # Расчет средней оценки по каждому курсу
    course_averages = {}
    for course in courses:
        course_grades = grades.filter(assignment__course=course)
        avg = course_grades.aggregate(Avg('score'))['score__avg']
        course_averages[course.id] = avg if avg else 0
    
    # Данные о посещаемости
    attendance_data = {}
    for course in courses:
        attendance = Attendance.objects.filter(student=student, course=course)
        total = attendance.count()
        present = attendance.filter(is_present=True).count()
        attendance_data[course.id] = {
            'total': total,
            'present': present,
            'rate': (present / total * 100) if total > 0 else 0
        }
    
    # Последние прогнозы
    predictions = Prediction.objects.filter(student=student).select_related('course')
    
    context = {
        'student': student,
        'courses': courses,
        'grades': grades,
        'course_averages': course_averages,
        'attendance_data': attendance_data,
        'predictions': predictions,
    }
    return render(request, 'dashboard/student_details.html', context)

@staff_member_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
        messages.success(request, f'Курс "{course.name}" успешно удален.')
    return redirect('admin_courses')

@staff_member_required
def edit_student(request, student_id=None):
    # Если ID студента не передан в URL, пытаемся получить его из POST-данных
    if student_id is None and request.method == 'POST':
        student_id = request.POST.get('student_id')
    
    # Если метод GET и ID не передан, перенаправляем на список студентов
    if request.method == 'GET' and student_id is None:
        return redirect('admin_students')
    
    # Получаем студента или возвращаем 404
    student = get_object_or_404(User, id=student_id, role='student')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        student_number = request.POST.get('student_number', '').strip()
        course_ids = request.POST.getlist('courses')
        
        # Обновление данных студента
        if ' ' in full_name:
            first_name, last_name = full_name.split(' ', 1)
        else:
            first_name, last_name = full_name, ''
        
        student.first_name = first_name
        student.last_name = last_name
        student.email = email
        student.student_number = student_number
        student.save()
        
        # Обновление записи на курсы
        if course_ids:
            student.enrolled_courses.clear()
            for course_id in course_ids:
                try:
                    course = Course.objects.get(id=course_id)
                    student.enrolled_courses.add(course)
                except Course.DoesNotExist:
                    continue
        
        messages.success(request, f'Данные студента "{student.get_full_name()}" успешно обновлены.')
        return redirect('admin_students')
    
    # Для GET-запроса возвращаем страницу редактирования
    context = {
        'student': student,
        'courses': Course.objects.all(),
    }
    return render(request, 'dashboard/edit_student.html', context)