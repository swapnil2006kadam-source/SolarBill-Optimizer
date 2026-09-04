from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    session,
    flash,
    send_file,
    url_for
    
)
import secrets

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from database import get_connection
from config import SECRET_KEY

from Bill_reader import read_bill, extract_bill_data
from save_bill import save_bill
from generate_pdf import create_pdf
from email_service import send_login_otp, send_password_reset_email

from services.subsidy_service import (
    calculate_central_subsidy
)

from services.installation_service import (
    calculate_installation_cost
)

from services.location_service import (
    get_location_info
)

from services.solar_generation_service import (
    estimate_solar_generation
)

from datetime import datetime, timedelta

from dotenv import load_dotenv
from google import genai

import os
import requests


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

app = Flask(__name__)

app.secret_key = SECRET_KEY


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

WEATHER_API_KEY = os.getenv(
    "WEATHER_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)


# =========================================================
# GEMINI CLIENT
# =========================================================

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# WEATHER
# =========================================================

def get_weather(city):

    if not city:
        return None

    if not WEATHER_API_KEY:
        print("⚠️ WEATHER_API_KEY not configured.")
        return None

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
    )

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data.get("cod") != 200:
            return None

        return {
            "temp": round(
                data["main"]["temp"],
                1
            ),
            "condition": data["weather"][0]["main"],
            "icon": data["weather"][0]["icon"],
            "city": city
        }

    except Exception as e:

        print(
            "❌ WEATHER ERROR:",
            repr(e)
        )

        return None


# =========================================================
# SOLAR POWER INDICATOR
# =========================================================

def solar_power(condition):

    if condition == "Clear":
        return 100

    if condition == "Clouds":
        return 50

    if condition == "Rain":
        return 20

    if condition == "Drizzle":
        return 30

    if condition == "Thunderstorm":
        return 10

    return 60


# =========================================================
# SOLAR GUIDANCE
# =========================================================

def solar_guidance(system_size):

    if system_size <= 2:

        return {
            "companies": [

                {
                    "name": "Loom Solar",
                    "link": "https://www.loomsolar.com",
                    "rating": 4.5
                },

                {
                    "name": "Tata Power Solar",
                    "link": "https://www.tatapowersolar.com",
                    "rating": 4.7
                },

                {
                    "name": "Waaree Energies",
                    "link": "https://www.waaree.com",
                    "rating": 4.6
                },

                {
                    "name": "Adani Solar",
                    "link": (
                        "https://www.adani.com/businesses/"
                        "energy-utilities/solar-manufacturing"
                    ),
                    "rating": 4.4
                },

                {
                    "name": "Vikram Solar",
                    "link": "https://www.vikramsolar.com",
                    "rating": 4.5
                }

            ],

            "place": (
                "Buy from official company websites "
                "or authorized solar installers."
            ),

            "scheme": {
                "name": "PM Surya Ghar Muft Bijli Yojana",
                "link": "https://pmsuryaghar.gov.in"
            }
        }


    if system_size <= 5:

        return {
            "companies": [

                {
                    "name": "Adani Solar",
                    "link": "https://www.adanisolar.com",
                    "rating": 4.4
                },

                {
                    "name": "Waaree Solar",
                    "link": "https://www.waaree.com",
                    "rating": 4.6
                }

            ],

            "place": (
                "Best for medium homes and villas."
            ),

            "scheme": {
                "name": "State Solar Subsidy",
                "link": "https://mnre.gov.in"
            }
        }


    return {
        "companies": [

            {
                "name": "Tata Power Solar",
                "link": "https://www.tatapowersolar.com",
                "rating": 4.7
            },

            {
                "name": "Adani Solar",
                "link": "https://www.adanisolar.com",
                "rating": 4.5
            }

        ],

        "place": (
            "Best for large homes / commercial use."
        ),

        "scheme": {
            "name": "Commercial Solar Scheme",
            "link": "https://mnre.gov.in"
        }
    }


# =========================================================
# MAIN SOLAR CALCULATION
# =========================================================

def calculate_solar_recommendation(
    bill,
    units,
    city
):

    # -----------------------------------------------------
    # Validate input
    # -----------------------------------------------------

    if bill <= 0:
        raise ValueError(
            "Bill amount must be greater than zero."
        )

    if units <= 0:
        raise ValueError(
            "Electricity units must be greater than zero."
        )


    # -----------------------------------------------------
    # Validate city
    # -----------------------------------------------------

    location_info = get_location_info(
        city
    )

    if not location_info:

        raise ValueError(
            f"Verified solar data is not available "
            f"for {city.title()}."
        )


    state = location_info["state"]

    discom = location_info["discom"]


    # -----------------------------------------------------
    # EFFECTIVE ELECTRICITY RATE
    # -----------------------------------------------------

    effective_electricity_rate = (
        bill / units
    )


    # -----------------------------------------------------
    # SOLAR SYSTEM SIZE
    # -----------------------------------------------------

    solar_kw = round(
        units / 120,
        1
    )

    if solar_kw <= 0:
        solar_kw = 0.1


    # -----------------------------------------------------
    # LOCATION-BASED SOLAR GENERATION
    # -----------------------------------------------------

    generation = estimate_solar_generation(
        solar_kw=solar_kw,
        city=city
    )


    daily_generation = generation[
        "daily_generation_kwh"
    ]

    monthly_generation = generation[
        "monthly_generation_kwh"
    ]

    yearly_generation = generation[
        "yearly_generation_kwh"
    ]


    # -----------------------------------------------------
    # SOLAR SAVINGS
    # -----------------------------------------------------

    monthly_savings = round(
        monthly_generation
        * effective_electricity_rate,
        2
    )

    yearly_savings = round(
        yearly_generation
        * effective_electricity_rate,
        2
    )


    # -----------------------------------------------------
    # 25-YEAR ESTIMATED IMPACT
    # -----------------------------------------------------

    LIFETIME_YEARS = 25

    lifetime_generation = round(
        yearly_generation
        * LIFETIME_YEARS,
        2
    )

    lifetime_savings = round(
        yearly_savings
        * LIFETIME_YEARS,
        2
    )


    # -----------------------------------------------------
    # BEFORE VS AFTER SOLAR
    # -----------------------------------------------------

    bill_before_solar = round(
        bill,
        2
    )

    estimated_bill_after_solar = round(
        max(
            bill - monthly_savings,
            0
        ),
        2
    )


    # -----------------------------------------------------
    # BILL REDUCTION PERCENT
    # -----------------------------------------------------

    if bill > 0:

        bill_reduction_percent = round(
            (
                (
                    bill
                    - estimated_bill_after_solar
                )
                / bill
            )
            * 100,
            1
        )

    else:

        bill_reduction_percent = 0


    # -----------------------------------------------------
    # CENTRAL SUBSIDY
    # -----------------------------------------------------

    subsidy = calculate_central_subsidy(
        solar_kw
    )


    # -----------------------------------------------------
    # INSTALLATION COST
    # -----------------------------------------------------

    installation_cost = calculate_installation_cost(
        solar_kw,
        state=state
    )


    # -----------------------------------------------------
    # FINAL COST
    # -----------------------------------------------------

    final_cost = round(
        installation_cost - subsidy,
        2
    )


    # -----------------------------------------------------
    # ROI / PAYBACK
    # -----------------------------------------------------

    if yearly_savings > 0:

        roi = round(
            final_cost / yearly_savings,
            1
        )

    else:

        roi = 0


    # -----------------------------------------------------
    # GUIDANCE
    # -----------------------------------------------------

    guidance = solar_guidance(
        solar_kw
    )


    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    solar = {

        # -------------------------------------------------
        # Solar system
        # -------------------------------------------------

        "solar_kw": solar_kw,


        # -------------------------------------------------
        # Solar generation
        # -------------------------------------------------

        "daily_generation": daily_generation,

        "monthly_generation": monthly_generation,

        "yearly_generation": yearly_generation,


        # -------------------------------------------------
        # Savings
        # -------------------------------------------------

        "monthly_savings": monthly_savings,

        "yearly_savings": yearly_savings,

        "electricity_rate": round(
            effective_electricity_rate,
            2
        ),


        # -------------------------------------------------
        # 25-year impact
        # -------------------------------------------------

        "lifetime_years": LIFETIME_YEARS,

        "lifetime_generation": lifetime_generation,

        "lifetime_savings": lifetime_savings,


        # -------------------------------------------------
        # BEFORE vs AFTER SOLAR
        # -------------------------------------------------

        "bill_before_solar": bill_before_solar,

        "estimated_bill_after_solar":
            estimated_bill_after_solar,

        "bill_reduction_percent":
            bill_reduction_percent,


        # -------------------------------------------------
        # Subsidy
        # -------------------------------------------------

        "subsidy": subsidy,


        # -------------------------------------------------
        # Installation
        # -------------------------------------------------

        "installation_cost": installation_cost,

        "final_cost": final_cost,


        # -------------------------------------------------
        # ROI
        # -------------------------------------------------

        "roi": roi,


        # -------------------------------------------------
        # Guidance
        # -------------------------------------------------

        "guidance": guidance,


        # -------------------------------------------------
        # Location
        # -------------------------------------------------

        "city": location_info.get(
            "city",
            city
        ),

        "state": state,

        "discom": discom,


        # -------------------------------------------------
        # Solar generation information
        # -------------------------------------------------

        "latitude": generation.get(
            "latitude"
        ),

        "longitude": generation.get(
            "longitude"
        ),

        "average_daily_radiation":
            generation.get(
                "average_daily_radiation_kwh"
            ),

        "performance_ratio":
            generation.get(
                "performance_ratio"
            ),

        "solar_generation_source":
            generation.get(
                "source"
            ),

        "solar_generation_days":
            generation.get(
                "days_used"
            )
    }


    return solar


# =========================================================
# SOLAR AI
# =========================================================

@app.route(
    "/solar-ai",
    methods=["POST"]
)
def solar_ai():

    try:

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )

        question = (
            data.get(
                "question",
                ""
            )
            .strip()
        )


        print(
            "🔥 QUESTION RECEIVED:",
            question
        )


        if not question:

            return jsonify({
                "success": False,
                "answer": (
                    "Please ask me a "
                    "solar-related question."
                )
            })


        prompt = f"""
You are Solar AI Assistant inside a website called SolarBill Optimizer.

Your job is ONLY to answer questions related to solar energy and solar electricity systems.

You can answer questions about:

• Solar panels
• Solar energy
• Solar systems
• Solar installation
• Solar panel types
• Solar panel efficiency
• Solar generation
• Solar capacity
• Solar inverter
• Solar batteries
• Solar maintenance
• Solar cost
• Solar installation cost
• Solar subsidy
• Indian solar government schemes
• PM Surya Ghar Muft Bijli Yojana
• Electricity bills
• Electricity units
• Solar savings
• Solar ROI
• Net metering
• On-grid solar
• Off-grid solar
• Hybrid solar
• Rooftop solar
• Solar installation requirements
• Solar lifespan
• Solar cleaning
• Solar performance
• Solar generation based on weather
• Solar generation based on location
• Solar-related environmental benefits

IMPORTANT:

If the question is not related to solar energy, solar electricity,
solar panels, solar systems, or electricity usage related to solar,
do not answer the unrelated question.

Instead say:

I can only answer questions related to solar energy and solar systems.
Please ask me a solar-related question.

RESPONSE FORMAT:

• Use plain text.
• Do not use Markdown.
• Do not use **.
• Do not use # headings.
• Do not use Markdown tables.
• Do not use Markdown links.
• Use • for lists.
• Keep answers simple and clear.
• Use ₹ for Indian prices.
• Use kW for system size.
• Use kWh or units for electricity generation.
• Avoid unnecessary symbols.
• Keep the answer suitable for normal homeowners.

If current government subsidy information is requested,
explain that rules can change and recommend checking
the official government portal.

USER QUESTION:
{question}
"""


        response = (
            gemini_client
            .models
            .generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
        )


        answer = (
            response.text
            or
            "Sorry, I could not generate an answer."
        )


        answer = answer.strip()


        print(
            " GEMINI RESPONSE RECEIVED"
        )


        return jsonify({
            "success": True,
            "answer": answer
        })


    except Exception as e:

        print(
            "❌ SOLAR AI ERROR:",
            repr(e)
        )


        return jsonify({

            "success": False,

            "answer": (
                "Sorry, Solar AI is temporarily "
                "unavailable."
            )

        }), 500


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "home.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        if not name or not email or not password:

            flash(
                "Please fill all fields."
            )

            return redirect(
                "/register"
            )


        conn = get_connection()

        cursor = conn.cursor(
            dictionary=True
        )


        try:

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email=%s
                """,
                (email,)
            )

            if cursor.fetchone():

                flash(
                    "Email already registered!"
                )

                return redirect(
                    "/register"
                )


            hashed_password = (
                generate_password_hash(
                    password
                )
            )


            cursor.execute(
                """
                INSERT INTO users(
                    full_name,
                    email,
                    password
                )
                VALUES(%s, %s, %s)
                """,
                (
                    name,
                    email,
                    hashed_password
                )
            )


            conn.commit()


            flash(
                "Registration Successful!"
            )


            return redirect(
                "/login"
            )


        finally:

            cursor.close()
            conn.close()


    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN + OTP
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        step = request.form.get(
            "step"
        )


        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        if step == "login":

            email = request.form.get(
                "email",
                ""
            ).strip()

            password = request.form.get(
                "password",
                ""
            )


            conn = get_connection()

            cursor = conn.cursor(
                dictionary=True
            )


            try:

                cursor.execute(
                    """
                    SELECT *
                    FROM users
                    WHERE email=%s
                    """,
                    (email,)
                )

                user = cursor.fetchone()


                if (
                    user
                    and check_password_hash(
                        user["password"],
                        password
                    )
                ):

                    otp, status = send_login_otp(
                        user["email"]
                    )


                    expiry = (
                        datetime.now()
                        + timedelta(minutes=5)
                    )


                    cursor.execute(
                        """
                        UPDATE users
                        SET otp=%s,
                            otp_expiry=%s
                        WHERE id=%s
                        """,
                        (
                            otp,
                            expiry,
                            user["id"]
                        )
                    )


                    conn.commit()


                    session[
                        "pending_user"
                    ] = user["id"]


                    return render_template(
                        "login.html",
                        show_otp=True,
                        email=email
                    )


                flash(
                    "Invalid Email or Password"
                )


            finally:

                cursor.close()
                conn.close()


        # -------------------------------------------------
        # OTP
        # -------------------------------------------------

        elif step == "otp":

            entered_otp = request.form.get(
                "otp",
                ""
            )


            conn = get_connection()

            cursor = conn.cursor(
                dictionary=True
            )


            try:

                cursor.execute(
                    """
                    SELECT *
                    FROM users
                    WHERE id=%s
                    """,
                    (
                        session.get(
                            "pending_user"
                        ),
                    )
                )


                user = cursor.fetchone()


                if (
                    user
                    and user["otp"]
                    == entered_otp
                ):

                    if (
                        user["otp_expiry"]
                        and
                        datetime.now()
                        >
                        user["otp_expiry"]
                    ):

                        flash(
                            "OTP expired"
                        )

                        return redirect(
                            "/login"
                        )


                    cursor.execute(
                        """
                        UPDATE users
                        SET otp=NULL,
                            otp_expiry=NULL
                        WHERE id=%s
                        """,
                        (user["id"],)
                    )


                    conn.commit()


                    session["user"] = (
                        user["full_name"]
                    )

                    session["user_id"] = (
                        user["id"]
                    )


                    session.pop(
                        "pending_user",
                        None
                    )


                    return redirect(
                        "/dashboard"
                    )


                flash(
                    "Invalid OTP"
                )


            finally:

                cursor.close()
                conn.close()


    return render_template(
        "login.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    # -----------------------------------------------------
    # Check Login
    # -----------------------------------------------------

    if "user" not in session:

        return redirect("/login")


    # -----------------------------------------------------
    # Weather
    # -----------------------------------------------------

    city = session.get(
        "city",
        "Mumbai"
    )

    weather = get_weather(
        city
    )


    if weather:

        power = solar_power(
            weather["condition"]
        )

    else:

        power = 0


    # -----------------------------------------------------
    # Database
    # -----------------------------------------------------

    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )


    try:

        # -------------------------------------------------
        # Get Bill History
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM bill_history
            WHERE user_id=%s
            ORDER BY upload_date DESC
            """,
            (
                session["user_id"],
            )
        )

        history = cursor.fetchall()


        # -------------------------------------------------
        # Latest Bill
        # -------------------------------------------------

        latest_bill = (
            history[0]
            if history
            else None
        )


        # -------------------------------------------------
        # Dashboard Statistics
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_reports,
                SUM(bill_amount) AS total_bill,
                AVG(bill_amount) AS average_bill,
                MAX(bill_amount) AS highest_bill,
                MIN(bill_amount) AS lowest_bill,
                SUM(monthly_savings) AS total_savings
            FROM bill_history
            WHERE user_id=%s
            """,
            (
                session["user_id"],
            )
        )

        stats = cursor.fetchone()


    finally:

        cursor.close()
        conn.close()


    # -----------------------------------------------------
    # Current Solar Calculation
    # -----------------------------------------------------

    if session.get("calc_data"):

        solar = dict(
            session["calc_data"]
        )

    elif latest_bill:

        solar = dict(
            latest_bill
        )

    else:

        solar = None


    # -----------------------------------------------------
    # Ensure Solar Generation Values Exist
    # -----------------------------------------------------

    if solar:

        # -------------------------------------------------
        # Daily Generation
        # -------------------------------------------------

        daily_generation = solar.get(
            "daily_generation",
            0
        )

        try:

            daily_generation = float(
                daily_generation or 0
            )

        except (TypeError, ValueError):

            daily_generation = 0


        solar["daily_generation"] = (
            daily_generation
        )


        # -------------------------------------------------
        # Monthly Generation
        # -------------------------------------------------

        monthly_generation = solar.get(
            "monthly_generation"
        )

        try:

            if monthly_generation is None:

                monthly_generation = (
                    daily_generation * 30
                )

            else:

                monthly_generation = float(
                    monthly_generation
                )

        except (TypeError, ValueError):

            monthly_generation = (
                daily_generation * 30
            )


        solar["monthly_generation"] = (
            monthly_generation
        )


        # -------------------------------------------------
        # Yearly Generation
        # -------------------------------------------------

        yearly_generation = solar.get(
            "yearly_generation"
        )

        try:

            if yearly_generation is None:

                yearly_generation = (
                    daily_generation * 365
                )

            else:

                yearly_generation = float(
                    yearly_generation
                )

        except (TypeError, ValueError):

            yearly_generation = (
                daily_generation * 365
            )


        solar["yearly_generation"] = (
            yearly_generation
        )


        # -------------------------------------------------
        # System Size
        # -------------------------------------------------

        system_size = solar.get(
            "solar_kw",
            0
        )

        try:

            system_size = float(
                system_size or 0
            )

        except (TypeError, ValueError):

            system_size = 0


        solar["solar_kw"] = (
            system_size
        )


        # -------------------------------------------------
        # Guidance
        # -------------------------------------------------

        if system_size:

            solar["guidance"] = (
                solar_guidance(
                    system_size
                )
            )


        # -------------------------------------------------
        # City
        # -------------------------------------------------

        solar["city"] = (
            solar.get("city")
            or
            session.get(
                "city",
                "Mumbai"
            )
        )


    # -----------------------------------------------------
    # Render Dashboard
    # -----------------------------------------------------

    return render_template(

        "dashboard.html",

        username=session.get(
            "user",
            "User"
        ),

        history=history,

        stats=stats,

        bill=latest_bill,

        solar=solar,

        calc=session.get(
            "calc_data"
        ),

        weather=weather,

        power=power

    )
# =========================================================
# MANUAL CALCULATOR
# =========================================================

@app.route(
    "/calculate",
    methods=["POST"]
)
def calculate():

    if "user" not in session:

        return redirect(
            "/login"
        )


    try:

        # -------------------------------------------------
        # Get calculator values
        # -------------------------------------------------

        bill = float(
            request.form.get(
                "bill",
                0
            )
        )

        units = float(
            request.form.get(
                "units",
                0
            )
        )

        city = (
            request.form.get(
                "city",
                ""
            )
            .strip()
        )


        # -------------------------------------------------
        # Validate input
        # -------------------------------------------------

        if bill <= 0:

            raise ValueError(
                "Please enter a valid bill amount."
            )


        if units <= 0:

            raise ValueError(
                "Please enter valid electricity units."
            )


        if not city:

            raise ValueError(
                "Please enter your city."
            )


        # -------------------------------------------------
        # Calculate solar recommendation
        # -------------------------------------------------

        solar = calculate_solar_recommendation(
            bill=bill,
            units=units,
            city=city
        )


        # -------------------------------------------------
        # Store latest calculation
        # -------------------------------------------------

        session["calc_data"] = solar

        session["city"] = city

        session.modified = True


        # -------------------------------------------------
        # Save manual calculation to history
        # -------------------------------------------------

        bill_data = {

            "bill_amount": bill,

            "units": units,

            "ca_number": "MANUAL-CALC",

            "bill_month": datetime.now().strftime(
                "%b-%y"
            )
        }


        save_bill(
            session["user_id"],
            session["user"],
            bill_data,
            solar
        )


        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        flash(
            "Solar calculation completed successfully!"
        )


        return redirect(
            "/dashboard"
        )


    except Exception as e:

        print(
            "❌ CALCULATION ERROR:",
            repr(e)
        )


        flash(
            str(e)
        )


        return redirect(
            "/dashboard"
        )


# =========================================================
# BILL UPLOAD
# =========================================================

@app.route(
    "/upload_bill",
    methods=["POST"]
)
def upload_bill():

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user" not in session:

        return redirect(
            "/login"
        )


    # -----------------------------------------------------
    # Get uploaded file
    # -----------------------------------------------------

    uploaded_file = request.files.get(
        "bill"
    )


    if (
        not uploaded_file
        or uploaded_file.filename == ""
    ):

        flash(
            "Please select a PDF file."
        )

        return redirect(
            "/dashboard"
        )


    # -----------------------------------------------------
    # Upload folder
    # -----------------------------------------------------

    upload_folder = os.path.join(
        "static",
        "uploads"
    )


    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    # -----------------------------------------------------
    # Secure filename
    # -----------------------------------------------------

    filename = secure_filename(
        uploaded_file.filename
    )


    filepath = os.path.join(
        upload_folder,
        filename
    )


    # -----------------------------------------------------
    # Save uploaded PDF
    # -----------------------------------------------------

    uploaded_file.save(
        filepath
    )


    try:

        # -------------------------------------------------
        # Read electricity bill
        # -------------------------------------------------

        text = read_bill(
            filepath
        )


        # -------------------------------------------------
        # Extract bill information
        # -------------------------------------------------

        bill = extract_bill_data(
            text
        )


        # -------------------------------------------------
        # Get city
        # -------------------------------------------------

        city = session.get(
            "city",
            "Mumbai"
        )


        # -------------------------------------------------
        # Calculate solar recommendation
        # -------------------------------------------------

        solar = calculate_solar_recommendation(
            bill=bill["bill_amount"],
            units=bill["units"],
            city=city
        )


        # -------------------------------------------------
        # Store calculation
        # -------------------------------------------------

        session["calc_data"] = solar

        session["city"] = city

        session.modified = True


        # -------------------------------------------------
        # Save uploaded bill
        # -------------------------------------------------

        save_bill(
            session["user_id"],
            session["user"],
            bill,
            solar
        )


        # -------------------------------------------------
        # Success message
        # -------------------------------------------------

        flash(
            "Bill uploaded successfully!"
        )


        return redirect(
            "/dashboard"
        )


    except Exception as e:

        print(
            "❌ BILL UPLOAD ERROR:",
            repr(e)
        )


        flash(
            f"Unable to process bill: {e}"
        )


        return redirect(
            "/dashboard"
        )


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():

    if "user" not in session:

        return redirect(
            "/login"
        )


    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )


    try:

        cursor.execute(
            """
            SELECT *
            FROM bill_history
            WHERE user_id=%s
            ORDER BY upload_date DESC
            """,
            (
                session["user_id"],
            )
        )


        reports = cursor.fetchall()


    finally:

        cursor.close()
        conn.close()


    return render_template(

        "reports.html",

        reports=reports,

        username=session.get(
            "user",
            "User"
        )

    )


# =========================================================
# REPORT DETAILS
# =========================================================

@app.route(
    "/report/<int:id>"
)
def report_details(id):

    if "user" not in session:

        return redirect(
            "/login"
        )


    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )


    try:

        cursor.execute(
            """
            SELECT *
            FROM bill_history
            WHERE id=%s
            AND user_id=%s
            """,
            (
                id,
                session["user_id"]
            )
        )


        report = cursor.fetchone()


    finally:

        cursor.close()
        conn.close()


    if report is None:

        return (
            "Report Not Found",
            404
        )


    return render_template(

        "report_details.html",

        report=report,

        username=session.get(
            "user",
            "User"
        )

    )


# =========================================================
# DELETE REPORT
# =========================================================

@app.route(
    "/delete_report/<int:id>"
)
def delete_report(id):

    if "user" not in session:

        return redirect(
            "/login"
        )


    conn = get_connection()

    cursor = conn.cursor()


    try:

        cursor.execute(
            """
            DELETE FROM bill_history
            WHERE id=%s
            AND user_id=%s
            """,
            (
                id,
                session["user_id"]
            )
        )


        conn.commit()


    finally:

        cursor.close()
        conn.close()


    return redirect(
        "/reports"
    )


# =========================================================
# DOWNLOAD PDF
# =========================================================

@app.route(
    "/download_pdf/<int:id>"
)
def download_pdf(id):

    if "user" not in session:

        return redirect(
            "/login"
        )


    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )


    try:

        cursor.execute(
            """
            SELECT *
            FROM bill_history
            WHERE id=%s
            AND user_id=%s
            """,
            (
                id,
                session["user_id"]
            )
        )


        report = cursor.fetchone()


    finally:

        cursor.close()
        conn.close()


    if report is None:

        return (
            "Report Not Found",
            404
        )


    os.makedirs(
        "static/pdfs",
        exist_ok=True
    )


    filename = (
        f"static/pdfs/report_{id}.pdf"
    )


    create_pdf(
        filename,
        report
    )


    return send_file(
        filename,
        as_attachment=True
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        "/login"
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user" not in session:

        return redirect(
            "/login"
        )


    return render_template(
        "profile.html",
        user=session["user"]
    )


# =========================================================
# ABOUT
# =========================================================

@app.route("/about")
def about():

    if "user" not in session:

        return redirect(
            "/login"
        )


    return render_template(
        "about.html"
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    # -----------------------------------------------------
    # SHOW FORGOT PASSWORD PAGE
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(
            "forgot_password.html"
        )


    # -----------------------------------------------------
    # GET EMAIL FROM FORM
    # -----------------------------------------------------

    email = request.form.get(
        "email",
        ""
    ).strip().lower()


    if not email:

        flash(
            "Please enter your email address.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )


    # -----------------------------------------------------
    # FIND USER
    # -----------------------------------------------------

    conn = get_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT id, email
            FROM users
            WHERE LOWER(email) = %s
            LIMIT 1
            """,
            (email,)
        )

        user = cursor.fetchone()

    except Exception as error:

        print(
            "User lookup error:",
            error
        )

        flash(
            "Something went wrong. Please try again later.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    finally:

        cursor.close()
        conn.close()


    # -----------------------------------------------------
    # USER NOT FOUND
    # -----------------------------------------------------

    if not user:

        flash(
            "If an account exists with this email, "
            "a password reset link has been sent.",
            "success"
        )

        return redirect(
            url_for("forgot_password")
        )


    # -----------------------------------------------------
    # GENERATE SECURE RESET TOKEN
    # -----------------------------------------------------

    token = secrets.token_urlsafe(32)


    # -----------------------------------------------------
    # TOKEN EXPIRATION
    # -----------------------------------------------------

    expires_at = (
        datetime.utcnow()
        + timedelta(minutes=30)
    )


    # -----------------------------------------------------
    # SAVE TOKEN IN DATABASE
    # -----------------------------------------------------

    conn = get_connection()

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE users
            SET reset_token = %s,
                reset_token_expires = %s
            WHERE id = %s
            """,
            (
                token,
                expires_at,
                user["id"]
            )
        )

        conn.commit()

    except Exception as error:

        conn.rollback()

        print(
            "Password reset database error:",
            error
        )

        flash(
            "Something went wrong. Please try again later.",
            "error"
        )

        return redirect(
            url_for("forgot_password")
        )

    finally:

        cursor.close()
        conn.close()


    # -----------------------------------------------------
    # CREATE RESET LINK
    # -----------------------------------------------------

    reset_link = url_for(
        "reset_password",
        token=token,
        _external=True
    )


    # -----------------------------------------------------
    # SEND RESET EMAIL THROUGH BREVO
    # -----------------------------------------------------

    try:

        email_status = send_password_reset_email(
            email,
            reset_link
        )

    except Exception as error:

        print(
            "Password reset email error:",
            error
        )

        email_status = None


    # -----------------------------------------------------
    # CHECK EMAIL RESULT
    # -----------------------------------------------------

    if email_status in (200, 201):

        flash(
            "If an account exists with this email, "
            "a password reset link has been sent.",
            "success"
        )

    else:

        print(
            "Brevo password reset email failed."
        )

        print(
            "Brevo status:",
            email_status
        )

        flash(
            "Unable to send the password reset email. "
            "Please try again later.",
            "error"
        )


    # -----------------------------------------------------
    # RETURN TO FORGOT PASSWORD PAGE
    # -----------------------------------------------------

    return redirect(
        url_for("forgot_password")
    )

# =========================================================
# RESET PASSWORD
# =========================================================

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    # -----------------------------------------------------
    # FIND USER USING RESET TOKEN
    # -----------------------------------------------------

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, email
            FROM users
            WHERE reset_token = %s
              AND reset_token_expires > %s
            LIMIT 1
            """,
            (token, datetime.utcnow())
        )

        user = cursor.fetchone()

    except Exception as error:

        print("Reset token lookup error:", error)

        flash(
            "Something went wrong. Please try again.",
            "error"
        )

        return redirect(url_for("login"))

    finally:

        cursor.close()
        conn.close()


    # -----------------------------------------------------
    # INVALID OR EXPIRED TOKEN
    # -----------------------------------------------------

    if not user:

        flash(
            "This password reset link is invalid or has expired.",
            "error"
        )

        return redirect(url_for("forgot_password"))


    # -----------------------------------------------------
    # SHOW RESET PASSWORD PAGE
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(
            "reset_password.html",
            token=token
        )


    # -----------------------------------------------------
    # GET NEW PASSWORD
    # -----------------------------------------------------

    password = request.form.get(
        "password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    # -----------------------------------------------------
    # VALIDATE PASSWORD
    # -----------------------------------------------------

    if not password:

        flash(
            "Please enter a new password.",
            "error"
        )

        return render_template(
            "reset_password.html",
            token=token
        )


    if len(password) < 8:

        flash(
            "Password must be at least 8 characters long.",
            "error"
        )

        return render_template(
            "reset_password.html",
            token=token
        )


    if password != confirm_password:

        flash(
            "Passwords do not match.",
            "error"
        )

        return render_template(
            "reset_password.html",
            token=token
        )


    # -----------------------------------------------------
    # HASH NEW PASSWORD
    # -----------------------------------------------------

    hashed_password = generate_password_hash(
        password
    )


    # -----------------------------------------------------
    # UPDATE PASSWORD
    # AND CLEAR RESET TOKEN
    # -----------------------------------------------------

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE users
            SET password = %s,
                reset_token = NULL,
                reset_token_expires = NULL
            WHERE id = %s
            """,
            (
                hashed_password,
                user["id"]
            )
        )

        conn.commit()

    except Exception as error:

        conn.rollback()

        print(
            "Password reset update error:",
            error
        )

        flash(
            "Unable to reset your password. Please try again.",
            "error"
        )

        return render_template(
            "reset_password.html",
            token=token
        )

    finally:

        cursor.close()
        conn.close()


    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    flash(
        "Password reset successfully. You can now log in.",
        "success"
    )

    return redirect(
        url_for("login")
    )

# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )