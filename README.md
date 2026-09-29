# Personal Finance Advisor Bot

A student-friendly full-stack personal finance management project based on the provided project specification.

## Features
- User registration and login
- Secure password hashing and session management
- Monthly income and savings-goal management
- Expense tracking by category
- Dashboard with income, expenses and remaining balance
- Category-wise spending summary
- Budget/savings recommendations
- Optional Gemini AI integration
- SQLite database through SQLAlchemy
- Responsive dark UI
- Expense deletion
- JSON summary API

## Tech stack
- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- Jinja2
- HTML/CSS/JavaScript
- Gemini AI (optional)

## Run locally

### 1. Create a virtual environment
Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install packages
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Copy `.env.example` to `.env` and set a strong `SECRET_KEY`.

For Gemini AI, add:
```text
GEMINI_API_KEY=your_key_here
```

The application still works without a Gemini key using built-in local recommendations.

### 4. Start
```bash
python app.py
```

Open:
http://127.0.0.1:5000

## Suggested demo flow
1. Register a user.
2. Set monthly income and savings goal.
3. Add rent, food, transport and entertainment expenses.
4. Review dashboard totals.
5. Click "Get AI Advice".
6. Show category-wise spending and savings recommendations.

## Project mapping
1. Environment setup & AI configuration → requirements + `.env`
2. Authentication → registration/login/session handling
3. Financial tracking → income + expense modules
4. AI budget engine → `/api/ai-advice`
5. Dashboard/reporting → dashboard page + summary API
6. Database → SQLAlchemy models with SQLite
7. Frontend/backend integration → Flask routes + Jinja templates
8. Deployment → can be hosted behind a production WSGI server or tunnel
9. Testing → manual workflows plus unit tests can be added

## Important
This is an educational project, not professional financial advice. Do not enter sensitive banking credentials or card numbers.
