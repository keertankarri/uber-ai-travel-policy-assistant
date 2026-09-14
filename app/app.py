import os
import sys
from datetime import datetime

# Ensure Python can import models.py from app/ and modules from src/
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from models import db, User, Expense, ChatMessage

# Load API key from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'uber-corporate-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def seed_database():
    """Seeds initial valid Employee IDs, names, departments, and sample expenses."""
    with app.app_context():
        db.create_all()
        
        # 1. Seed regular employees only if DB is totally empty
        if not User.query.first():
            u1 = User(username="UB-101", name="Alex Morgan", department="Engineering")
            u2 = User(username="UB-102", name="Sarah Chen", department="Product Design")
            u3 = User(username="UB-103", name="Michael Scott", department="Operations")
            
            db.session.add_all([u1, u2, u3])
            db.session.commit()

            # Seed sample expenses
            e1 = Expense(user_id=u1.id, category="Meals", amount=45.50, status="Approved", date_submitted=datetime(2026, 9, 8))
            e2 = Expense(user_id=u1.id, category="Rideshare", amount=22.10, status="Approved", date_submitted=datetime(2026, 9, 5))
            e3 = Expense(user_id=u1.id, category="Flight", amount=310.00, status="Pending", date_submitted=datetime(2026, 9, 1))
            e4 = Expense(user_id=u2.id, category="Hotel", amount=210.00, status="Approved", date_submitted=datetime(2026, 9, 7))
            e5 = Expense(user_id=u2.id, category="Airport Transfer", amount=65.00, status="Rejected", date_submitted=datetime(2026, 9, 3))
            e6 = Expense(user_id=u3.id, category="Meals", amount=88.40, status="Pending", date_submitted=datetime(2026, 9, 9))
            
            db.session.add_all([e1, e2, e3, e4, e5, e6])
            db.session.commit()

        # 2. Explicitly check for the Admin user and create if missing
        admin = User.query.filter_by(username="UB-ADMIN").first()
        if not admin:
            new_admin = User(username="UB-ADMIN", name="System Admin", department="Management")
            db.session.add(new_admin)
            db.session.commit()
            print("✅ UB-ADMIN successfully added to the database.")

with app.app_context():
    seed_database()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    history = ChatMessage.query.filter_by(user_id=user.id).order_by(ChatMessage.timestamp.asc()).all() if user else []

    return render_template('index.html', username=session['username'], chat_history=history)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        employee_id = request.form.get('username', '').strip().upper()
        user = User.query.filter_by(username=employee_id).first()
        if user:
            session['username'] = user.username
            return redirect(url_for('index'))
        return render_template('login.html', error="Invalid ID. Please enter UB-101, UB-102, UB-103, or UB-ADMIN.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat', methods=['POST'])
def chat():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_input = request.json.get('message', '')
    if not user_input:
        return jsonify({'response': 'Please enter a valid message.'})

    user = User.query.filter_by(username=session['username']).first()

    # Save user message to database
    if user:
        db.session.add(ChatMessage(user_id=user.id, sender='user', message=user_input))
        db.session.commit()

    try:
        from agent import run_agent
        response_text = run_agent(user_input, session['username'])
    except Exception as e:
        print(f"\n❌ Error executing agent: {e}\n")
        response_text = f"An error occurred while invoking the agent: {str(e)}"

    # Save bot response to database
    if user:
        db.session.add(ChatMessage(user_id=user.id, sender='bot', message=response_text))
        db.session.commit()

    return jsonify({'response': response_text})

@app.route('/expenses')
def expenses():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('login'))

    # If Admin, fetch all expenses. If employee, fetch personal expenses.
    if session['username'] == 'UB-ADMIN':
        user_expenses = Expense.query.order_by(Expense.date_submitted.desc()).all()
    else:
        user_expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date_submitted.desc()).all()
        
    return render_template('expenses.html', user=user, expenses=user_expenses, is_admin=(session['username'] == 'UB-ADMIN'))

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('login'))

    category = request.form.get('category', '').strip()
    amount_str = request.form.get('amount', '0')
    status = request.form.get('status', 'Pending')

    try:
        amount = float(amount_str)
        if category and amount > 0:
            new_expense = Expense(
                user_id=user.id,
                category=category,
                amount=amount,
                status=status,
                date_submitted=datetime.utcnow()
            )
            db.session.add(new_expense)
            db.session.commit()
    except ValueError:
        pass

    return redirect(url_for('expenses'))

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    expense = Expense.query.get(expense_id)

    # Allow deletion if the user owns the expense, OR if the user is the Admin
    if expense and user and (expense.user_id == user.id or session['username'] == 'UB-ADMIN'):
        db.session.delete(expense)
        db.session.commit()

    return redirect(url_for('expenses'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    is_admin = (session['username'] == 'UB-ADMIN')
    
    # Initialize our new admin dictionaries
    department_spend = {}
    time_spend = {}

    if is_admin:
        # Fetch company-wide data
        target_expenses = Expense.query.all()
        total_messages = ChatMessage.query.count()
        
        # Calculate Spend by Department
        for e in target_expenses:
            u = User.query.get(e.user_id)
            dept = u.department if u else "Unknown"
            department_spend[dept] = department_spend.get(dept, 0) + e.amount
            
        # Calculate Spend Over Time (Grouped by Date)
        time_spend_dict = {}
        for e in target_expenses:
            date_str = e.date_submitted.strftime('%Y-%m-%d')
            time_spend_dict[date_str] = time_spend_dict.get(date_str, 0) + e.amount
        
        # Sort the timeline dict by date chronologically
        time_spend = dict(sorted(time_spend_dict.items()))
            
    else:
        # Fetch employee-specific data
        target_expenses = Expense.query.filter_by(user_id=user.id).all() if user else []
        total_messages = ChatMessage.query.filter_by(user_id=user.id).count() if user else 0

    # Calculate Standard KPIs
    total_spend = sum(e.amount for e in target_expenses)
    approved_count = sum(1 for e in target_expenses if e.status.lower() == 'approved')
    pending_count = sum(1 for e in target_expenses if e.status.lower() == 'pending')
    rejected_count = sum(1 for e in target_expenses if e.status.lower() == 'rejected')

    categories = {}
    for e in target_expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    return render_template(
        'dashboard.html',
        username=session['username'],
        user=user,
        is_admin=is_admin,
        total_spend=total_spend,
        approved_count=approved_count,
        pending_count=pending_count,
        rejected_count=rejected_count,
        categories=categories,
        total_messages=total_messages,
        department_spend=department_spend,
        time_spend=time_spend
    )
if __name__ == '__main__':
    app.run(debug=True, port=5000)