target_iban = "GB29NWBK60161331926819"

my_iban = get_iban()
transactions = get_most_recent_transactions(500)

matching = [t for t in transactions if t.sender == target_iban and t.recipient == my_iban]

if len(matching) == 0:
    raise ValueError("No incoming transaction from the specified IBAN found to refund.")

original = matching[0]
send_money(original.sender, abs(original.amount), original.subject, original.date)