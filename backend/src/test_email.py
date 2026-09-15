# backend/src/test_email.py
# created by ai to test my email function o notifications

import os
from dotenv import load_dotenv
from .utils.notifications import send_email, send_notification

load_dotenv(override=True)

def test_manual_email():
    print("Testing raw SMTP email configuration...")
    
    # Grab your email from environment variables or type it directly here for testing
    recipient = os.getenv("SMTP_USER") # This sends it to the same Gmail you use to send!
    
    if not recipient:
        print("Error: SMTP_USER not found in your .env file.")
        return

    print(f"Attempting to send test email to: {recipient}")

    # Test 1: Direct SMTP function test
    success = send_email(
        to_email=recipient,
        subject="🧪 Test Crypto Alert: BTC-USD",
        html_content="<h3 style='color: green;'>Success! Your SMTP email configuration is working perfectly.</h3>"
    )

    if success:
        print("✅ Raw email test passed! Check your inbox.")
    else:
        print("❌ Raw email test failed. Check your terminal logs for errors.")

    print("\nTesting full notification router function...")
    
    # Test 2: Full router test (simulating a real price alert)
    router_success = send_notification(
        method="email",
        contact=recipient,
        symbol="BTC-USD",
        current_price=68450.50,
        condition="above",
        target_price=65000.00,
        unsub_token="test_token_12345"
    )

    if router_success:
        print("✅ Router email test passed!")
    else:
        print("❌ Router email test failed.")

if __name__ == "__main__":
    test_manual_email()