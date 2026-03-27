# API Reference

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

## Endpoints

### Health Check

```
GET /health
```

Response:
```json
{"status": "ok", "version": "1.0.0"}
```

### Authentication

| Method | Endpoint         | Description          |
| ------ | ---------------- | -------------------- |
| POST   | `/api/v1/auth/login`   | Login              |
| POST   | `/api/v1/auth/refresh` | Refresh token      |
| POST   | `/api/v1/auth/logout`  | Logout             |
| GET    | `/api/v1/auth/me`      | Current user info  |

### Students

| Method | Endpoint                      | Description          |
| ------ | ----------------------------- | -------------------- |
| GET    | `/api/v1/students`            | List students        |
| POST   | `/api/v1/students`            | Create student       |
| GET    | `/api/v1/students/{id}`       | Get student          |
| PUT    | `/api/v1/students/{id}`       | Update student       |
| DELETE | `/api/v1/students/{id}`       | Delete student       |
| POST   | `/api/v1/students/{id}/enroll-face` | Enroll face   |

### Attendance

| Method | Endpoint                  | Description              |
| ------ | ------------------------- | ------------------------ |
| GET    | `/api/v1/attendance`      | List attendance records  |
| GET    | `/api/v1/attendance/today`| Today's attendance       |
| GET    | `/api/v1/attendance/stats`| Attendance statistics    |
| POST   | `/api/v1/attendance/manual`| Manual check-in         |

### Devices

| Method | Endpoint                    | Description          |
| ------ | --------------------------- | -------------------- |
| GET    | `/api/v1/devices`           | List devices         |
| POST   | `/api/v1/devices`           | Register device      |
| GET    | `/api/v1/devices/{id}/status` | Device status      |
| POST   | `/api/v1/devices/{id}/sync` | Sync device          |
| DELETE | `/api/v1/devices/{id}`      | Remove device        |

### Reports

| Method | Endpoint               | Description          |
| ------ | ---------------------- | -------------------- |
| GET    | `/api/v1/reports/daily`  | Daily report       |
| GET    | `/api/v1/reports/weekly` | Weekly report      |
| GET    | `/api/v1/reports/monthly`| Monthly report     |
| GET    | `/api/v1/reports/export` | Export CSV/Excel   |

## Error Format

All errors return a standard format:

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource was not found."
  },
  "meta": {
    "timestamp": "2025-01-01T00:00:00+00:00"
  }
}
```

## Interactive Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
