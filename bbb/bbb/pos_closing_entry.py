def validate(doc, method):
    payment_reconciliation = doc.payment_reconciliation
    for payment in payment_reconciliation:
        one_thousand_taka_note = payment.one_thousand_taka_note if payment.one_thousand_taka_note else 0
        five_hundred_taka_note = payment.five_hundred_taka_note if payment.five_hundred_taka_note else 0
        two_hundred_taka_note = payment.two_hundred_taka_note if payment.two_hundred_taka_note else 0
        one_hundred_taka_note = payment.one_hundred_taka_note if payment.one_hundred_taka_note else 0
        fifty_taka_note = payment.fifty_taka_note if payment.fifty_taka_note else 0
        twenty_taka_note = payment.twenty_taka_note if payment.twenty_taka_note else 0
        ten_taka_note = payment.ten_taka_note if payment.ten_taka_note else 0
        five_taka_note = payment.five_taka_note if payment.five_taka_note else 0
        five_taka_coin = payment.five_taka_coin if payment.five_taka_coin else 0
        two_taka_note = payment.two_taka_note if payment.two_taka_note else 0
        two_taka_coin = payment.two_taka_coin if payment.two_taka_coin else 0
        one_taka_note = payment.one_taka_note if payment.one_taka_note else 0
        one_taka_coin = payment.one_taka_coin if payment.one_taka_coin else 0

        total_amount = (
                1000 * one_thousand_taka_note + 500 * five_hundred_taka_note + 200 * two_hundred_taka_note +
                100 * one_hundred_taka_note + 50 * fifty_taka_note + 20 * twenty_taka_note + 10 * ten_taka_note +
                5 * five_taka_note + 5 * five_taka_coin + 2 * two_taka_note + 2 * two_taka_coin + one_taka_note + one_taka_coin)

        payment.total_amount = total_amount
