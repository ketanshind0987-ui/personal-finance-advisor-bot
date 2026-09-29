import os
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///finance.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    monthly_income = db.Column(db.Float, default=0)
    savings_goal = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), default="")
    expense_date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def financial_summary(user):
    expenses = Expense.query.filter_by(user_id=user.id).all()
    total = sum(e.amount for e in expenses)
    by_category = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount
    remaining = (user.monthly_income or 0) - total
    return total, remaining, by_category


def generate_local_advice(user):
    total, remaining, by_category = financial_summary(user)
    income = user.monthly_income or 0
    advice = []

    if income <= 0:
        return ["Add your monthly income to receive personalized budget advice."]

    if total > income:
        advice.append("Your recorded expenses are above your monthly income. Review non-essential categories first.")
    else:
        saving_rate = (remaining / income) * 100
        advice.append(f"Your current recorded balance is ₹{remaining:,.2f}, about {saving_rate:.1f}% of income.")

    if by_category:
        largest = max(by_category, key=by_category.get)
        advice.append(f"Your highest recorded spending category is {largest} at ₹{by_category[largest]:,.2f}.")
        if by_category[largest] > income * 0.30:
            advice.append(f"Consider setting a lower limit for {largest} and reviewing recurring purchases.")

    if user.savings_goal > 0:
        if remaining >= user.savings_goal:
            advice.append("Your current recorded balance meets your monthly savings goal.")
        else:
            gap = user.savings_goal - max(remaining, 0)
            advice.append(f"You are ₹{gap:,.2f} away from your monthly savings goal.")

    return advice


@app.route("/")
def index():
    return redirect(url_for("dashboard") if current_user() else url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if User.query.filter_by(email=email).first():
            return render_template("register.html", error="Email already registered.")
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return render_template("login.html", error="Invalid email or password.")
        session["user_id"] = user.id
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.expense_date.desc()).all()
    total, remaining, by_category = financial_summary(user)
    return render_template(
        "dashboard.html",
        user=user,
        expenses=expenses,
        total=total,
        remaining=remaining,
        by_category=by_category,
        advice=generate_local_advice(user),
    )


@app.route("/profile", methods=["POST"])
@login_required
def profile():
    user = current_user()
    user.monthly_income = float(request.form.get("monthly_income", 0) or 0)
    user.savings_goal = float(request.form.get("savings_goal", 0) or 0)
    db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/expense", methods=["POST"])
@login_required
def add_expense():
    user = current_user()
    expense = Expense(
        user_id=user.id,
        category=request.form["category"].strip(),
        amount=float(request.form["amount"]),
        description=request.form.get("description", "").strip(),
        expense_date=datetime.strptime(request.form["expense_date"], "%Y-%m-%d").date()
        if request.form.get("expense_date") else datetime.utcnow().date(),
    )
    db.session.add(expense)
    db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/expense/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = db.session.get(Expense, expense_id)
    if expense and expense.user_id == current_user().id:
        db.session.delete(expense)
        db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/api/summary")
@login_required
def api_summary():
    user = current_user()
    total, remaining, by_category = financial_summary(user)
    return jsonify({
        "income": user.monthly_income or 0,
        "expenses": total,
        "remaining": remaining,
        "categories": by_category,
        "advice": generate_local_advice(user),
    })


@app.route("/api/ai-advice", methods=["POST"])
@login_required
def ai_advice():
    user = current_user()
    total, remaining, by_category = financial_summary(user)
    prompt = f"""
You are a personal finance planning assistant. Give concise, educational budgeting guidance.
Do not present yourself as a licensed financial advisor and do not recommend specific securities.
User monthly income: ₹{user.monthly_income or 0:.2f}
Recorded expenses: ₹{total:.2f}
Remaining: ₹{remaining:.2f}
Categories: {json.dumps(by_category)}
Savings goal: ₹{user.savings_goal or 0:.2f}
Give 5 practical recommendations and a simple next-month budget allocation.
"""

    # Optional Gemini integration. If no key/package is configured, use safe local advice.
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                contents=prompt,
            )
            return jsonify({"advice": response.text})
        except Exception as exc:
            return jsonify({
                "advice": generate_local_advice(user),
                "note": f"AI service unavailable; local recommendations shown. ({type(exc).__name__})"
            })

    return jsonify({"advice": generate_local_advice(user), "note": "Add GEMINI_API_KEY to enable Gemini-generated advice."})


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
