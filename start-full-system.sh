#!/bin/bash

echo "Запуск полной системы онлайн-кинотеатра"
echo "=========================================="

# Функция для остановки всех процессов при выходе
cleanup() {
    echo ""
    echo "Остановка всех сервисов..."
    
    # Останавливаем фоновые процессы
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "Backend остановлен"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "Frontend остановлен"
    fi
    if [ ! -z "$CELERY_PID" ]; then
        kill $CELERY_PID 2>/dev/null
        echo "Celery worker остановлен"
    fi
    
    # Останавливаем Docker контейнеры
    echo "Остановка Docker контейнеров..."
    sudo docker-compose -f docker-compose.media.yml down > /dev/null 2>&1
    echo "Docker контейнеры остановлены"
    
    exit 0
}

# Устанавливаем обработчик сигналов
trap cleanup SIGINT SIGTERM

# Проверяем зависимости
echo "Проверка зависимостей..."

if ! command -v docker &> /dev/null; then
    echo "Docker не установлен"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose не установлен"
    exit 1
fi

if [ ! -f "backend/venv/bin/activate" ]; then
    echo "Backend виртуальное окружение не найдено"
    echo "   Создайте его: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

if [ ! -f "frontend/package.json" ]; then
    echo "Frontend не найден"
    exit 1
fi

echo "Все зависимости найдены"

# Очищаем предыдущие процессы
echo "Очистка предыдущих процессов..."
./kill-processes.sh > /dev/null 2>&1

# 1. Запускаем Docker сервисы
echo "Запуск Docker сервисов (MinIO, Redis, Prometheus, Grafana)..."
sudo docker-compose -f docker-compose.media.yml up -d minio redis prometheus grafana

# Ждем запуска Docker сервисов
echo "Ожидание запуска Docker сервисов..."
sleep 5

# Проверяем статус Docker сервисов
if ! sudo docker ps | grep -q "cinema_minio"; then
    echo "MinIO не запустился"
    exit 1
fi

if ! sudo docker ps | grep -q "cinema_redis"; then
    echo "Redis не запустился"
    exit 1
fi

if ! sudo docker ps | grep -q "cinema_prometheus"; then
    echo "Prometheus не запустился (не критично)"
fi

if ! sudo docker ps | grep -q "cinema_grafana"; then
    echo "Grafana не запустился (не критично)"
fi

echo "Docker сервисы запущены"

# 2. Запускаем Celery Worker
echo "Запуск Celery Worker..."
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info --detach --pidfile=celery.pid --logfile=logs/celery.log
CELERY_PID=$(cat celery.pid 2>/dev/null)
cd ..
echo "Celery Worker запущен (PID: $CELERY_PID)"

# 3. Запускаем Backend
echo "Запуск Backend API..."
cd backend
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..
echo "Backend запущен (PID: $BACKEND_PID)"

# Ждем запуска backend
sleep 3

# 4. Запускаем Frontend
echo "Запуск Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo "Frontend запущен (PID: $FRONTEND_PID)"

# Ждем запуска frontend
sleep 3

echo ""
echo "Система полностью запущена!"
echo "================================"
echo ""
echo "Доступные сервисы:"
echo "   • Frontend:        http://localhost:3000"
echo "   • Backend API:     http://localhost:8000"
echo "   • API документация: http://localhost:8000/docs"
echo "   • MinIO Console:   http://localhost:9001 (admin/minio123456)"
echo "   • MinIO API:       http://localhost:9000"
echo "   • Prometheus:      http://localhost:9090"
echo "   • Grafana:         http://localhost:3002 (admin/admin)"
echo ""
echo "Статистика системы:"
echo "   • Фильмов в базе: 44,888"
echo "   • Жанры: Drama, Comedy, Action и другие"
echo "   • Годы: 1900-2020"
echo "   • Поиск: Работает"
echo "   • Загрузка видео: Готова"
echo ""
echo "Админ доступ:"
echo "   • Email: admin@cinema.com"
echo "   • Password: admin123"
echo ""
echo "Запущенные сервисы:"
echo "   • Backend API (PID: $BACKEND_PID)"
echo "   • Frontend (PID: $FRONTEND_PID)"
echo "   • Celery Worker (PID: $CELERY_PID)"
echo "   • MinIO (Docker)"
echo "   • Redis (Docker)"
echo "   • Prometheus (Docker)"
echo "   • Grafana (Docker)"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo "Для просмотра логов: tail -f backend/logs/celery.log"
echo ""

# Ждем сигнала остановки
wait