from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

PRIVACY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - UM CRM</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            line-height: 1.6;
            color: #333;
        }
        h1 { color: #1a1a1a; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        h2 { color: #2a2a2a; margin-top: 30px; }
        h3 { color: #444; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background: #f5f5f5; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
        .last-updated { color: #666; font-style: italic; }
        ul { padding-left: 20px; }
        li { margin: 8px 0; }
    </style>
</head>
<body>
    <h1>Privacy Policy</h1>
    <p class="last-updated">Last Updated: April 20, 2026</p>
    
    <p>This Privacy Policy describes how we collect, use, and disclose your information when you use the UM CRM application.</p>

    <h2>1. Information We Collect</h2>
    
    <h3>User Account Data</h3>
    <ul>
        <li>Email address (login identifier)</li>
        <li>Password (stored as bcrypt hash)</li>
        <li>Full name</li>
        <li>Role</li>
    </ul>

    <h3>Google OAuth Data</h3>
    <ul>
        <li>Google email address</li>
        <li>Google access token and refresh token</li>
        <li>Gmail watch expiration and history ID</li>
        <li>Calendar access token and refresh token</li>
    </ul>

    <h3>WhatsApp Business Data</h3>
    <ul>
        <li>Phone number ID and display phone number</li>
        <li>WhatsApp access token</li>
        <li>Verify token</li>
    </ul>

    <h3>Contact Information</h3>
    <ul>
        <li>Name, email address, phone number</li>
        <li>Company name</li>
        <li>Notes</li>
    </ul>

    <h3>Email Data</h3>
    <ul>
        <li>Gmail message ID and thread ID</li>
        <li>Subject, from/to email addresses</li>
        <li>Email snippet (up to 500 characters)</li>
        <li>Full email body (up to 50,000 characters)</li>
        <li>HTML email content</li>
        <li>Label IDs, history ID, read status</li>
        <li>Received timestamp</li>
    </ul>

    <h3>CRM Records</h3>
    <ul>
        <li><strong>Opportunities</strong>: Title, deal value, stage, contact, assigned user, expected close date</li>
        <li><strong>Tasks</strong>: Title, description, status, priority, due date</li>
        <li><strong>Activities</strong>: Type, description, source, scheduled time</li>
    </ul>

    <h2>2. How Information is Used</h2>
    <p>We use your information to:</p>
    <ul>
        <li>Provide and maintain the CRM services</li>
        <li>Authenticate user accounts</li>
        <li>Integrate with Google Gmail and Calendar</li>
        <li>Enable WhatsApp Business messaging</li>
        <li>Manage customer relationships</li>
        <li>Provide automated support and AI-powered features</li>
        <li>Personalize your experience</li>
    </ul>

    <h2>3. Data Retention</h2>
    <p>We retain your data for as long as your account is active or as needed to provide services. You may request deletion at any time.</p>

    <h2>4. Data Deletion</h2>
    <p>To request deletion of your data, please contact us at:</p>
    <p><strong>Email</strong>: nelz020513@gmail.com</p>
    
    <p>Include "Data Deletion Request" in the subject line. We will:</p>
    <ol>
        <li>Verify your identity</li>
        <li>Delete your data from our active database within 30 days</li>
    </ol>
    
    <p><strong>Note</strong>: Account deletion requires contacting the developer directly at nelz020513@gmail.com. We do not provide self-service account deletion.</p>

    <h2>5. Third-Party Disclosure</h2>
    <p>We may share your information with third-party service providers:</p>
    <table>
        <tr><th>Service</th><th>Purpose</th></tr>
        <tr><td>Supabase</td><td>Database hosting</td></tr>
        <tr><td>Google/Gmail API</td><td>Email integration</td></tr>
        <tr><td>Google Calendar API</td><td>Calendar sync</td></tr>
        <tr><td>Meta/Facebook WhatsApp API</td><td>WhatsApp Business messaging</td></tr>
    </table>
    <p>These providers are contractually obligated to protect your information.</p>

    <h2>6. Children's Privacy</h2>
    <p>Our service is not intended for children under 13. We do not knowingly collect personal information from children under 13.</p>

    <h2>7. User Rights</h2>
    <p>You have the right to:</p>
    <ul>
        <li>Access your personal data</li>
        <li>Request correction of inaccurate data</li>
        <li>Request deletion of your data</li>
        <li>Withdraw consent at any time</li>
    </ul>
    <p>To exercise these rights, contact us at nelz020513@gmail.com.</p>

    <h2>8. Security</h2>
    <p>We implement security measures including:</p>
    <ul>
        <li>Bcrypt password hashing</li>
        <li>JWT authentication</li>
        <li>HTTPS encryption</li>
    </ul>

    <h2>9. Contact Information</h2>
    <p>For any privacy-related inquiries, contact:</p>
    <p><strong>Email</strong>: nelz020513@gmail.com</p>
</body>
</html>
"""


@router.get("", response_class=HTMLResponse)
def get_privacy_policy():
    return HTMLResponse(content=PRIVACY_HTML, media_type="text/html")