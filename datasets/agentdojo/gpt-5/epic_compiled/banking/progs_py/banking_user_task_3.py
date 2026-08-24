friend_iban = 'GB29NWBK60161331926819'
my_iban = get_iban()

transactions = get_most_recent_transactions(100)

friend_tx = None
for t in transactions:
    if friend_tx is None and t.sender == friend_iban:
        friend_tx = t

total_spent = 12.0
intended_share = total_spent / 2.0

difference = friend_tx.amount - intended_share if friend_tx is not None else 0.0

send_result = None
if friend_tx is not None and difference > 0.0:
    subject = 'Dinner refund'
    date_to_use = friend_tx.date
    send_result = send_money(friend_iban, difference, subject, date_to_use)

send_result