#!/bin/bash

echo "Остановка всех процессов"

kill_processes() {
    local process_name=$1
    local pids=$(pgrep -f "$process_name" 2>/dev/null)
    
    if [ ! -z "$pids" ]; then
        echo "Останавливаем $process_name процессы: $pids"
        echo "$pids" | xargs kill -TERM 2>/dev/null
        sleep 2
        
        # Проверяем что процессы завершились
        local remaining=$(pgrep -f "$process_name" 2>/dev/null)
        if [ ! -z "$remaining" ]; then
            echo "Принудительно завершаем оставшиеся процессы: $remaining"
            echo "$remaining" | xargs kill -KILL 2>/dev/null
        fi
    fi
}

echo "Поиск Next.js процессов..."
kill_processes "next"
kill_processes "npm run dev"
kill_processes "yarn dev"

echo "Поиск Node.js процессов..."
kill_processes "node.*frontend"

echo "Поиск Python/FastAPI процессов..."
kill_processes "uvicorn"
kill_processes "python.*main:app"
kill_processes "fastapi"

echo "Поиск Celery процессов..."
kill_processes "celery"


echo "Проверка Docker контейнеров..."
if command -v docker &> /dev/null; then
    docker ps --format "table {{.Names}}" | grep -E "(cinema|minio|redis|prometheus|grafana|streaming)" | while read container; do
        if [ "$container" != "NAMES" ] && [ ! -z "$container" ]; then
            echo "Останавливаем Docker контейнер: $container"
            docker stop "$container" 2>/dev/null
        fi
    done
fi

echo "Очистка lock файлов..."
if [ -f "frontend/.next/dev/lock" ]; then
    rm -f frontend/.next/dev/lock
    echo "Удален lock файл Next.js"
fi

find . -name "*.pid" -type f -delete 2>/dev/null

echo "Проверка занятых портов..."
check_port() {
    local port=$1
    local service=$2
    local pid=$(lsof -ti:$port 2>/dev/null)
    
    if [ ! -z "$pid" ]; then
        echo "Порт $port ($service) занят процессом $pid"
        echo "Завершаем процесс на порту $port..."
        kill -TERM $pid 2>/dev/null
        sleep 1
        
        # Проверяем снова
        local remaining=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$remaining" ]; then
            echo "Принудительно завершаем процесс $remaining на порту $port"
            kill -KILL $remaining 2>/dev/null
        fi
    fi
}

# Проверяем основные порты
check_port 3000 "Frontend"
check_port 8000 "Backend API"
check_port 5555 "Celery Flower"
check_port 9000 "MinIO"
check_port 9001 "MinIO Console"
check_port 9090 "Prometheus"
check_port 3002 "Grafana"

echo ""
echo "Все процессы остановлены!"
echo ""
echo "Проверка статуса портов:"
for port in 3000 8000 5555 9000 9001 9090 3002; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "Порт $port: занят"
    else
        echo "Порт $port: свободен"
    fi
done

echo ""
echo "Теперь можно запустить систему"
echo "   ./start-dev.sh"