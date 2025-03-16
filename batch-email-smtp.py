def update_unsubscribe_links(html_content, text_content, email):
    """
    Update unsubscribe links in email content to include the recipient's email.
    
    Args:
        html_content: HTML email content
        text_content: Plain text email content
        email: Recipient's email address
        
    Returns:
        Tuple of (updated_html, updated_text)
    """
    unsubscribe_url = f"https://example.com/unsubscribe?email={email}"
    
    if html_content:
        # Replace generic unsubscribe URL with personalized one in HTML
        html_content = html_content.replace(
            "https://example.com/unsubscribe?email={email}", 
            unsubscribe_url
        )
    
    if text_content:
        # Replace generic unsubscribe URL with personalized one in text
        text_content = text_content.replace(
            "https://example.com/unsubscribe?email={email}", 
            unsubscribe_url
        )
    
    return html_content, text_content    def check_subscription_status(self, email_list: List[str]) -> Dict[str, bool]:
        """
        Check which emails are subscribed and which are unsubscribed.
        
        Args:
            email_list: List of email addresses to check
            
        Returns:
            Dict mapping email addresses to subscription status (True=subscribed, False=unsubscribed)
        """
        # Connect to the subscription database
        try:
            conn = sqlite3.connect('email_subscribers.db')
            cursor = conn.cursor()
            
            # Prepare a dictionary to hold results
            subscription_status = {}
            
            # Check each email
            for email in email_list:
                cursor.execute('SELECT subscribed FROM subscribers WHERE email = ?', (email,))
                result = cursor.fetchone()
                
                if result is None:
                    # Email not found in database, default to unsubscribed to be safe
                    subscription_status[email] = False
                    logging.warning(f"Email not found in subscriber database: {email}")
                else:
                    # Email found, set status based on database value
                    subscription_status[email] = bool(result[0])
            
            conn.close()
            return subscription_status
            
        except Exception as e:
            logging.error(f"Error checking subscription status: {str(e)}")
            # If there's an error, return all as unsubscribed to be safe
            return {email: False for email in email_list}
    
    def filter_unsubscribed(self, email_list: List[str]) -> List[str]:
        """
        Filter out unsubscribed email addresses.
        
        Args:
            email_list: List of email addresses to filter
            
        Returns:
            List of subscribed email addresses only
        """
        status_dict = self.check_subscription_status(email_list)
        return [email for email in email_list if status_dict.get(email, False)]import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import csv
import time
import logging
import sqlite3
from typing import List, Dict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='email_log.txt'
)

class BatchEmailSender:
    def __init__(self, smtp_server: str, port: int, email: str, password: str):
        """
        Initialize the email sender with SMTP server details.
        
        Args:
            smtp_server: SMTP server address (e.g., 'smtp.gmail.com')
            port: SMTP port (typically 587 for TLS)
            email: Your email address
            password: Your app password from Google Account -> Security -> App passwords
                     (With 2-step verification enabled, regular passwords won't work)
        """
        self.smtp_server = smtp_server
        self.port = port
        self.email = email
        self.password = password
        self.session = None
    
    def connect(self):
        """Establish connection to the SMTP server."""
        try:
            # Create SMTP session
            self.session = smtplib.SMTP(self.smtp_server, self.port)
            self.session.ehlo()
            # Start TLS encryption
            self.session.starttls()
            # Re-identify ourselves over TLS connection
            self.session.ehlo()
            # Login to server
            self.session.login(self.email, self.password)
            logging.info("Successfully connected to SMTP server")
            return True
        except Exception as e:
            logging.error(f"Connection error: {str(e)}")
            return False
    
    def disconnect(self):
        """Close the SMTP connection."""
        if self.session:
            self.session.quit()
            self.session = None
            logging.info("Disconnected from SMTP server")
    
    def send_email(self, recipient: str, subject: str, body_html: str, 
                   body_text: str = None, bcc: List[str] = None) -> bool:
        """
        Send a single email.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body_html: HTML content of the email
            body_text: Plain text version (optional)
            bcc: List of BCC recipients (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.session:
            if not self.connect():
                return False
        
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Set BCC recipients (not visible in email headers)
            bcc_recipients = bcc if bcc else []
            
            # Attach parts to the message
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))
            msg.attach(MIMEText(body_html, 'html'))
            
            # Determine all recipients for sending
            all_recipients = [recipient]
            if bcc_recipients:
                all_recipients.extend(bcc_recipients)
            
            # Send the message
            self.session.sendmail(self.email, all_recipients, msg.as_string())
            logging.info(f"Email sent to {recipient} (with {len(bcc_recipients)} BCC recipients)")
            return True
        except Exception as e:
            logging.error(f"Error sending email to {recipient}: {str(e)}")
            # Try to reconnect in case of connection issues
            self.connect()
            return False
    
    def send_batch_from_csv(self, csv_path: str, html_template: str, 
                           text_template: str = None, subject_template: str = None,
                           delay: int = 1, batch_size: int = 50, use_bcc: bool = True,
                           check_unsubscribed: bool = True) -> Dict[str, int]:
        """
        Send batch emails using data from a CSV file.
        
        Args:
            csv_path: Path to CSV file with recipient data
            html_template: HTML email template with {placeholders}
            text_template: Plain text template with {placeholders} (optional)
            subject_template: Subject template with {placeholders} (optional)
            delay: Delay between emails in seconds (to avoid rate limits)
            batch_size: Number of recipients to include in each BCC batch (when use_bcc=True)
            use_bcc: If True, sends emails in batches using BCC (ideal for marketing emails)
            check_unsubscribed: If True, checks subscription database and skips unsubscribed emails
            
        Returns:
            Dict with count of successful and failed emails
        """
        if not self.connect():
            return {"success": 0, "failed": 0, "skipped": 0}
        
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                all_rows = list(reader)
                
                if use_bcc:
                    # Group recipients into batches for BCC sending
                    for i in range(0, len(all_rows), batch_size):
                        batch = all_rows[i:i+batch_size]
                        
                        # Skip empty batches
                        if not batch:
                            continue
                        
                        # Create list of recipient emails for this batch
                        batch_emails = []
                        for row in batch:
                            if 'email' in row and row['email'].strip():
                                batch_emails.append(row['email'].strip())
                        
                        if not batch_emails:
                            continue
                        
                        # Filter out unsubscribed email addresses if requested
                        if check_unsubscribed:
                            original_count = len(batch_emails)
                            batch_emails = self.filter_unsubscribed(batch_emails)
                            skipped = original_count - len(batch_emails)
                            results["skipped"] += skipped
                            
                            if not batch_emails:  # Skip if all recipients were unsubscribed
                                logging.info(f"All recipients in batch were unsubscribed, skipping batch")
                                continue
                        
                        # Use the first row for template variables
                        # (since BCC recipients all get the same content)
                        template_row = batch[0]
                        
                        # Process templates (no personalization in BCC mode)
                        email_html = html_template
                        email_text = text_template
                        email_subject = subject_template or "Important Information"
                        
                        # Replace only general placeholders, not recipient-specific ones
                        for key, value in template_row.items():
                            if key != 'email' and key != 'first_name' and key != 'last_name':
                                if email_html:
                                    email_html = email_html.replace(f"{{{key}}}", value)
                                if email_text:
                                    email_text = email_text.replace(f"{{{key}}}", value)
                                if email_subject:
                                    email_subject = email_subject.replace(f"{{{key}}}", value)
                        
                        # Remove any remaining personalization placeholders
                        if email_html:
                            email_html = email_html.replace("{first_name}", "Valued Customer")
                            email_html = email_html.replace("{last_name}", "")
                            email_html = email_html.replace("{email}", "")
                        if email_text:
                            email_text = email_text.replace("{first_name}", "Valued Customer")
                            email_text = email_text.replace("{last_name}", "")
                            email_text = email_text.replace("{email}", "")
                        
                        # Send to yourself with all recipients in BCC
                        success = self.send_email(
                            recipient=self.email,  # Send to yourself
                            subject=email_subject,
                            body_html=email_html,
                            body_text=email_text,
                            bcc=batch_emails  # All recipients in BCC
                        )
                        
                        if success:
                            results["success"] += len(batch_emails)
                        else:
                            results["failed"] += len(batch_emails)
                        
                        # Add delay between batches
                        if delay > 0 and i + batch_size < len(all_rows):
                            time.sleep(delay)
                else:
                    # Individual email sending logic
                    for row in all_rows:
                        # Check if email address exists in the row
                        if 'email' not in row:
                            logging.error(f"Missing email field in row: {row}")
                            results["failed"] += 1
                            continue
                        
                        recipient = row['email'].strip()
                        
                        # Check if recipient is unsubscribed
                        if check_unsubscribed:
                            subscription_status = self.check_subscription_status([recipient])
                            if not subscription_status.get(recipient, False):
                                logging.info(f"Skipping unsubscribed recipient: {recipient}")
                                results["skipped"] += 1
                                continue
                        
                        # Process templates
                        email_html = html_template
                        email_text = text_template
                        email_subject = subject_template or "Important Information"
                        
                        # Replace placeholders in templates with actual data
                        for key, value in row.items():
                            if email_html:
                                email_html = email_html.replace(f"{{{key}}}", value)
                            if email_text:
                                email_text = email_text.replace(f"{{{key}}}", value)
                            if email_subject:
                                email_subject = email_subject.replace(f"{{{key}}}", value)
                        
                        # Send email (with personalized unsubscribe link in individual mode)
                        
                        # Add personalized unsubscribe link
                        personalized_html, personalized_text = update_unsubscribe_links(
                            email_html, email_text, recipient
                        )
                        
                        success = self.send_email(
                            recipient=recipient,
                            subject=email_subject,
                            body_html=personalized_html,
                            body_text=personalized_text
                        )
                        
                        if success:
                            results["success"] += 1
                        else:
                            results["failed"] += 1
                        
                        # Add delay between emails
                        if delay > 0:
                            time.sleep(delay)
        
        except Exception as e:
            logging.error(f"Batch processing error: {str(e)}")
        
        finally:
            self.disconnect()
            
        return results


# Example usage
if __name__ == "__main__":
    # Google Workspace SMTP settings
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    # Google Workspace credentials
    # IMPORTANT: Since you have 2-step verification enabled, you MUST use an app password
    # Get an app password from: https://myaccount.google.com/apppasswords
    EMAIL = "your.email@yourdomain.com"  # Your Google Workspace email
    
    # This must be an app password, NOT your regular account password
    # App passwords are 16 characters without spaces
    PASSWORD = "abcdefghijklmnop"  # Replace with your generated app password
    
    # Create sender
    sender = BatchEmailSender(SMTP_SERVER, SMTP_PORT, EMAIL, PASSWORD)
    
    # HTML Email Template Example for Marketing
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #4CAF50; padding: 20px; text-align: center; color: white; }
            .content { padding: 20px; background-color: #f9f9f9; }
            .button { background-color: #4CAF50; color: white; padding: 12px 20px; text-decoration: none; display: inline-block; border-radius: 4px; margin: 20px 0; }
            .footer { font-size: 12px; color: #777; margin-top: 20px; text-align: center; }
            .social { margin-top: 15px; }
            .social a { margin: 0 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Special Offer!</h1>
            </div>
            <div class="content">
                <h2>Hello {first_name}!</h2>
                <p>{marketing_message}</p>
                <p>Campaign ID: {campaign_id}</p>
                <center><a href="https://example.com/shop" class="button">SHOP NOW</a></center>
                <p>Don't miss out on this limited-time offer!</p>
            </div>
            <div class="footer">
                <p>© 2025 Your Company. All rights reserved.</p>
                <p>This is a marketing email sent to our subscribers.</p>
                <p>To unsubscribe, <a href="https://example.com/unsubscribe?email={email}">click here</a>.</p>
                <div class="social">
                    <a href="https://facebook.com/yourcompany">Facebook</a>
                    <a href="https://instagram.com/yourcompany">Instagram</a>
                    <a href="https://twitter.com/yourcompany">Twitter</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_template = """
    SPECIAL OFFER!
    
    Hello {first_name}!
    
    {marketing_message}
    
    Campaign ID: {campaign_id}
    
    SHOP NOW: https://example.com/shop
    
    Don't miss out on this limited-time offer!
    
    © 2025 Your Company. All rights reserved.
    This is a marketing email sent to our subscribers.
    
    To unsubscribe, visit: https://example.com/unsubscribe?email={email}
    """
    
    # Subject template
    subject_template = "Special Offer Inside! 🎁 {campaign_id}"
    
    # Path to your CSV file with recipient data
    csv_path = "examples/recipients.csv"
    
    # Send batch emails using BCC method for marketing emails
    results = sender.send_batch_from_csv(
        csv_path=csv_path,
        html_template=html_template,
        text_template=text_template,
        subject_template=subject_template,
        delay=2,  # 2 seconds between batches to avoid rate limits
        batch_size=50,  # Send to 50 recipients at a time via BCC
        use_bcc=True,  # Use BCC method for privacy and efficiency
        check_unsubscribed=True  # Check against unsubscribe database
    )
    
    print(f"Batch email results: {results['success']} successful, {results['failed']} failed, {results['skipped']} skipped (unsubscribed)")