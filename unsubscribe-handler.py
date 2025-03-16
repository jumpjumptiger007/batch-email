from flask import Flask, request, jsonify, render_template, redirect
import sqlite3
import csv
from datetime import datetime
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='unsubscribe_log.txt'
)

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('email_subscribers.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        first_name TEXT,
        last_name TEXT,
        subscribed BOOLEAN DEFAULT 1,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS unsubscribe_reasons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        reason TEXT,
        comments TEXT,
        preference TEXT,
        unsubscribed_at TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

# Route for handling the unsubscribe form submission
@app.route('/api/unsubscribe', methods=['POST'])
def unsubscribe():
    try:
        data = request.json
        email = data.get('email')
        reasons = data.get('reasons', [])
        comments = data.get('comments', '')
        preference = data.get('preference', 'unsubscribe-all')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        # Connect to database
        conn = sqlite3.connect('email_subscribers.db')
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute('SELECT * FROM subscribers WHERE email = ?', (email,))
        subscriber = cursor.fetchone()
        
        if not subscriber:
            conn.close()
            return jsonify({'success': False, 'message': 'Email not found in our database'}), 404
        
        # Update subscriber status based on preference
        if preference == 'unsubscribe-all':
            cursor.execute(
                'UPDATE subscribers SET subscribed = 0, updated_at = ? WHERE email = ?',
                (datetime.now(), email)
            )
        elif preference == 'less-frequent':
            # In a real implementation, you would set a frequency preference
            cursor.execute(
                'UPDATE subscribers SET updated_at = ? WHERE email = ?',
                (datetime.now(), email)
            )
        
        # Store the unsubscribe reason
        for reason in reasons:
            cursor.execute(
                'INSERT INTO unsubscribe_reasons (email, reason, comments, preference, unsubscribed_at) VALUES (?, ?, ?, ?, ?)',
                (email, reason, comments, preference, datetime.now())
            )
        
        conn.commit()
        
        # Export to unsubscribe list CSV for reference
        export_to_csv(email, reasons, comments, preference)
        
        # Log the unsubscribe
        logging.info(f"Unsubscribe request: {email}, Preference: {preference}, Reasons: {reasons}")
        
        conn.close()
        return jsonify({'success': True, 'message': 'Successfully unsubscribed'})
    
    except Exception as e:
        logging.error(f"Error processing unsubscribe: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

def export_to_csv(email, reasons, comments, preference):
    """Export unsubscribe data to CSV for backup and reference"""
    file_exists = os.path.isfile('unsubscribes.csv')
    
    with open('unsubscribes.csv', 'a', newline='') as csvfile:
        fieldnames = ['email', 'reasons', 'comments', 'preference', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'email': email,
            'reasons': ', '.join(reasons),
            'comments': comments,
            'preference': preference,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

# Serve the unsubscribe page
@app.route('/unsubscribe', methods=['GET'])
def unsubscribe_page():
    email = request.args.get('email', '')
    return render_template('unsubscribe.html', email=email)

# Route to check email status (if someone wants to confirm they're unsubscribed)
@app.route('/api/check-status', methods=['GET'])
def check_status():
    email = request.args.get('email')
    
    if not email:
        return jsonify({'subscribed': False, 'message': 'Email parameter is required'}), 400
    
    conn = sqlite3.connect('email_subscribers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT subscribed FROM subscribers WHERE email = ?', (email,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return jsonify({'subscribed': bool(result[0])})
    else:
        return jsonify({'subscribed': False, 'message': 'Email not found in database'})

# Import an existing email list
@app.route('/api/import-subscribers', methods=['POST'])
def import_subscribers():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    try:
        # Read and process the CSV file
        csv_content = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(csv_content)
        
        conn = sqlite3.connect('email_subscribers.db')
        cursor = conn.cursor()
        
        count = 0
        for row in reader:
            if 'email' not in row:
                continue
                
            email = row.get('email', '').strip()
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            
            if not email:
                continue
                
            try:
                cursor.execute(
                    'INSERT OR IGNORE INTO subscribers (email, first_name, last_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                    (email, first_name, last_name, datetime.now(), datetime.now())
                )
                count += 1
            except Exception as e:
                logging.error(f"Error importing subscriber {email}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Successfully imported {count} subscribers'})
    
    except Exception as e:
        logging.error(f"Error importing subscribers: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Run the application
if __name__ == '__main__':
    app.run(debug=True, port=5000)
