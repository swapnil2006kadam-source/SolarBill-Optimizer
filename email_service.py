import requests
import random
import os

# Replace with your Brevo API Key
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

def send_login_otp(email):

    otp = str(random.randint(100000, 999999))

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    body = {
        "sender": {
            "name": "SolarBill Optimizer",
            "email": "swapnil2006kadam@gmail.com"
        },

        "to": [
            {
                "email": email
            }
        ],

        "subject": "Your Login OTP",

        "htmlContent": f"""
        <h2>SolarBill Optimizer</h2>

        <p>Your login OTP is:</p>

        <h1>{otp}</h1>

        <p>This OTP is valid for 5 minutes.</p>
        """
    }

    response = requests.post(
        url,
        json=body,
        headers=headers
    )

    print("BREVO STATUS:", response.status_code)
    print("BREVO RESPONSE:", response.text)

    return otp, response.status_code