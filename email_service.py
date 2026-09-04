import requests
import random
import os


# =========================================================
# BREVO CONFIGURATION
# =========================================================

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

BREVO_URL = "https://api.brevo.com/v3/smtp/email"

SENDER_NAME = "SolarBill Optimizer"
SENDER_EMAIL = "swapnil2006kadam@gmail.com"


# =========================================================
# SEND LOGIN OTP
# =========================================================

def send_login_otp(email):

    otp = str(
        random.randint(100000, 999999)
    )

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    body = {

        "sender": {
            "name": SENDER_NAME,
            "email": SENDER_EMAIL
        },

        "to": [
            {
                "email": email
            }
        ],

        "subject": "Your SolarBill Optimizer Login OTP",

        "htmlContent": f"""
        <!DOCTYPE html>
        <html>

        <body style="
            font-family: Arial, sans-serif;
            background: #f5f7fb;
            padding: 30px;
        ">

            <div style="
                max-width: 600px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
            ">

                <h2 style="color: #1e3a8a;">
                    SolarBill Optimizer
                </h2>

                <p>
                    Your login verification code is:
                </p>

                <h1 style="
                    letter-spacing: 6px;
                    color: #2563eb;
                ">
                    {otp}
                </h1>

                <p>
                    This OTP is valid for 5 minutes.
                </p>

                <p style="
                    color: #777;
                    font-size: 13px;
                ">
                    If you did not request this code,
                    you can safely ignore this email.
                </p>

            </div>

        </body>

        </html>
        """
    }

    response = requests.post(
        BREVO_URL,
        json=body,
        headers=headers
    )

    return otp, response.status_code


# =========================================================
# SEND PASSWORD RESET EMAIL
# =========================================================

def send_password_reset_email(email, reset_link):

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    body = {

        "sender": {
            "name": SENDER_NAME,
            "email": SENDER_EMAIL
        },

        "to": [
            {
                "email": email
            }
        ],

        "subject": "Reset Your SolarBill Optimizer Password",

        "htmlContent": f"""
        <!DOCTYPE html>
        <html>

        <body style="
            font-family: Arial, sans-serif;
            background: #f5f7fb;
            padding: 30px;
        ">

            <div style="
                max-width: 600px;
                margin: auto;
                background: white;
                padding: 35px;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            ">

                <h2 style="
                    color: #1e3a8a;
                    margin-bottom: 20px;
                ">
                    SolarBill Optimizer
                </h2>

                <h3>
                    Reset Your Password
                </h3>

                <p style="
                    color: #4b5563;
                    line-height: 1.6;
                ">
                    We received a request to reset your
                    SolarBill Optimizer account password.
                </p>

                <p style="
                    color: #4b5563;
                    line-height: 1.6;
                ">
                    Click the button below to create a
                    new password.
                </p>

                <div style="
                    text-align: center;
                    margin: 30px 0;
                ">

                    <a
                        href="{reset_link}"
                        style="
                            display: inline-block;
                            background: #2563eb;
                            color: white;
                            text-decoration: none;
                            padding: 14px 28px;
                            border-radius: 8px;
                            font-weight: bold;
                        "
                    >
                        Reset Password
                    </a>

                </div>

                <p style="
                    color: #6b7280;
                    font-size: 13px;
                    line-height: 1.5;
                ">
                    This password reset link will expire
                    in 30 minutes.
                </p>

                <p style="
                    color: #6b7280;
                    font-size: 13px;
                    line-height: 1.5;
                ">
                    If you did not request a password reset,
                    you can safely ignore this email.
                </p>

                <hr style="
                    border: 0;
                    border-top: 1px solid #e5e7eb;
                    margin: 25px 0;
                ">

                <p style="
                    color: #9ca3af;
                    font-size: 12px;
                ">
                    SolarBill Optimizer
                </p>

            </div>

        </body>

        </html>
        """
    }

    try:

        response = requests.post(
            BREVO_URL,
            json=body,
            headers=headers,
            timeout=15
        )

        return response.status_code

    except requests.RequestException as error:

        print(
            "Password reset email error:",
            error
        )

        return None