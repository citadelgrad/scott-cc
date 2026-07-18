def process_payment(payment):
    token = payment["token"].strip()
    return charge(token)


def charge(token):
    return {"status": "charged", "token": token}


def apply_discount(order):
    return order["discount_code"].upper()
