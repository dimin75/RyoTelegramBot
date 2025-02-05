# Используем официальный образ Python
FROM python:3.10.12-slim

RUN apt update && apt install -y \
    build-essential cmake pkg-config \ 
    libboost-all-dev libssl-dev libzmq3-dev \ 
    libunbound-dev libsodium-dev libunwind8-dev \
    liblzma-dev libreadline6-dev libldns-dev \
    libexpat1-dev doxygen graphviz libpgm-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Устанавливаем необходимые зависимости
RUN pip install --no-cache-dir python-dotenv requests

# Копируем и устанавливаем зависимости из requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем исходный код бота в контейнер
COPY . .


# Копируем файл .env
COPY .env /app/.env

# Expose the main port (if applicable)
EXPOSE 8000

# Указываем команду запуска бота
CMD ["python", "main.py"]
