import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os

def train_models():
    """
    Обучает модели для прогнозирования успеваемости студентов и сохраняет их
    """
    # Загрузка подготовленных данных (или генерация демо-данных, если файл не существует)
    try:
        data = pd.read_csv('data/prepared_data.csv')
    except FileNotFoundError:
        # Генерация демо-данных
        np.random.seed(42)
        n = 1000
        
        # Создание синтетических данных
        avg_grades = np.random.normal(75, 15, n)
        attendance_rates = np.random.normal(80, 20, n)
        participation_levels = np.random.choice([0, 1, 2], size=n, p=[0.2, 0.5, 0.3])
        
        # Целевая переменная с некоторым шумом и зависимостью от входных данных
        final_scores = (
            0.6 * avg_grades +
            0.3 * attendance_rates +
            10 * participation_levels +
            np.random.normal(0, 5, n)
        )
        
        # Обрезание значений до интервала [0, 100]
        final_scores = np.clip(final_scores, 0, 100)
        
        # Создание DataFrame
        data = pd.DataFrame({
            'avg_grade': avg_grades,
            'attendance_rate': attendance_rates,
            'participation_level': participation_levels,
            'final_score': final_scores
        })
        
        # Сохранение сгенерированных данных
        os.makedirs('data', exist_ok=True)
        data.to_csv('data/prepared_data.csv', index=False)
    
    # Подготовка данных для модели
    X = data[['avg_grade', 'attendance_rate', 'participation_level']]
    y = data['final_score']
    
    # Разделение на тренировочную и тестовую выборки
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Нормализация данных
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Обучение модели регрессии Random Forest
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train_scaled, y_train)
    
    # Обучение модели логистической регрессии для оценки вероятности
    # Преобразуем задачу в бинарную классификацию с порогом 70 (проходной балл)
    y_train_binary = (y_train >= 70).astype(int)
    y_test_binary = (y_test >= 70).astype(int)
    
    lr_model = LogisticRegression(random_state=42)
    lr_model.fit(X_train_scaled, y_train_binary)
    
    # Оценка производительности моделей
    rf_score = rf_model.score(X_test_scaled, y_test)
    lr_score = lr_model.score(X_test_scaled, y_test_binary)
    
    print(f"Random Forest Regression R² score: {rf_score:.4f}")
    print(f"Logistic Regression accuracy score: {lr_score:.4f}")
    
    # Сохранение моделей и scaler
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    os.makedirs(model_dir, exist_ok=True)
    
    joblib.dump(rf_model, os.path.join(model_dir, 'random_forest_model.pkl'))
    joblib.dump(lr_model, os.path.join(model_dir, 'logistic_regression_model.pkl'))
    joblib.dump(scaler, os.path.join(model_dir, 'scaler.pkl'))
    
    return rf_score, lr_score