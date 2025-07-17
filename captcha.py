import random
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFont
import io
import base64

class CaptchaSystem:
    """Современная система капчи с различными типами проверок"""
    
    def __init__(self):
        self.colors = {
            'красный': '🔴',
            'синий': '🔵', 
            'зеленый': '🟢',
            'желтый': '🟡',
            'фиолетовый': '🟣',
            'оранжевый': '🟠',
            'черный': '⚫',
            'белый': '⚪'
        }
        
        self.animals = {
            'кот': '🐱',
            'собака': '🐶',
            'слон': '🐘',
            'лев': '🦁',
            'обезьяна': '🐵',
            'медведь': '🐻',
            'лиса': '🦊',
            'волк': '🐺',
            'тигр': '🐯',
            'панда': '🐼'
        }
        
        self.objects = {
            'дом': '🏠',
            'машина': '🚗',
            'самолет': '✈️',
            'корабль': '🚢',
            'велосипед': '🚲',
            'поезд': '🚂',
            'ракета': '🚀',
            'вертолет': '🚁',
            'автобус': '🚌',
            'мотоцикл': '🏍️'
        }
        
        self.numbers = {
            'один': '1️⃣',
            'два': '2️⃣',
            'три': '3️⃣',
            'четыре': '4️⃣',
            'пять': '5️⃣',
            'шесть': '6️⃣',
            'семь': '7️⃣',
            'восемь': '8️⃣',
            'девять': '9️⃣',
            'ноль': '0️⃣'
        }
    
    def generate_color_captcha(self) -> Tuple[str, str, List[str]]:
        """Генерация капчи с выбором цвета"""
        correct_color = random.choice(list(self.colors.keys()))
        wrong_colors = random.sample([c for c in self.colors.keys() if c != correct_color], 3)
        
        options = [correct_color] + wrong_colors
        random.shuffle(options)
        
        question = f"🎨 Выберите {correct_color} цвет:"
        
        return question, correct_color, options
    
    def generate_animal_captcha(self) -> Tuple[str, str, List[str]]:
        """Генерация капчи с выбором животного"""
        correct_animal = random.choice(list(self.animals.keys()))
        wrong_animals = random.sample([a for a in self.animals.keys() if a != correct_animal], 3)
        
        options = [correct_animal] + wrong_animals
        random.shuffle(options)
        
        question = f"🐾 Найдите {correct_animal}:"
        
        return question, correct_animal, options
    
    def generate_object_captcha(self) -> Tuple[str, str, List[str]]:
        """Генерация капчи с выбором объекта"""
        correct_object = random.choice(list(self.objects.keys()))
        wrong_objects = random.sample([o for o in self.objects.keys() if o != correct_object], 3)
        
        options = [correct_object] + wrong_objects
        random.shuffle(options)
        
        question = f"🔍 Выберите {correct_object}:"
        
        return question, correct_object, options
    
    def generate_number_captcha(self) -> Tuple[str, str, List[str]]:
        """Генерация капчи с выбором числа"""
        correct_number = random.choice(list(self.numbers.keys()))
        wrong_numbers = random.sample([n for n in self.numbers.keys() if n != correct_number], 3)
        
        options = [correct_number] + wrong_numbers
        random.shuffle(options)
        
        question = f"🔢 Найдите число {correct_number}:"
        
        return question, correct_number, options
    
    def generate_math_captcha(self) -> Tuple[str, str, List[str]]:
        """Генерация математической капчи"""
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operation = random.choice(['+', '-', '*'])
        
        if operation == '+':
            correct_answer = str(num1 + num2)
            question = f"🧮 Сколько будет {num1} + {num2}?"
        elif operation == '-':
            # Убеждаемся, что результат положительный
            if num1 < num2:
                num1, num2 = num2, num1
            correct_answer = str(num1 - num2)
            question = f"🧮 Сколько будет {num1} - {num2}?"
        else:  # multiplication
            correct_answer = str(num1 * num2)
            question = f"🧮 Сколько будет {num1} × {num2}?"
        
        # Генерируем неправильные ответы
        wrong_answers = []
        while len(wrong_answers) < 3:
            wrong = str(random.randint(1, 50))
            if wrong != correct_answer and wrong not in wrong_answers:
                wrong_answers.append(wrong)
        
        options = [correct_answer] + wrong_answers
        random.shuffle(options)
        
        return question, correct_answer, options
    
    def generate_sequence_captcha(self) -> Tuple[str, str, List[str]]:
        """Генерация капчи с последовательностью"""
        start = random.randint(1, 5)
        step = random.randint(2, 4)
        sequence = [start + i * step for i in range(4)]
        next_number = str(start + 4 * step)
        
        question = f"🔢 Продолжите последовательность: {', '.join(map(str, sequence))}, ?"
        
        # Генерируем неправильные ответы
        wrong_answers = []
        while len(wrong_answers) < 3:
            wrong = str(random.randint(1, 50))
            if wrong != next_number and wrong not in wrong_answers:
                wrong_answers.append(wrong)
        
        options = [next_number] + wrong_answers
        random.shuffle(options)
        
        return question, next_number, options
    
    def generate_captcha(self) -> Dict:
        """Генерация случайной капчи"""
        captcha_types = [
            'color', 'animal', 'object', 'number', 'math', 'sequence'
        ]
        
        captcha_type = random.choice(captcha_types)
        
        if captcha_type == 'color':
            question, answer, options = self.generate_color_captcha()
            emoji_options = [f"{self.colors[opt]} {opt}" for opt in options]
        elif captcha_type == 'animal':
            question, answer, options = self.generate_animal_captcha()
            emoji_options = [f"{self.animals[opt]} {opt}" for opt in options]
        elif captcha_type == 'object':
            question, answer, options = self.generate_object_captcha()
            emoji_options = [f"{self.objects[opt]} {opt}" for opt in options]
        elif captcha_type == 'number':
            question, answer, options = self.generate_number_captcha()
            emoji_options = [f"{self.numbers[opt]} {opt}" for opt in options]
        elif captcha_type == 'math':
            question, answer, options = self.generate_math_captcha()
            emoji_options = [f"🔢 {opt}" for opt in options]
        else:  # sequence
            question, answer, options = self.generate_sequence_captcha()
            emoji_options = [f"➡️ {opt}" for opt in options]
        
        return {
            'type': captcha_type,
            'question': question,
            'correct_answer': answer,
            'options': options,
            'emoji_options': emoji_options,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=1)
        }
    
    def verify_answer(self, user_answer: str, correct_answer: str) -> bool:
        """Проверка ответа пользователя"""
        return user_answer.lower().strip() == correct_answer.lower().strip()

# Создание глобального экземпляра системы капчи
captcha_system = CaptchaSystem()