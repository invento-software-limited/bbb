def validate(doc, method):
    payment_reconciliation = doc.payment_reconciliation
    for payment in payment_reconciliation:
        total_amount = (
                1000 * payment.one_thousand_taka_note + 500 * payment.five_hundred_taka_note + 200 * payment.two_hundred_taka_note +
                100 * payment.one_hundred_taka_note + 50 * payment.fifty_taka_note + 20 * payment.twenty_taka_note + 10 * payment.ten_taka_note +
                5 * payment.five_taka_note + 5 * payment.five_taka_coin + 2 * payment.two_taka_note + 2 * payment.two_taka_coin + payment.one_taka_note + payment.one_taka_coin)

        payment.total_amount = total_amount
