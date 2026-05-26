# 🌐 API REFERENCE — All Endpoints & Examples

## Base URL: `http://localhost:8000/api/`

All APIs return JSON. Some require authentication.

---

## 🔍 API Routes Overview

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/users/` | GET/POST/PUT/DELETE | ✅ | Manage all users |
| `/api/elections/` | GET/POST | ❌ Read, ✅ Write | List & manage elections |
| `/api/positions/` | GET/POST | ❌ Read, ✅ Write | Positions within elections |
| `/api/candidates/` | GET/POST | ❌ Read, ✅ Write | Candidate profiles |
| `/api/manifestos/` | GET/POST | ❌ Read, ✅ Write | Manifesto items |
| `/api/votes/` | GET/POST | ✅ Must be logged in | Cast votes |
| `/api/updates/` | GET/POST | ❌ Read, ✅ Write | Manifesto progress updates |
| `/api/ratings/` | GET/POST | ✅ Must be logged in | Rate manifestos |
| `/api/audit-logs/` | GET | ✅ Admin only | System audit trail |
| `/api/elections/<id>/results/` | GET | ❌ Anyone | Election results with vote counts |
| `/api/elections/<id>/tracking/` | GET | ❌ Anyone | Full manifesto tracking data |
| `/api/leaderboard/` | GET | ❌ Anyone | Candidate success rankings |

---

## 📡 Examples

### Get all elections
```bash
curl http://localhost:8000/api/elections/
```
```json
[
  {
    "id": 1,
    "title": "CUEA Student Council Elections 2024",
    "description": "The 2024 annual student council elections.",
    "start_date": "2025-04-21T14:03:00+03:00",
    "end_date": "2025-04-28T14:03:00+03:00",
    "is_active": false
  },
  ...
]
```

### Get election results
```bash
curl http://localhost:8000/api/elections/1/results/
```
```json
{
  "election": "CUEA Student Council Elections 2024",
  "results": [
    {
      "position": "President",
      "candidates": [
        {"candidate_id": 2, "name": "Faith Chebet", "votes": 180},
        {"candidate_id": 1, "name": "James Mwangi", "votes": 165},
        {"candidate_id": 3, "name": "Kevin Odhiambo", "votes": 155}
      ]
    }
  ]
}
```

### Get leaderboard
```bash
curl http://localhost:8000/api/leaderboard/
```
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "name": "James Mwangi",
      "success_rate": 100.0,
      "avg_rating": 4.5,
      "total_manifestos": 5,
      "completed_manifestos": 5,
      "total_votes": 165
    }
  ]
}
```

### Get manifesto tracking data
```bash
curl http://localhost:8000/api/elections/1/tracking/
```
```json
{
  "election": "CUEA Student Council Elections 2024",
  "candidates": [
    {
      "candidate_id": 1,
      "name": "James Mwangi",
      "position": "President",
      "manifestos": [
        {
          "id": 1,
          "title": "Digital Library Access",
          "category": "education",
          "latest_status": "completed",
          "updates": [...]
        }
      ]
    }
  ]
}
```

### Create a vote (requires login)
```bash
curl -X POST http://localhost:8000/api/votes/ \
  -H "Content-Type: application/json" \
  -u v0001:voter123 \
  -d '{"candidate": 1, "position": 1, "election": 3}'
```

### Rate a manifesto (requires login)
```bash
curl -X POST http://localhost:8000/api/ratings/ \
  -H "Content-Type: application/json" \
  -u v0001:voter123 \
  -d '{"manifesto": 1, "rating": 5, "comment": "Excellent work!"}'
```

---

## 🔐 Authentication Methods

### Method 1: Basic Auth (for testing)
```bash
curl -u username:password http://localhost:8000/api/votes/
```

### Method 2: Session Auth (browser)
Login first at `/login/`, then API calls from the same browser work automatically.

### Method 3: Token Auth (for apps)
Django REST Framework supports token auth. Add `Authorization: Token <your-token>` header.

---

## 📋 Response Format

All list endpoints return an **array**: `[ {...}, {...} ]`

All detail endpoints return an **object**: `{ "id": 1, ... }`

Custom endpoints return **nested objects**: `{ "election": "...", "results": [...] }`

---

## ⚠️ Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created (POST success) |
| `400` | Bad Request (missing fields) |
| `401` | Unauthorized (not logged in) |
| `403` | Forbidden (wrong role) |
| `404` | Not Found |
| `500` | Server Error |
