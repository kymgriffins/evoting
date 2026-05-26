# 🗃️ DATA MODEL — Every Database Table Explained

## Entity Relationship Summary

```
User ──┬──→ Candidate (one-to-one)
       └──→ Vote (one-to-many)
       └──→ ManifestoRating (one-to-many)
       └──→ AuditLog (one-to-many)

Election ──→ Position (one-to-many)
          └──→ Candidate (one-to-many)
          └──→ Vote (one-to-many)

Position ──→ Candidate (one-to-many)
          └──→ Vote (one-to-many)

Candidate ──→ Manifesto (one-to-many)
           └── Vote (one-to-many)

Manifesto ──→ ManifestoUpdate (one-to-many)
          └── ManifestoRating (one-to-many)
```

---

## Table 1: `core_user` — Users

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (auto) | Unique ID |
| `username` | Text (unique) | Login username |
| `password` | Text | Hashed password (bcrypt) |
| `email` | Text | User's email |
| `first_name` | Text | First name |
| `last_name` | Text | Last name |
| `role` | Text: `voter`/`candidate`/`admin` | User type |
| `is_verified` | Boolean | Email/account verified |
| `student_id` | Text (unique, nullable) | University ID like `ENGR-2024/0001` |
| `is_staff` | Boolean | Can access Django admin |
| `is_superuser` | Boolean | Full system access |

**Note:** This extends Django's built-in User model. All default fields (date_joined, last_login, etc.) also exist.

---

## Table 2: `core_election` — Elections

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (auto) | Unique ID |
| `title` | Text | "CUEA Student Council Elections 2026" |
| `description` | Text | Long description of the election |
| `start_date` | DateTime | When voting opens |
| `end_date` | DateTime | When voting closes |
| `is_active` | Boolean | Whether it's visible to voters |
| `created_at` | DateTime | Auto-set when created |

---

## Table 3: `core_position` — Positions within an Election

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (auto) | Unique ID |
| `election` | ForeignKey → Election | Which election this belongs to |
| `title` | Text | "President", "Vice President", etc. |
| `description` | Text | Description of the role |
| `max_votes` | Integer | Usually 1 (how many candidates voter can pick) |
| `order` | Integer | Display order (1 = first on ballot) |

---

## Table 4: `core_candidate` — Candidates

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (auto) | Unique ID |
| `user` | OneToOneField → User | Link to user account |
| `position` | ForeignKey → Position | Which position they're running for |
| `election` | ForeignKey → Election | Which election |
| `bio` | Text | Candidate biography / platform summary |
| `photo` | URL | Link to candidate photo |
| `is_approved` | Boolean | Admin must approve before appearing on ballot |
| `created_at` | DateTime | When they registered |

### Calculated Properties (not stored in DB)
- `success_rate` — % of manifesto items marked completed
- `avg_rating` — Average star rating across all their manifestos
- `total_ratings` — Number of ratings received

---

## Table 5: `core_manifesto` — Manifesto Items (Campaign Promises)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (auto) | Unique ID |
| `candidate` | ForeignKey → Candidate | Who made this promise |
| `title` | Text | "Campus Wi-Fi Upgrade" |
| `description` | Text | Detailed explanation of the promise |
| `category` | Choice: `education`/`healthcare`/`infrastructure`/`student_welfare`/`other` | Category of the promise |
| `created_at` | DateTime | When added |
| `updated_at` | DateTime | Last modified |

---

## Table 6: `core_vote` — Votes Cast

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (auto) | Unique ID |
| `voter` | ForeignKey → User | Who voted |
| `candidate` | ForeignKey → Candidate | Who they voted for |
| `position` | ForeignKey → Position | Which position |
| `election` | ForeignKey → Election | Which election |
| `timestamp` | DateTime | When vote was cast |

**Constraint:** A voter can only vote once per position per election (`unique_together`).

---

## Table 7: `core_manifestoupdate` — Progress Updates

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (auto) | Unique ID |
| `manifesto` | ForeignKey → Manifesto | Which promise this updates |
| `status` | Choice: `not_started`/`in_progress`/`completed`/`delayed` | Current progress |
| `description` | Text | What was done / why delayed |
| `evidence_url` | URL (optional) | Link to proof (report, photo, etc.) |
| `created_at` | DateTime | When update was posted |

---

## Table 8: `core_manifestorating` — User Ratings & Comments

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (auto) | Unique ID |
| `user` | ForeignKey → User | Who rated |
| `manifesto` | ForeignKey → Manifesto | What they rated |
| `rating` | Integer (1-5) | Star rating |
| `comment` | Text (optional) | Written feedback |
| `created_at` | DateTime | When rated |

**Constraint:** Each user can only rate each manifesto once (`unique_together`).

---

## Table 9: `core_auditlog` — Audit Trail

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer (auto) | Unique ID |
| `user` | ForeignKey → User (nullable) | Who performed the action |
| `action` | Text | "Vote cast", "Candidate approved", etc. |
| `details` | Text | More info about the action |
| `ip_address` | IP Address | Where the request came from |
| `timestamp` | DateTime | When it happened |

**Why no blockchain?** Instead of complex blockchain, every action is logged to this table with user, IP, and timestamp. This gives us a complete, auditable trail that's searchable and doesn't require mining or consensus.

---

## 🗺️ Visual Data Flow

```
USER REGISTERS
  └── core_user created (role = voter/candidate/admin)

CANDIDATE SETS UP PROFILE
  └── core_candidate created (linked to user)
  └── Admin approves (is_approved = true)

CANDIDATE CREATES MANIFESTO
  └── core_manifesto created (linked to candidate)

ELECTION CREATED (by admin)
  └── core_election created
  └── core_position created (President, VP, etc.)

VOTER VOTES
  └── core_vote created (linked to voter, candidate, position, election)
  └── core_auditlog created ("v0001 voted for President")

CANDIDATE POSTS UPDATE
  └── core_manifestoupdate created (status, description)

VOTER RATES MANIFESTO
  └── core_manifestorating created (rating 1-5, comment)
```

---

## 🧮 Row Counts After Population

| Table | Rows |
|-------|------|
| `core_user` | 615 |
| `core_election` | 3 |
| `core_position` | 12 |
| `core_candidate` | 10 |
| `core_manifesto` | 50 |
| `core_vote` | 3,000 |
| `core_manifestoupdate` | ~108 |
| `core_manifestorating` | ~619 |
| `core_auditlog` | ~12 |
