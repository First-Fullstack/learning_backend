# learning_backend

## Setup

Create a `.env` in `backend/`:

```
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=learning
DATABASE_URL=
SECRET_KEY=change_me
CORS_ALLOW_ORIGINS=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
STRIPE_API_KEY=
```

Install dependencies and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Create tables
python -m app.cli
# Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Prefix

- All endpoints are under `/api/v1`.

## Feature Coverage

- Auth: register, login, logout, password reset stub
- Users: profile view/update, stats
- Courses: CRUD, filter, status, categories, detail with progress
- Quizzes: CRUD, list, attempt
- Subscriptions/Purchase: subscribe, cancel, one-time purchase
- Uploads: avatar, course thumbnail/video to S3 (fallback local URL)
- Admin: basic statistics
