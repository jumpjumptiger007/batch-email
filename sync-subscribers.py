#!/usr/bin/env python3
"""
Synchronizes your marketing CSV with the subscribers database
to ensure you're only emailing people who haven't unsubscribed.
"""

import sqlite3
import csv
import argparse
import os
from datetime import datetime

def init_db():
    """Initialize the subscriber database if it doesn't exist"""
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
    conn.commit()
    conn.close()

def import_from_csv(csv_path):
    """Import subscribers from CSV into database"""
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found")
        return 0
    
    conn = sqlite3.connect('email_subscribers.db')
    cursor = conn.cursor()
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if 'email' not in row:
                continue
            
            email = row.get('email', '').strip()
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            
            if not email:
                continue
            
            # Check if this email exists first
            cursor.execute('SELECT email, subscribed FROM subscribers WHERE email = ?', (email,))
            result = cursor.fetchone()
            
            if result is None:
                # Insert new subscriber
                cursor.execute(
                    'INSERT INTO subscribers (email, first_name, last_name, subscribed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (email, first_name, last_name, 1, datetime.now(), datetime.now())
                )
                count += 1
            # Note: We don't update existing records to preserve their subscription status
    
    conn.commit()
    conn.close()
    return count

def filter_unsubscribed(input_csv, output_csv):
    """
    Create a new CSV with only subscribed emails
    """
    if not os.path.exists(input_csv):
        print(f"Error: File {input_csv} not found")
        return 0
    
    conn = sqlite3.connect('email_subscribers.db')
    cursor = conn.cursor()
    
    # Read all rows from the input CSV
    with open(input_csv, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        rows = list(reader)
    
    # Create output CSV with the same headers
    with open(output_csv, 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        
        # Filter rows based on subscription status
        filtered_count = 0
        for row in rows:
            if 'email' not in row:
                continue
                
            email = row.get('email', '').strip()
            if not email:
                continue
            
            # Check if subscribed
            cursor.execute('SELECT subscribed FROM subscribers WHERE email = ?', (email,))
            result = cursor.fetchone()
            
            # Include row if subscribed or not found in database (default to include)
            if result is None or result[0] == 1:
                writer.writerow(row)
            else:
                filtered_count += 1
    
    conn.close()
    return filtered_count

def main():
    parser = argparse.ArgumentParser(description='Manage email subscribers')
    parser.add_argument('--import', dest='import_csv', help='Import subscribers from CSV file')
    parser.add_argument('--filter', dest='filter', nargs=2, metavar=('INPUT_CSV', 'OUTPUT_CSV'), 
                        help='Filter out unsubscribed emails from CSV file')
    
    args = parser.parse_args()
    
    # Initialize the database
    init_db()
    
    if args.import_csv:
        count = import_from_csv(args.import_csv)
        print(f"Imported {count} new subscribers to database")
    
    if args.filter:
        input_csv, output_csv = args.filter
        filtered = filter_unsubscribed(input_csv, output_csv)
        print(f"Created filtered CSV at {output_csv}, removed {filtered} unsubscribed emails")

if __name__ == "__main__":
    main()
