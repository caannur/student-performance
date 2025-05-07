from django.core.management.base import BaseCommand
from ml_model.model_trainer import train_models

class Command(BaseCommand):
    help = 'Обучает модели машинного обучения для прогнозирования успеваемости студентов'

    def handle(self, *args, **options):
        self.stdout.write('Начало обучения моделей...')
        rf_score, lr_score = train_models()
        self.stdout.write(self.style.SUCCESS(f'Успешно обучены модели:'))
        self.stdout.write(f'  - Random Forest R² score: {rf_score:.4f}')
        self.stdout.write(f'  - Logistic Regression accuracy score: {lr_score:.4f}')