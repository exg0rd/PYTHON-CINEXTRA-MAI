# Онлайн-кинотеатр (курсовой проект по дисциплине Python: продвинутый уровень)

*К сожалению в процессе разработки не удалось сохранить историю гита из-за мердж конфликтов, многочисленных правок и испорченных веток и пуллов с разных устройств, залита финальная версия

Полноценная платформа онлайн-кинотеатра с микросервисной архитектурой, включающая фронтенд на Next.js, бэкенд на FastAPI, систему обработки видео и потокового воспроизведения.

Базу данных можно найти тут https://drive.google.com/file/d/1mIKxDGw6ow_ld6qGb8rd-Dkfi2yQp2mi/view?usp=sharing

## Архитектура системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   MinIO         │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Storage)     │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 9000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   PostgreSQL    │              │
         │              │   (Database)    │              │
         │              │   Port: 5432    │              │
         │              └─────────────────┘              │
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   Redis         │              │
         │              │   (Cache/Queue) │              │
         │              │   Port: 6379    │              │
         │              └─────────────────┘              │
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         └─────────────►│   Celery        │◄─────────────┘
                        │   (Workers)     │
                        │   Background    │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   FFmpeg        │
                        │   (Transcoding) │
                        │   HLS Streaming │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Monitoring    │
                        │   Prometheus    │◄─── Metrics Collection
                        │   Port: 9090    │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Grafana       │
                        │   (Dashboard)   │◄─── Visualization
                        │   Port: 3002    │
                        └─────────────────┘
```

### Компоненты архитектуры:

**Frontend (Next.js)**
- Пользовательский интерфейс с адаптивным дизайном
- Административная панель для управления контентом
- Видеоплеер с поддержкой HLS потокового воспроизведения
- Система аутентификации и авторизации

**Backend (FastAPI)**
- REST API для управления фильмами, пользователями и контентом
- Система аутентификации с JWT токенами
- Интеграция с внешними сервисами (MinIO, Redis, PostgreSQL)
- Обработка загрузки файлов и управление задачами

**MinIO (Object Storage)**
- Хранение видеофайлов, превью и обработанного контента
- Совместимость с Amazon S3 API
- Поддержка больших файлов и потокового доступа

**PostgreSQL (Database)**
- Основная база данных для метаданных фильмов
- Информация о пользователях и сессиях
- Данные об актерах, жанрах и рейтингах

**Redis (Cache & Message Broker)**
- Кэширование часто запрашиваемых данных
- Очередь задач для Celery
- Хранение сессий пользователей

**Celery (Background Workers)**
- Асинхронная обработка видеофайлов
- Транскодирование в различные качества (480p, 720p, 1080p, 4K)
- Генерация превью и создание HLS манифестов
- Мониторинг прогресса обработки в реальном времени

**FFmpeg (Video Processing)**
- Транскодирование видео в различные форматы и качества
- Создание HLS сегментов для потокового воспроизведения
- Генерация превью изображений
- Оптимизация для веб-воспроизведения

**Prometheus (Metrics Collection)**
- Сбор метрик производительности системы
- Мониторинг использования ресурсов
- Отслеживание времени обработки видео
- Метрики API запросов и ошибок

**Grafana (Monitoring Dashboard)**
- Визуализация метрик в реальном времени
- Дашборды для мониторинга системы
- Алерты при превышении пороговых значений
- Анализ производительности и трендов

## Системные требования

- **Операционная система**: Linux, macOS, Windows
- **Node.js**: версия 18+ (рекомендуется 20+)
- **Python**: версия 3.9+
- **Docker**: для запуска сервисов инфраструктуры
- **FFmpeg**: для обработки видео
- **Свободное место**: минимум 10GB для видеофайлов

## Установка и запуск

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd online-cinema
```

### 2. Установка зависимостей
```bash
# Установка зависимостей фронтенда
cd frontend
npm install

# Установка зависимостей бэкенда
cd ../backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

**Backend (.env)**
```bash
cd backend
cp .env.example .env
```

Отредактируйте файл `.env`:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/cinema_db
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password123
MINIO_USE_SSL=false
JWT_SECRET_KEY=your-secret-key-here
```

**Frontend (.env.local)**
```bash
cd frontend
cp .env.example .env.local
```

Отредактируйте файл `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MINIO_ENDPOINT=http://localhost:9000
```

### 4. Быстрый запуск (рекомендуется)

**Запуск всей системы одной командой:**
```bash
./start-full-system.sh
```

Этот скрипт автоматически:
- Запускает все Docker сервисы (PostgreSQL, Redis, MinIO, Prometheus, Grafana)
- Запускает Celery Worker для обработки видео
- Запускает Backend API (FastAPI)
- Запускает Frontend (Next.js)
- Показывает статус всех сервисов

**Запуск только мониторинга (опционально):**
```bash
./start-monitoring.sh
```

### 5. Ручной запуск (альтернативный способ)

Если предпочитаете запускать компоненты по отдельности:

**Шаг 1: Запуск инфраструктурных сервисов**
```bash
sudo docker-compose -f docker-compose.media.yml up -d
```

**Шаг 2: Инициализация базы данных**
```bash
cd backend
source venv/bin/activate
python manage_db.py  # Создание таблиц и загрузка данных
python create_admin.py  # Создание администратора
```

**Шаг 3: Запуск Celery Worker**
```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
```

**Шаг 4: Запуск Backend**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Шаг 5: Запуск Frontend**
```bash
cd frontend
npm run dev
```

### 6. Остановка системы

**Остановка всех сервисов:**
```bash
./stop-full-system.sh
```

Или нажмите `Ctrl+C` в терминале где запущен `start-full-system.sh`

## Порты и сервисы

| Сервис | Порт | URL | Описание |
|--------|------|-----|----------|
| Frontend | 3000 | http://localhost:3000 | Пользовательский интерфейс |
| Backend API | 8000 | http://localhost:8000 | REST API |
| API Docs | 8000 | http://localhost:8000/docs | Swagger документация |
| PostgreSQL | 5432 | localhost:5432 | База данных |
| Redis | 6379 | localhost:6379 | Кэш и очередь задач |
| MinIO | 9000 | http://localhost:9000 | Объектное хранилище |
| MinIO Console | 9001 | http://localhost:9001 | Веб-интерфейс MinIO |
| Prometheus | 9090 | http://localhost:9090 | Сбор метрик |
| Grafana | 3002 | http://localhost:3002 | Визуализация метрик |

## Учетные данные по умолчанию

**Администратор системы:**
- Email: `admin@cinema.com`
- Пароль: `admin123`

**MinIO:**
- Access Key: `admin`
- Secret Key: `password123`

**PostgreSQL:**
- Пользователь: `postgres`
- Пароль: `password`
- База данных: `cinema_db`

**Grafana:**
- Пользователь: `admin`
- Пароль: `admin`

## Основные функции

**Для пользователей:**
- Просмотр каталога фильмов с фильтрацией и поиском
- Потоковое воспроизведение видео в различных качествах
- Информация о фильмах, актерах и рейтингах
- Адаптивный интерфейс для всех устройств

**Для администраторов:**
- Загрузка и управление видеофайлами
- Редактирование метаданных фильмов
- Мониторинг процесса обработки видео
- Управление пользователями и контентом

**Технические возможности:**
- Автоматическое транскодирование в множественные качества
- HLS потоковое воспроизведение с адаптивным битрейтом
- Генерация превью и миниатюр
- Мониторинг прогресса обработки в реальном времени
- Масштабируемая архитектура с поддержкой нагрузки

## Разработка

### Структура проекта
```
├── frontend/                 # Next.js приложение
│   ├── src/
│   │   ├── components/      # React компоненты
│   │   ├── pages/          # Страницы приложения
│   │   ├── styles/         # CSS стили
│   │   └── utils/          # Утилиты и хелперы
│   ├── public/             # Статические файлы
│   └── package.json        # Зависимости фронтенда
├── backend/                 # FastAPI приложение
│   ├── app/
│   │   ├── api/            # Эндпоинты API
│   │   ├── core/           # Основная логика
│   │   ├── db/             # Модели базы данных
│   │   ├── services/       # Бизнес-логика
│   │   └── workers/        # Celery задачи
│   ├── alembic/            # Миграции базы данных
│   ├── logs/               # Логи приложения
│   └── requirements.txt    # Зависимости Python
├── monitoring/              # Конфигурация мониторинга
│   ├── grafana/            # Дашборды и источники данных
│   ├── prometheus.yml      # Конфигурация Prometheus
│   └── alert_rules.yml     # Правила алертов
├── nginx/                   # Конфигурация Nginx
├── docker-compose.media.yml # Docker сервисы
├── start-full-system.sh     # Запуск всей системы
├── start-monitoring.sh      # Запуск мониторинга
├── stop-full-system.sh      # Остановка системы
├── kill-processes.sh        # Очистка процессов
└── README.md               # Документация
```

### API Endpoints

**Аутентификация:**
- `POST /api/auth/login` - Вход в систему
- `POST /api/auth/register` - Регистрация пользователя
- `POST /api/auth/refresh` - Обновление токена

**Фильмы:**
- `GET /api/movies` - Список фильмов с пагинацией
- `GET /api/movies/{id}` - Детальная информация о фильме
- `GET /api/movies/search` - Поиск фильмов

**Администрирование:**
- `POST /api/admin/movies/{id}/upload-video` - Загрузка видео
- `GET /api/upload/status/{task_id}` - Статус обработки
- `POST /api/upload/process/{movie_id}` - Запуск обработки

**Потоковое воспроизведение:**
- `GET /api/stream/{movie_id}` - HLS манифест
- `GET /api/stream/{movie_id}/thumbnail` - Превью фильма

## Мониторинг и логирование

**Система мониторинга:**
- **Prometheus**: Сбор метрик системы на http://localhost:9090
- **Grafana**: Дашборды мониторинга на http://localhost:3002
- **Метрики**: Производительность API, использование ресурсов, время обработки видео
- **Алерты**: Уведомления при превышении пороговых значений

**Логи приложения:**
- Backend: `backend/logs/app.log`
- Celery: `backend/logs/celery.log`
- Frontend: консоль браузера

**Мониторинг задач:**
- Статус обработки видео через API
- Логи Celery для отладки
- Метрики производительности в Grafana
- Дашборды в реальном времени

## Устранение неполадок

**Проблемы с запуском:**
1. Убедитесь, что все порты свободны (3000, 8000, 5432, 6379, 9000, 9001, 9090, 3002)
2. Проверьте статус Docker контейнеров: `sudo docker ps`
3. Проверьте логи сервисов: `sudo docker logs <container_name>`
4. Используйте `./kill-processes.sh` для очистки зависших процессов

**Проблемы с обработкой видео:**
1. Убедитесь, что FFmpeg установлен: `ffmpeg -version`
2. Проверьте логи Celery: `tail -f backend/logs/celery.log`
3. Проверьте доступность MinIO: `curl http://localhost:9000/minio/health/live`

**Проблемы с базой данных:**
1. Проверьте подключение к PostgreSQL: `sudo docker logs cinema_postgres`
2. Пересоздайте базу данных: `cd backend && python manage_db.py`
3. Проверьте переменные окружения в `.env`

**Проблемы с мониторингом:**
1. Запустите диагностику: `./start-monitoring.sh`
2. Проверьте логи: `sudo docker logs cinema_prometheus` и `sudo docker logs cinema_grafana`
3. Убедитесь, что порты 9090 и 3002 свободны

**Полезные команды:**
- Остановка всех сервисов: `./stop-full-system.sh`
- Очистка процессов: `./kill-processes.sh`
- Перезапуск Docker сервисов: `sudo docker-compose -f docker-compose.media.yml restart`
- Просмотр логов в реальном времени: `tail -f backend/logs/celery.log`

