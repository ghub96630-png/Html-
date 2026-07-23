from flask import Flask, request, jsonify, send_from_directory, session, render_template_string
import sqlite3
import os

app = Flask(__name__, static_folder='public')
app.secret_key = 'ajay_secret_key_kalolsavam'

def init_db():
    conn = sqlite3.connect('kalolsavam.db')
    cursor = conn.cursor()
    
    # പ്രധാന കുട്ടികളുടെ ടേബിൾ (re_exam_marks കൂടി ചേർത്തു)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            father_name TEXT DEFAULT 'N/A',
            mother_phone TEXT DEFAULT 'N/A',
            category TEXT NOT NULL,
            items TEXT NOT NULL,
            fee INTEGER NOT NULL,
            payment_status TEXT NOT NULL,
            marks INTEGER DEFAULT 0,
            total_marks INTEGER DEFAULT 100,
            quiz_marks REAL DEFAULT 0,
            re_exam_marks REAL DEFAULT 0,
            percentage REAL DEFAULT 0.0,
            grade TEXT DEFAULT 'Pending'
        )
    ''')

    # ഇംപ്രൂവ്മെന്റ് മാർക്കുകൾക്കായി ടേബിൾ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS improvements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id INTEGER,
            student_name TEXT NOT NULL,
            imp_marks REAL DEFAULT 0,
            imp_total REAL DEFAULT 50,
            remarks TEXT DEFAULT 'Improved',
            FOREIGN KEY (participant_id) REFERENCES participants (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/image/<path:filename>')
def serve_image(filename):
    return send_from_directory('image', filename)

@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form.get('name')
        father_name = request.form.get('father_name', 'N/A')
        mother_phone = request.form.get('mother_phone', 'N/A')
        category = request.form.get('category')
        items = request.form.get('items')
        fee = request.form.get('fee')

        if not name or not category or not items or not fee:
            return "എല്ലാ വിവരങ്ങളും കൃത്യമായി പൂരിപ്പിക്കുക!", 400

        conn = sqlite3.connect('kalolsavam.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO participants (name, father_name, mother_phone, category, items, fee, payment_status, marks, total_marks, quiz_marks, re_exam_marks, percentage, grade) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 100, 0, 0, 0.0, "Pending")',
            (name, father_name, mother_phone, category, items, int(fee), 'Verified Paid')
        )
        conn.commit()
        conn.close()

        return "<h1>രജിസ്ട്രേഷൻ വിജയകരമായി പൂർത്തിയായി! 🎉</h1><a href='/'>ഹോം പേജിലേക്ക് പോവുക</a>"
    except Exception as e:
        return f"പിഴവ്: {str(e)}", 500

@app.route('/participants', methods=['GET'])
def get_participants():
    conn = sqlite3.connect('kalolsavam.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM participants')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/improvements', methods=['GET'])
def get_improvements():
    conn = sqlite3.connect('kalolsavam.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM improvements')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.json
    password = data.get('password')
    if password == 'ajay':
        session['is_admin'] = True
        return jsonify({"success": True, "message": "Admin Login Success!"})
    return jsonify({"success": False, "message": "തെറ്റായ പാസ്‌വേഡ്!"}), 401

@app.route('/update-participant/<int:id>', methods=['PUT'])
def update_participant(id):
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Unauthorized!"}), 403

    data = request.json
    marks = int(data.get('marks', 0))
    total_marks = int(data.get('total_marks', 100))
    quiz_marks = float(data.get('quiz_marks', 0))
    re_exam_marks = float(data.get('re_exam_marks', 0))

    conn = sqlite3.connect('kalolsavam.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(imp_marks) as total_imp FROM improvements WHERE participant_id = ?', (id,))
    imp_row = cursor.fetchone()
    imp_marks = imp_row['total_imp'] if imp_row['total_imp'] else 0

    net_marks = marks + quiz_marks + imp_marks + re_exam_marks
    max_possible_marks = total_marks + 50 + 80 # കലാമേള + ക്വിസ്/ഇംപ്രൂവ്മെന്റ് + സെ എക്സാം
    percentage = (net_marks / max_possible_marks) * 100 if max_possible_marks > 0 else 0

    if percentage >= 90:
        grade = 'A+ (Full A+ Achieved)'
    elif percentage >= 80:
        grade = 'A (Passed)'
    elif percentage >= 70:
        grade = 'B+ (Passed)'
    elif percentage >= 60:
        grade = 'B (Passed)'
    elif percentage >= 40:
        grade = 'C (Passed)'
    else:
        grade = 'Failed - Re-Exam Required'

    cursor.execute('''
        UPDATE participants
        SET marks = ?, total_marks = ?, quiz_marks = ?, re_exam_marks = ?, percentage = ?, grade = ?
        WHERE id = ?
    ''', (marks, max_possible_marks, quiz_marks, re_exam_marks, round(percentage, 2), grade, id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "വിവരങ്ങൾ വിജയകരമായി അപ്ഡേറ്റ് ചെയ്തു!"})

@app.route('/add-improvement', methods=['POST'])
def add_improvement():
    data = request.json
    participant_id = data.get('participant_id')
    student_name = data.get('student_name')
    imp_marks = float(data.get('imp_marks', 0))

    conn = sqlite3.connect('kalolsavam.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO improvements (participant_id, student_name, imp_marks, imp_total, remarks)
        VALUES (?, ?, ?, 50, 'Improved')
    ''', (participant_id, student_name, imp_marks))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "ഇംപ്രൂവ്മെന്റ് മാർക്ക് ചേർത്തു!"})

# സെ എക്സാം മാർക്ക് സേവ് ചെയ്യാൻ API
@app.route('/add-re-exam', methods=['POST'])
def add_re_exam():
    data = request.json
    participant_id = data.get('participant_id')
    re_marks = float(data.get('re_marks', 0))

    conn = sqlite3.connect('kalolsavam.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE participants SET re_exam_marks = ? WHERE id = ?
    ''', (re_marks, participant_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "സെ എക്സാം മാർക്ക് വിജയകരമായി അപ്ഡേറ്റ് ചെയ്തു!"})

# ഡിജിറ്റൽ സർട്ടിഫിക്കറ്റ് പേജ് റൂട്ട്
@app.route('/certificate/<int:id>')
def view_certificate(id):
    conn = sqlite3.connect('kalolsavam.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM participants WHERE id = ?', (id,))
    student = cursor.fetchone()

    cursor.execute('SELECT SUM(imp_marks) as total_imp FROM improvements WHERE participant_id = ?', (id,))
    imp_row = cursor.fetchone()
    imp_marks = imp_row['total_imp'] if imp_row['total_imp'] else 0

    conn.close()

    if not student:
        return "<h3>കുട്ടിയെ കണ്ടെത്താനായില്ല!</h3>", 404

    net_score = student['marks'] + student['quiz_marks'] + imp_marks + student['re_exam_marks']
    max_limit = student['total_marks']
    required_for_full_aplus = round(max_limit * 0.90, 2)

    cert_html = f"""
    <!DOCTYPE html>
    <html lang="ml">
    <head>
        <meta charset="UTF-8">
        <title>ഡിജിറ്റൽ സർട്ടിഫിക്കറ്റ് - {student['name']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #eef2f3; padding: 20px; text-align: center; }}
            .certificate-box {{
                max-width: 750px; background: white; margin: auto; padding: 30px;
                border: 10px solid #007bff; border-radius: 15px; box-shadow: 0 0 20px rgba(0,0,0,0.2);
            }}
            h1 {{ color: #007bff; }}
            .details {{ text-align: left; margin: 20px 0; font-size: 15px; line-height: 1.6; }}
            .details span {{ font-weight: bold; color: #333; }}
            .scores-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            .scores-table th, .scores-table td {{ border: 1px solid #ddd; padding: 8px; text-align: center; font-size: 14px; }}
            .scores-table th {{ background: #007bff; color: white; }}
            .footer {{ margin-top: 30px; display: flex; justify-content: space-between; align-items: center; }}
            .sign {{ font-family: 'Brush Script MT', cursive; font-size: 24px; color: #d9534f; border-top: 2px dashed #333; padding-top: 5px; }}
            .pass-status {{ font-size: 16px; font-weight: bold; margin-top: 15px; padding: 10px; border-radius: 5px; }}
            .criteria-box {{ background: #fff3cd; padding: 10px; border-radius: 5px; margin-top: 15px; font-size: 13px; color: #856404; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="certificate-box">
            <h2>🏫 സ്കൂൾ കലയോത്സവം & എഥിക്കൽ ഹാക്കിംഗ് അക്കാദമി</h2>
            <h3>ഡിജിറ്റൽ പെർഫോമൻസ് സർട്ടിഫിക്കറ്റ് & മാർക്ക് ഷീറ്റ്</h3>
            <hr>
            <div class="details">
                <p>റജിസ്ട്രേഷൻ ID: <span>#{student['id']}</span> | കുട്ടിയുടെ പേര്: <span>{student['name']}</span></p>
                <p>അച്ഛന്റെ പേര്: <span>{student['father_name']}</span> | അമ്മയുടെ ഫോൺ: <span>{student['mother_phone']}</span></p>
                <p>വിഭാഗം & ഇനങ്ങൾ: <span>{student['category']} - {student['items']}</span></p>
            </div>

            <table class="scores-table">
                <tr>
                    <th>പരീക്ഷാ വിഭാഗം</th>
                    <th>ലഭിച്ച മാർക്ക്</th>
                </tr>
                <tr>
                    <td>കലാമേള മാർക്ക്</td>
                    <td>{student['marks']}</td>
                </tr>
                <tr>
                    <td>ക്വിസ് മാർക്ക് (?)</td>
                    <td>{student['quiz_marks']}</td>
                </tr>
                <tr>
                    <td>ഇംപ്രൂവ്മെന്റ് മാർക്ക്</td>
                    <td>{imp_marks}</td>
                </tr>
                <tr>
                    <td>സെ എക്സാം മാർക്ക് (80 ചോദ്യങ്ങൾ)</td>
                    <td>{student['re_exam_marks']}</td>
                </tr>
                <tr>
                    <td><b>ആകെ നേടിയ മാർക്ക് / മാക്സിമം മാർക്ക്</b></td>
                    <td><b>{net_score} / {max_limit}</b></td>
                </tr>
                <tr>
                    <td><b>ശതമാനവും ഗ്രേഡും</b></td>
                    <td><b>{student['percentage']}% ({student['grade']})</b></td>
                </tr>
            </table>

            <div class="criteria-box">
                📌 <b>ഫുൾ A+ ക്രൈറ്റീരിയ:</b> ഫുൾ A+ ലഭിക്കാൻ ആകെ മാക്സിമം മാർക്കായ {max_limit}-ൽ കുറഞ്ഞത് <b>{required_for_full_aplus} മാർക്ക് (90%)</b> നേടിയിരിക്കണം.
            </div>

            <div class="pass-status" style="background: {'#d4edda' if 'A+' in student['grade'] or 'Passed' in student['grade'] else '#f8d7da'}; color: {'#155724' if 'A+' in student['grade'] or 'Passed' in student['grade'] else '#721c24'};">
                സ്റ്റാറ്റസ്: {student['grade']}
            </div>

            <div class="footer">
                <div>
                    <p>സ്ഥലം: സ്കൂൾ അങ്കണം</p>
                    <p>ഡിജിറ്റൽ ഐഡി: SCH-2026-ID{student['id']}</p>
                </div>
                <div>
                    <div class="sign">Prof. Ajay Kumar</div>
                    <p><b>ഡിജിറ്റൽ പ്രിൻസിപ്പൽ / ഹെഡ്</b></p>
                </div>
            </div>
        </div>
        <br>
        <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer;">🖨️ സർട്ടിഫിക്കറ്റ് പ്രിന്റ് / ഡൗൺലോഡ് ചെയ്യുക</button>
    </body>
    </html>
    """
    return render_template_string(cert_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

