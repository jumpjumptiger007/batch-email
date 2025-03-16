# Batch Email Marketing System with Unsubscribe Management

An open-source solution for sending batch marketing emails via Google Workspace SMTP with proper unsubscribe handling, subscription tracking, and email list management. Built for marketers and developers who need a transparent, customizable email system that respects recipient preferences.

## Features

- Send batch marketing emails using BCC for recipient privacy
- Track and respect unsubscribe preferences
- Professional unsubscribe page for recipients
- Subscription database with reason tracking
- Personalized unsubscribe links
- Secure authentication with Google Workspace
- Email template personalization
- Rate limiting to avoid sending limits
- CSV-based recipient management

## Requirements

- Python 3.6+
- Google Workspace account with SMTP access
- App Password for your Google account (2-step verification required)

## Included Example Files

This repository includes several example files to help you get started:

1. **`examples/recipients.csv`** - Sample recipient list with email addresses and personalization fields
2. **`examples/filtered_output.csv`** - Pre-filtered version with only subscribed recipients
3. **`email_subscribers.db`** - Example SQLite database with sample subscription data

You can use these files to:
- Test the system without creating your own data
- Understand the expected file formats
- Have a starting point for your own email marketing campaigns

When you're ready for production use, you can:
- Replace the example recipients with your actual marketing list
- Use the scripts to maintain your own subscription database
- Create custom email templates for your branding

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/jumpjumptiger007/batch-email.git
   cd batch-email
   ```

2. Install dependencies:
   ```
   pip install flask
   ```

3. Use the example database or create your own:
   ```
   # If you want to use the provided example database:
   # The repository includes email_subscribers.db with sample data
   
   # Or create a new database:
   python create-database.py
   ```

4. Create your email templates and use the provided example recipient lists

## System Components

### 1. Batch Email Sender (`batch-email-smtp.py`)

Sends marketing emails in batches via Google's SMTP server, respecting subscription preferences.

```python
from batch_email_smtp import BatchEmailSender

# Initialize the sender
sender = BatchEmailSender(
    smtp_server="smtp.gmail.com",
    port=587,
    email="your.email@yourdomain.com",
    password="your-app-password"  # App password, not regular password
)

# Send batch emails
results = sender.send_batch_from_csv(
    # You can use either the original list or the pre-filtered list:
    csv_path="examples/recipients.csv",  # Original list with 'subscribed' column
    # csv_path="examples/filtered_output.csv",  # Pre-filtered list
    html_template=html_template,
    text_template=text_template,
    subject_template="Special Offer Inside! 🎁 {campaign_id}",
    use_bcc=True,
    batch_size=50,
    check_unsubscribed=True  # Set to False if using filtered_output.csv
)

print(f"Results: {results['success']} sent, {results['failed']} failed, {results['skipped']} unsubscribed")
```

### 2. Unsubscribe Handler (`unsubscribe-handler.py`)

Flask web service that handles unsubscribe requests and manages subscriber preferences.

```
# Run the unsubscribe service
python unsubscribe-handler.py
```

### 3. Subscriber Database Manager (`sync-subscribers.py`)

Utilities for managing your subscriber database and keeping email lists in sync.

```
# Import subscribers from the example CSV
python sync-subscribers.py --import examples/recipients.csv

# Create a filtered list excluding unsubscribed recipients
python sync-subscribers.py --filter examples/recipients.csv filtered_output.csv

# Update the original CSV file with current subscription status
python sync-subscribers.py --update examples/recipients.csv

# One-step sync: Import new subscribers and update the CSV file
python sync-subscribers.py --sync-all
```

### 4. Database Setup (`create-database.py`)

Sets up the SQLite database for tracking subscriptions and unsubscribe reasons.

```
# Create or reset the database
python create-database.py
```

## Usage Guide

### Setting Up a Google App Password

Since you've enabled 2-step verification, you'll need an app password:

1. Go to your Google Account at https://myaccount.google.com/
2. Click on "Security" in the left panel
3. Under "Signing in to Google," click on "App passwords"
4. Select "Mail" and your device type
5. Generate and copy the 16-character password

### Preparing Your Email List

Create a CSV with at minimum these columns:
- `email`: Recipient email address
- `first_name`: Recipient's first name (for personalization)
- `last_name`: Recipient's last name (for personalization)

Additional columns can be used for template variables. You can use the sample file provided in the `examples/recipients.csv` as a starting point:

```csv
email,first_name,last_name,campaign_id,marketing_message
john.doe@example.com,John,Doe,SPRING2025,"Check out our spring collection with 20% off!"
```

The repository includes a complete example CSV in the `examples` folder that you can use as a template for your own recipient lists.

### Creating Email Templates

HTML Template Example:
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .header { background-color: #4CAF50; padding: 20px; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Special Offer!</h1>
    </div>
    <p>Hello {first_name}!</p>
    <p>{marketing_message}</p>
    <p>To unsubscribe, <a href="https://example.com/unsubscribe?email={email}">click here</a>.</p>
</body>
</html>
```

### Complete Workflow

1. **Initial Setup**:
   - Use the included example database or create your own: `python create-database.py`
   - If creating your own, import your marketing list: `python sync-subscribers.py --import examples/recipients.csv`
   - Set up the unsubscribe web service: `python unsubscribe-handler.py`

2. **Before Each Campaign** (Important):
   - Always run the sync command to update subscription status: `python sync-subscribers.py --sync-all`
   - This step is critical as the CSV file won't automatically update when users unsubscribe
   - The sync command ensures you don't send emails to people who have unsubscribed since your last campaign
   - Alternatively, use the pre-filtered example: `examples/filtered_output.csv`

3. **Sending the Campaign**:
   - Run the batch email sender with your templates and updated recipient list
   - You can use the provided filtered example: `examples/filtered_output.csv`
   - The sender will respect the 'subscribed' column in your CSV file
   - Monitor the logs for sending status

4. **After Sending**:
   - Keep the unsubscribe service running to collect unsubscribe requests
   - Review unsubscribe reasons to improve future campaigns
   - Next time you send a campaign, start again from step 2

## Unsubscribe Page Integration

1. Make sure the unsubscribe web service is running
2. In your email templates, include a personalized unsubscribe link:
   ```
   https://yourdomain.com/unsubscribe?email={email}
   ```
3. The system will automatically replace `{email}` with each recipient's email

## Best Practices

- Always include a clear unsubscribe link in every email
- Respect unsubscription requests promptly
- Keep your subscriber database up to date
- Use the `check_unsubscribed` parameter to prevent emails to unsubscribed users
- Add delays between batches to avoid hitting sending limits
- Test with small batches before sending to your entire list

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add some amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Areas for Contribution
- Additional email template examples
- Support for other email service providers
- Enhanced unsubscribe page templates
- Improved analytics for tracking open/click rates
- Localization of the unsubscribe page

## License

This project is licensed under the MIT License.

## Disclaimer

This software is provided as-is and should be used in compliance with email marketing laws and regulations, including but not limited to CAN-SPAM, GDPR, and CASL.