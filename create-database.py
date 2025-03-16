#!/usr/bin/env python3
"""
Creates and initializes the email_subscribers.db database with tables and sample data.
"""

import sqlite3
import os
from datetime import datetime

def create_database():
    """Create and initialize the subscriber database"""
    # Check if database already exists
    if os.path.exists('email_subscribers.db'):
        print("Database already exists. Do you want to recreate it? (y/n)")
        response = input().strip().lower()
        if response != 'y':
            print("Operation cancelled.")
            return False
        else:
            os.remove('email_subscribers.db')
            print("Existing database removed.")
    
    # Create a new database
    conn = sqlite3.connect('email_subscribers.db')
    cursor = conn.cursor()
    
    # Create subscribers table
    cursor.execute('''
    CREATE TABLE subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        first_name TEXT,
        last_name TEXT,
        subscribed BOOLEAN DEFAULT 1,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    ''')
    
    # Create unsubscribe_reasons table
    cursor.execute('''
    CREATE TABLE unsubscribe_reasons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        reason TEXT,
        comments TEXT,
        preference TEXT,
        unsubscribed_at TIMESTAMP
    )
    ''')
    
    # Create indices for faster lookups
    cursor.execute('CREATE INDEX idx_subscribers_email ON subscribers(email)')
    cursor.execute('CREATE INDEX idx_unsubscribe_reasons_email ON unsubscribe_reasons(email)')
    
    print("Database and tables created successfully.")
    
    # Add sample data if requested
    print("Do you want to add sample data? (y/n)")
    response = input().strip().lower()
    if response == 'y':
        add_sample_data(cursor)
    
    conn.commit()
    conn.close()
    
    return True

def add_sample_data(cursor):
    """Add sample subscribers to the database"""
    # Sample subscribed users
    sample_subscribers = [
        ('john.doe@example.com', 'John', 'Doe', 1),
        ('jane.smith@example.com', 'Jane', 'Smith', 1),
        ('michael.johnson@example.com', 'Michael', 'Johnson', 1),
        ('emily.davis@example.com', 'Emily', 'Davis', 1),
        ('david.wilson@example.com', 'David', 'Wilson', 1),
        ('sarah.brown@example.com', 'Sarah', 'Brown', 1),
        ('james.taylor@example.com', 'James', 'Taylor', 1),
        ('olivia.anderson@example.com', 'Olivia', 'Anderson', 1),
        ('william.martinez@example.com', 'William', 'Martinez', 1),
        ('emma.thomas@example.com', 'Emma', 'Thomas', 1),
    ]
    
    # Sample unsubscribed users
    sample_unsubscribed = [
        ('robert.jackson@example.com', 'Robert', 'Jackson', 0),
        ('sophia.white@example.com', 'Sophia', 'White', 0),
        ('joseph.harris@example.com', 'Joseph', 'Harris', 0),
    ]
    
    now = datetime.now()
    
    # Insert subscribed users
    for email, first_name, last_name, subscribed in sample_subscribers:
        cursor.execute(
            'INSERT INTO subscribers (email, first_name, last_name, subscribed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
            (email, first_name, last_name, subscribed, now, now)
        )
    
    # Insert unsubscribed users
    for email, first_name, last_name, subscribed in sample_unsubscribed:
        cursor.execute(
            'INSERT INTO subscribers (email, first_name, last_name, subscribed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
            (email, first_name, last_name, subscribed, now, now)
        )
    
    # Add some unsubscribe reasons
    unsubscribe_reasons = [
        ('robert.jackson@example.com', 'too-many', 'Emails were too frequent', 'unsubscribe-all', now),
        ('sophia.white@example.com', 'not-relevant', 'Content wasn\'t relevant to me', 'unsubscribe-all', now),
        ('joseph.harris@example.com', 'other', 'Moving to a new company', 'unsubscribe-all', now),
    ]
    
    for email, reason, comments, preference, timestamp in unsubscribe_reasons:
        cursor.execute(
            'INSERT INTO unsubscribe_reasons (email, reason, comments, preference, unsubscribed_at) VALUES (?, ?, ?, ?, ?)',
            (email, reason, comments, preference, timestamp)
        )
    
    print(f"Added {len(sample_subscribers)} subscribed and {len(sample_unsubscribed)} unsubscribed sample users.")

def check_database():
    """Check if the database exists and has the expected tables"""
    if not os.path.exists('email_subscribers.db'):
        print("Database does not exist yet.")
        return False
    
    try:
        conn = sqlite3.connect('email_subscribers.db')
        cursor = conn.cursor()
        
        # Check for subscribers table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscribers'")
        if not cursor.fetchone():
            print("Subscribers table does not exist.")
            conn.close()
            return False
        
        # Check for unsubscribe_reasons table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='unsubscribe_reasons'")
        if not cursor.fetchone():
            print("Unsubscribe_reasons table does not exist.")
            conn.close()
            return False
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM subscribers")
        subscriber_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM unsubscribe_reasons")
        reason_count = cursor.fetchone()[0]
        
        print(f"Database exists with {subscriber_count} subscribers and {reason_count} unsubscribe reasons.")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error checking database: {str(e)}")
        return False

def main():
    print("Email Subscriber Database Setup")
    print("===============================")
    
    if check_database():
        print("\nThe database already exists. What would you like to do?")
        print("1. Use existing database")
        print("2. Recreate database (this will delete all existing data)")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            print("Using existing database.")
        elif choice == '2':
            create_database()
        else:
            print("Exiting without changes.")
    else:
        print("\nNo database found. Creating new database...")
        create_database()

if __name__ == "__main__":
    main()
