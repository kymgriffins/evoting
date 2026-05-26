# 🔐 CREDENTIALS — All Logins for Testing

---

## Admin Accounts (full system control)

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Super Admin |
| `admin02` | `admin123` | Admin |
| `admin03` | `admin123` | Admin |
| `admin04` | `admin123` | Admin |
| `admin05` | `admin123` | Admin |

**Admin can:** Create elections, add positions, approve/reject candidates, view audit logs, see all stats.

---

## Candidate Accounts (can upload manifestos & post updates)

| Username | Password | Full Name | School |
|----------|----------|-----------|--------|
| `cand001` | `cand123` | James Mwangi | Engineering |
| `cand002` | `cand123` | Faith Chebet | Education |
| `cand003` | `cand123` | Kevin Odhiambo | Health Sciences |
| `cand004` | `cand123` | Esther Nyambura | Business |
| `cand005` | `cand123` | Daniel Kiprop | Law |
| `cand006` | `cand123` | Sarah Wanjiku | Science & Tech |
| `cand007` | `cand123` | Michael Ndegwa | Engineering |
| `cand008` | `cand123` | Lucy Akinyi | Education |
| `cand009` | `cand123` | Brian Omondi | Business |
| `cand010` | `cand123` | Grace Mwende | Law |

**Candidate can:** Create/edit/delete manifestos, post progress updates (Not Started / In Progress / Completed / Delayed), view leaderboard.

---

## Voter Accounts (can vote & rate manifestos)

| Range | Password | Count |
|-------|----------|-------|
| `v0001` – `v0600` | `voter123` | 600 voters |

**Voter can:** Vote in active elections, rate manifestos (1-5 stars + comments), view results & tracking & leaderboard.

---

## How to Login

1. Go to `http://localhost:8000/login/`
2. Enter username and password from above
3. Each role sees a **different dashboard** after login

---

## Quick Test Flow

```
1. Login as admin → Create Election → Add Positions
2. Candidates are already pre-loaded and approved
3. Login as v0001 → Vote in the election → Rate manifestos
4. Login as cand001 → Post manifesto updates
5. Visit /leaderboard/ → See rankings
6. Visit /api/leaderboard/ → See JSON data
```
