# MedNet2 Frontend (Vue 3)

SPA-клиент для backend `MedNet2`:

- CRUD:
  - `/api/v1/institutions`
  - `/api/v1/employees`
  - `/api/v1/specialties`
  - `/api/v1/patients` (+ `polyclinicId`)
  - `/api/v1/operations` (+ `patientId`)
- Отчёты:
  - все 14 эндпоинтов `/api/v1/reports/*`

## Маршруты интерфейса

- `/tables` — просмотр и CRUD по таблицам БД
- `/reports` — 14 вкладок отчётов с фильтрами для каждого SQL-запроса

## Порты (без конфликтов)

- Frontend dev server: **5174**
- Backend: **8081**
- Запросы на `/api/*` проксируются на `http://localhost:8081`

## Запуск

```bash
cd frontend
npm install
npm run dev
```

## Сборка

```bash
npm run build
```

## Переопределение API base

По умолчанию используется `/api/v1` (через vite proxy).  
Можно переопределить переменной окружения:

```bash
VITE_API_BASE_URL=http://localhost:8081/api/v1 npm run dev
```
