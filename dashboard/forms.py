from django import forms
from .models import Course, Assignment, Grade, Attendance, Participation

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'code', 'description', 'students']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'max_points']
        # Удаляем поле course из формы, так как будем устанавливать его программно
        # fields = ['title', 'course', 'description', 'due_date', 'max_points']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['score']  # Только поле score, student и assignment будут заполняться программно

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'course', 'date', 'is_present']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class ParticipationForm(forms.ModelForm):
    class Meta:
        model = Participation
        fields = ['student', 'course', 'date', 'level', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Пароли не совпадают.")
        
        return cleaned_data