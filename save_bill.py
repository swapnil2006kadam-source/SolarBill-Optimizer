from database import get_connection


def save_bill(user_id, user_name, bill, solar):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO bill_history (
            user_id,
            user_name,
            ca_number,
            bill_month,
            units,
            bill_amount,
            solar_kw,
            monthly_savings,
            yearly_savings,
            subsidy,
            installation_cost,
            final_cost,
            roi
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        user_id,
        user_name,
        bill["ca_number"],
        bill["bill_month"],
        bill["units"],
        bill["bill_amount"],
        solar["solar_kw"],
        solar["monthly_savings"],
        solar["yearly_savings"],
        solar["subsidy"],
        solar["installation_cost"],
        solar["final_cost"],
        solar["roi"]
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()