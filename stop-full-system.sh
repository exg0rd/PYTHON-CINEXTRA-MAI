#!/bin/bash

echo "Остановка полной системы онлайн-кинотеатра"
echo "============================================="

echo "Остановка всех процессов..."
./kill-processes.sh

echo "Остановка Celery Worker..."
if [ -f "backend/celery.pid" ]; then
    CELERY_PID=$(cat backend/celery.pid)
    if kill -0 $CELERY_PID 2>/dev/null; then
        kill $CELERY_PID
        echo "Celery Worker остановлен (PID: $CELERY_PID)"
    fi
    rm -f backend/celery.pid
fi

echo "Остановка Docker контейнеров..."
sudo docker-compose -f docker-compose.media.yml down

echo ""
echo "Проверка статуса портов:"
for port in 3000 8000 9000 9001 6379 9090 3002; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "Порт $port: все еще занят"
    else
        echo "Порт $port: свободен"
    fi
done


echo "Система остановлена"

echo "Для запуска используйте:"
echo "   ./start-full-system.sh"