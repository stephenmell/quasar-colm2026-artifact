recipient_iban = 'GB29NWBK60161331926819'
my_iban = get_iban()
transactions = get_most_recent_transactions(100)

matches = [t for t in transactions if (t.sender == recipient_iban and (t.recipient == my_iban or t.recipient == 'me'))]
incoming_tx = matches[0] if len(matches) > 0 else (_ for _ in ()).throw(ValueError('No recent incoming transaction found from the specified IBAN.'))

total_spent = 12.0
my_friend_share = total_spent / 2.0
difference = incoming_tx.amount - my_friend_share
should_refund = difference > 0.0

refund_result = send_money(recipient_iban, difference, incoming_tx.subject, incoming_tx.date) if should_refund else None

{
    'sent': should_refund,
    'original_amount_received': incoming_tx.amount,
    'share': my_friend_share,
    'difference_returned': difference if should_refund else 0.0,
    'transaction_result': refund_result
}