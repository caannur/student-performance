import os
import numpy as np

def predict_student_performance(avg_grade, attendance_rate, participation_level):
    """
    Предсказывает итоговую оценку студента на основе средней оценки, 
    посещаемости и уровня участия.
    
    Параметры:
    avg_grade (float): средний балл студента (0-100)
    attendance_rate (float): процент посещаемости (0-100)
    participation_level (int): уровень участия (0, 1, 2)
    
    Возвращает:
    tuple: (predicted_score, confidence)
    """
    # Простая формула для прогнозирования
    predicted_score = 0.6 * avg_grade + 0.3 * attendance_rate + 5 * participation_level
    predicted_score = min(100, max(0, predicted_score))  # Обрезание до [0, 100]
    
    # Уверенность - фиксированное значение для заглушки
    confidence = 0.8
    
    print(f"Предсказание на основе: средний балл={avg_grade}, посещаемость={attendance_rate}, участие={participation_level}")
    print(f"Результат: оценка={predicted_score:.1f}, уверенность={confidence:.2f}")
    
    return predicted_score, confidence
