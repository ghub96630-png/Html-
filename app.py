from flask import Flask, request, jsonify, send_from_directory, session
import sqlite3
import os

app = Flask(__name__, static_folder='public')
app.secret_key = 'ajay_secret_key_kalolsavam'  # സെഷൻ സെക്യൂരിറ്റിക്ക് വേണ്ടി

# SQLite Database Setup
def init_db():
    conn = sqlite3.connect('kalolsavam.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            items TEXT NOT NULL,
            fee INTEGER NOT NULL,
            payment_status TEXT NOT NULL,
            marks INTEGER DEFAULT 0,
            total_marks INTEGER DEFAULT 100,
            percentage REAL DEFAULT 0.0,
            grade TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

# API to Register Student
@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form.get('name')
        category = request.form.get('category')
        items = request.form.get('items')
        fee = request.form.get('fee')

        if not name or not category or not items or not fee:
            return "എല്ലാ വിവരങ്ങളും കൃത്യമായി പൂരിപ്പിക്കുക!", 400

        conn = sqlite3.connect('kalolsavam.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO participants (name, category, items, fee, payment_status, marks, total_marks, percentage, grade) VALUES (?, ?, ?, ?, ?, 0, 100, 0.0, "Pending")',
            (name, category, items, int(fee), 'Verified Paid')
        )
        conn.commit()
        conn.close()

        return "<h1>രജിസ്ട്രേഷൻ വിജയകരമായി പൂർത്തിയായി! 🎉</h1><a href='/'>ഹോം പേജിലേക്ക് പോവുക</a>"
    except Exception as e:
        return f"പിഴവ്: {str(e)}", 500

# API to view all participants (Public/Student view)
@app.route('/participants', methods=['GET'])
def get_participants():
    conn = sqlite3.connect('kalolsavam.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM participants')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

# Admin Login API
@app.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.json
    password = data.get('password')
    if password == 'ajay':
        session['is_admin'] = True
        return jsonify({"success": True, "message": "Admin Login Success!"})
    return jsonify({"success": False, "message": "തെറ്റായ പാസ്‌വേഡ്!"}), 401

# Admin Update Marks API
@app.route('/update-participant/<int:id>', methods=['PUT'])
def update_participant(id):
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Unauthorized! ആദ്യം അഡ്മിൻ ആയി ലോഗിൻ ചെയ്യുക."}), 403
    
    data = request.json
    marks = int(data.get('marks', 0))
    total_marks = int(data.get('total_marks', 100))
    
    # ശതമാനവും ഗ്രേഡും കണക്കാക്കുന്നു
    percentage = (marks / total_marks) * 100 if total_marks > 0 else 0
    
    if percentage >= 90:
        grade = 'A+'
    elif percentage >= 80:
        grade = 'A'
    elif percentage >= 70:
        grade = 'B+'
    elif percentage >= 60:
        grade = 'B'
    elif percentage >= 40:
        grade = 'C'
    else:
        grade = 'Failed/Need Improvement'

    conn = sqlite3.connect('kalolsavam.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE participants 
        SET marks = ?, total_marks = ?, percentage = ?, grade = ? 
        WHERE id = ?
    ''', (marks, total_marks, round(percentage, 2), grade, id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "വിവരങ്ങൾ വിജയകരമായി അപ്ഡേറ്റ് ചെയ്തു!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

