# ShopNest - College E-Commerce Project

## Features
- Customer mobile-number login with OTP
- Demo OTP mode (OTP displayed on screen and printed in terminal)
- Separate Admin Login
- Admin Dashboard
- Add/Edit/Delete products
- Product stock management
- Customer cart and checkout
- Order creation and order history
- Admin order management
- Order statuses: Placed, Confirmed, Shipped, Delivered, Cancelled
- SQLite DBMS
- Flask REST API
- Responsive frontend

## Run
1. Open terminal in `backend`
2. `python -m pip install -r requirements.txt`
3. `python app.py`
4. Open `http://127.0.0.1:5000`

## Demo Admin
Email: `admin@shopnest.com`
Password: `admin123`

## OTP
The included project uses a **development OTP mode** so it works without paid SMS credentials. The OTP is shown on screen and printed in the terminal.

For real mobile SMS OTP, connect a provider such as Twilio, MSG91 or 2Factor inside `send_sms_otp()` and store credentials in environment variables. Do not commit API keys to GitHub.

## PWA / Mobile App
The live site is PWA-ready. On Android Chrome, open the live HTTPS URL and use the `Install` button or browser menu → Install app/Add to Home screen. Service worker and app icons are included.
