def update_original_csv(csv_path):
    """
    Update the original CSV file to reflect current subscription status.
    This modifies the original CSV file directly, adding a 'subscribed' column.
    
    Args:
        csv_path: Path to the original CSV file
    
    Returns:
        int: Number of unsubscribed users marked in the file
    """
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found")
        return 0
    
    conn = sqlite3.connect('email_subscribers.db')
    cursor = conn.cursor()
    
    # Create a backup of the original file
    backup_path = f"{csv_path}.backup"
    with open(csv_path, 'r', encoding='utf-8') as original:
        with open(backup_path, 'w', encoding='utf-8') as backup:
            backup.write(original.read())
    
    # Read all rows from the input CSV
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        rows = list(reader)
    
    # Add 'subscribed' to headers if it doesn't exist
    if 'subscribed' not in headers:
        headers.append('subscribed')
    
    # Update rows with subscription status
    unsubscribed_count = 0
    for row in rows:
        if 'email' not in row:
            row['subscribed'] = "1"  # Default to subscribed if no email
            continue
                
        email = row.get('email', '').strip()
        if not email:
            row['subscribed'] = "1"  # Default to subscribed if empty email
            continue
        
        # Check if subscribed
        cursor.execute('SELECT subscribed FROM subscribers WHERE email = ?', (email,))
        result = cursor.fetchone()
        
        if result is None:
            # Email not in database, add it as subscribed
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            cursor.execute(
                'INSERT INTO subscribers (email, first_name, last_name, subscribed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
                (email, first_name, last_name, 1, datetime.now(), datetime.now())
            )
            row['subscribed'] = "1"
        else:
            # Update row with current subscription status
            status = "1" if result[0] == 1 else "0"
            row['subscribed'] = status
            if status == "0":
                unsubscribed_count += 1
    
    # Write updated data back to the original file
    with open(csv_path, 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    conn.commit()
    conn.close()
    
    print(f"Updated {csv_path} with current subscription status")
    print(f"A backup of the original file was created at {backup_path}")
    
    return unsubscribed_count#!/usr/bin/env python3
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
    parser.add_argument('--update', dest='update_csv', help='Update the original CSV with subscription status')
    parser.add_argument('--sync-all', dest='sync_all', action='store_true',
                        help='Sync database and update the original CSV in one operation')
    
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
    
    if args.update_csv:
        unsubscribed = update_original_csv(args.update_csv)
        print(f"Updated CSV file, marked {unsubscribed} emails as unsubscribed")
    
    if args.sync_all:
        default_csv = "examples/recipients.csv"
        if os.path.exists(default_csv):
            # First import any new subscribers
            count = import_from_csv(default_csv)
            print(f"Imported {count} new subscribers to database")
            
            # Then update the CSV with current subscription status
            unsubscribed = update_original_csv(default_csv)
            print(f"Updated CSV file, marked {unsubscribed} emails as unsubscribed")
        else:
            print(f"Error: Default CSV file {default_csv} not found")
            print(f"Please use --update <csv_path> to specify a different file.")

if __name__ == "__main__":
    main()