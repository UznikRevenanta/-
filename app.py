from flask import Flask, render_template, request
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

DB_PATH = os.path.join('/tmp', 'database.db') if os.path.exists('/tmp') else 'database.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT NOT NULL,
            service_name TEXT NOT NULL,
            prev_reading REAL,
            curr_reading REAL,
            tariff REAL,
            total_sum REAL,
            date_payment TEXT
        )
    ''')
    conn.commit()
    conn.close()  
    
@app.before_request
def before_request():
    init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    result_message = ""

    if request.method == 'POST':
        try:
            fio = request.form['fio']
            service_name = request.form['service_name']
            curr_reading = float(request.form['curr_reading'])
            tariff = float(request.form['tariff'])

           
            cursor.execute('''
                SELECT curr_reading FROM payments 
                WHERE fio = ? AND service_name = ? 
                ORDER BY id DESC LIMIT 1
            ''', (fio, service_name))
            
            row = cursor.fetchone()
            if row:
                prev_reading = row[0]
            else:
                prev_reading = 0.0

            if curr_reading < prev_reading:
                result_message = f"Ошибка: Текущие показания меньше предыдущих ({prev_reading})!"
            else:
                consumption = curr_reading - prev_reading
                total_sum = consumption * tariff
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

                cursor.execute('''
                    INSERT INTO payments (fio, service_name, prev_reading, curr_reading, tariff, total_sum, date_payment)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (fio, service_name, prev_reading, curr_reading, tariff, total_sum, current_date))
                conn.commit()
                
                result_message = f"Успешно! Для услуги '{service_name}' итого к оплате: {total_sum:.2f} руб."
        except ValueError:
            result_message = "Ошибка: Введите корректные числа!"

   
    cursor.execute("SELECT * FROM payments ORDER BY id DESC")
    all_payments = cursor.fetchall()
    conn.close()

    return render_template('index.html', result=result_message, payments=all_payments)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
