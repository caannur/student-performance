from django.db import models
from accounts.models import User

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    description = models.TextField()
    # Теперь администратор будет управлять курсами
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True, limit_choices_to={'role': 'student'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Assignment(models.Model):
    title = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    description = models.TextField()
    due_date = models.DateTimeField()
    max_points = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Grade(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grades')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='grades')
    score = models.FloatField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'assignment']
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title} - {self.score}"

class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    is_present = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['student', 'course', 'date']
    
    def __str__(self):
        status = "Присутствовал" if self.is_present else "Отсутствовал"
        return f"{self.student.username} - {self.course.name} - {self.date} - {status}"

class Participation(models.Model):
    PARTICIPATION_CHOICES = (
        (0, 'Низкая'),
        (1, 'Средняя'),
        (2, 'Высокая'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='participations')
    date = models.DateField()
    level = models.IntegerField(choices=PARTICIPATION_CHOICES, default=1)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'course', 'date']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.name} - {self.date} - {self.get_level_display()}"

class Prediction(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='predictions')
    predicted_score = models.FloatField()
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'course']
        get_latest_by = 'created_at'
    
    def __str__(self):
        return f"{self.student.username} - {self.course.name} - {self.predicted_score:.2f}"