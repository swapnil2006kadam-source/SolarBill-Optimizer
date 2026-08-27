def calculate_solar(units, bill_amount):
    units = int(units)
    bill_amount = float(bill_amount)

    # Recommended solar capacity
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

    # Installation cost
    installation_cost = solar_kw * 60000

    # Government subsidy
    subsidy_table = {
        1: 30000,
        2: 60000,
        3: 78000,
        5: 78000,
        7: 78000
    }

    subsidy = subsidy_table.get(solar_kw, 78000)

    # Cost after subsidy
    final_cost = installation_cost - subsidy

    # Estimated savings
    monthly_savings = bill_amount * 0.90
    yearly_savings = monthly_savings * 12

    # Return on investment
    roi = final_cost / yearly_savings

    # Estimated CO2 reduction
    co2 = round(units * 0.011, 2)

    return {
        "solar_kw": solar_kw,
        "monthly_savings": round(monthly_savings, 2),
        "yearly_savings": round(yearly_savings, 2),
        "subsidy": subsidy,
        "installation_cost": installation_cost,
        "final_cost": final_cost,
        "roi": round(roi, 1),
        "co2": co2
    }