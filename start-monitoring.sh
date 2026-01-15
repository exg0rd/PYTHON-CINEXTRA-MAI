#!/bin/bash

echo "Запуск системы мониторинга"
echo "==========================="

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "Docker не установлен"
    exit 1
fi

# Останавливаем старые контейнеры если есть
echo "Остановка старых контейнеров мониторинга..."
sudo docker stop cinema_prometheus cinema_grafana 2>/dev/null || true
sudo docker rm cinema_prometheus cinema_grafana 2>/dev/null || true

# Запускаем Prometheus и Grafana
echo "Запуск Prometheus и Grafana..."
sudo docker-compose -f docker-compose.media.yml up -d prometheus grafana

# Ждем запуска
echo "Ожидание запуска сервисов..."
sleep 5

# Проверяем статус
echo ""
echo "Проверка статуса контейнеров:"
sudo docker ps | grep -E "(prometheus|grafana)" || echo "Контейнеры не найдены"

echo ""
echo "Проверка логов Prometheus:"
sudo docker logs cinema_prometheus --tail 10 2>&1 | head -10

echo ""
echo "Проверка логов Grafana:"
sudo docker logs cinema_grafana --tail 10 2>&1 | head -10

echo ""
echo "Проверка доступности портов:"
if nc -z localhost 9090 2>/dev/null; then
    echo "  Prometheus (9090): доступен"
else
    echo "  Prometheus (9090): недоступен"
fi

if nc -z localhost 3002 2>/dev/null; then
    echo "  Grafana (3002): доступен"
else
    echo "  Grafana (3002): недоступен"
fi

echo ""
echo "Доступ к сервисам:"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3002 (admin/admin)"
echo ""
echo "Для просмотра логов:"
echo "  sudo docker logs -f cinema_prometheus"
echo "  sudo docker logs -f cinema_grafana"
