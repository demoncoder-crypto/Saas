from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import stripe
import sqlite3

app = Flask(__name__)
app.secret_key = 'name'

stripe.api_key = "name"
publishable_key = "name"

def init_db():
    with sqlite3.connect('database.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, plan TEXT)')
        conn.commit()

@app.route('/')
def index():
    return render_template('index.html', key=publishable_key)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']
    plan = request.form['plan']
    stripe_token = request.form['stripeToken']

    try:

        customer = stripe.Customer.create(
            email=email,
            source=stripe_token
        )

        
        stripe.Subscription.create(
            customer=customer.id,
            items=[{'plan': plan}]
        )

        
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO users (email, plan) VALUES (?, ?)', (email, plan))
            conn.commit()

        flash('Subscription successful!', 'success')
    except Exception as e:
        flash(str(e), 'danger')

    return redirect(url_for('index'))

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, 'your_webhook_secret'
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'invoice.payment_succeeded':
        customer_email = event['data']['object']['customer_email']
        flash(f'Payment succeeded for {customer_email}', 'success')

    return '', 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True)