# Используем официальный образ Python
FROM python:3.10.12-slim

WORKDIR /app

# Устанавливаем необходимые зависимости
RUN pip install --no-cache-dir python-dotenv requests

# Копируем и устанавливаем зависимости из requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем исходный код бота в контейнер
COPY . /app


# Копируем файл .env
COPY .env /app/.env

# Указываем команду запуска бота
CMD ["python", "main.py"]
