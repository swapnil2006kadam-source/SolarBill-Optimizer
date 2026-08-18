def calculate_solar(units, bill_amount):

    units = int(units)
    bill_amount = float(bill_amount)

    # Recommended Solar Capacity
    if units <= 100:
        solar_kw = 1
    elif units <= 200:
        solar_kw = 2
    elif units <= 300:
        solar_kw = 3
    elif units <= 500:
        solar_kw = 5
    else:
        solar_kw = 7

    # Approximate installation cost
    installation_cost = solar_kw * 60000

    # Government Subsidy
    subsidy_table = {
        1: 30000,
        2: 60000,
        3: 78000,
        5: 78000,
        7: 78000
    }

    subsidy = subsidy_table.get(solar_kw, 78000)

    # User pays after subsidy
    final_cost = installation_cost - subsidy

    # Monthly Savings (Approx. 90%)
    monthly_savings = bill_amount * 0.90

    # Yearly Savings
    yearly_savings = monthly_savings * 12

    # ROI
    roi = final_cost / yearly_savings

    # CO₂ Saved
    co2 = round(units * 0.011, 2)

    return {

        "solar_kw": solar_kw,

        "monthly_savings": round(monthly_savings,2),

        "yearly_savings": round(yearly_savings,2),

        "subsidy": subsidy,

        "installation_cost": installation_cost,

        "final_cost": final_cost,

        "roi": round(roi,1),

        "co2": co2
    }