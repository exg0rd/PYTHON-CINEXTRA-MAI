# Мониторинг системы

## Обзор

Система использует Prometheus для сбора метрик и Grafana для их визуализации.

## Доступ к сервисам

После запуска системы через `./start-full-system.sh`:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3002
  - Логин: `admin`
  - Пароль: `admin`

## Собираемые метрики

### Backend API (FastAPI)
- Количество запросов
- Время ответа
- Коды ошибок
- Активные соединения

### MinIO
- Использование хранилища
- Количество объектов
- Операции чтения/записи

### Redis
- Использование памяти
- Количество ключей
- Операции в секунду

### Celery Workers
- Количество задач
- Время выполнения
- Успешные/неудачные задачи

## Настройка Grafana

### Первый запуск

1. Откройте http://localhost:3002
2. Войдите с логином `admin` / паролем `admin`
3. Grafana попросит сменить пароль (можно пропустить)

### Добавление источника данных

1. Перейдите в Configuration → Data Sources
2. Нажмите "Add data source"
3. Выберите "Prometheus"
4. URL: `http://prometheus:9090`
5. Нажмите "Save & Test"

### Создание дашборда

1. Перейдите в Create → Dashboard
2. Добавьте панели с метриками:
   - `rate(http_requests_total[5m])` - запросы в секунду
   - `http_request_duration_seconds` - время ответа
   - `celery_tasks_total` - количество задач Celery
   - `minio_bucket_usage_total_bytes` - использование MinIO

## Полезные запросы Prometheus

### Backend API
```promql
# Запросы в секунду
rate(http_requests_total[5m])

# Среднее время ответа
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Процент ошибок
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100
```

### Celery
```promql
# Задачи в очереди
celery_tasks_total{state="pending"}

# Успешные задачи
rate(celery_tasks_total{state="success"}[5m])

# Неудачные задачи
rate(celery_tasks_total{state="failure"}[5m])
```

### MinIO
```promql
# Использование хранилища
minio_bucket_usage_total_bytes

# Количество объектов
minio_bucket_objects_count
```

## Алерты

Алерты настроены в `monitoring/alert_rules.yml`:

- Высокая частота ошибок (>5%)
- Медленные запросы (>1s)
- Недостаток места на диске (<10%)
- Неудачные задачи Celery

## Логи

Логи сервисов доступны через Docker:

```bash
# Backend логи
tail -f backend/logs/celery.log

# Celery логи
sudo docker logs -f cinema_celery_worker

# Prometheus логи
sudo docker logs -f cinema_prometheus

# Grafana логи
sudo docker logs -f cinema_grafana
```

## Troubleshooting

### Prometheus не собирает метрики

1. Проверьте доступность целей: http://localhost:9090/targets
2. Убедитесь, что сервисы запущены
3. Проверьте конфигурацию в `monitoring/prometheus.yml`

### Grafana не подключается к Prometheus

1. Проверьте URL источника данных: `http://prometheus:9090`
2. Убедитесь, что контейнеры в одной сети
3. Проверьте логи: `sudo docker logs cinema_grafana`

### Метрики не отображаются

1. Проверьте, что Backend экспортирует метрики: http://localhost:8000/metrics
2. Убедитесь, что Prometheus собирает данные
3. Проверьте запросы в Grafana

## Рекомендуемые дашборды

Можно импортировать готовые дашборды из Grafana Labs:

- FastAPI: Dashboard ID 14280
- Redis: Dashboard ID 11835
- PostgreSQL: Dashboard ID 9628
- Node Exporter: Dashboard ID 1860

Импорт: Dashboards → Import → введите ID → Load
