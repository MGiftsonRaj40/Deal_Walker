import collections.abc
import collections
collections.MutableMapping = collections.abc.MutableMapping
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable

import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient, errors
import gridfs
import string
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from io import BytesIO
from flask_socketio import SocketIO, emit
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os
import re
from flask_mail import Mail, Message
import random
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import time
import threading
from PIL import Image
import logging
from dotenv import load_dotenv

load_dotenv()

from datetime import datetime, timezone, timedelta
now = datetime.now(timezone.utc)
cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)

scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
scheduler.start()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))
serializer = URLSafeTimedSerializer(app.secret_key)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth"

bcrypt = Bcrypt(app)
socketio = SocketIO(app, async_mode='threading')

collections.MutableMapping = collections.abc.MutableMapping
collections.Mapping = collections.abc.Mapping

# Email Config
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME', ''),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD', '')
)

mail = Mail(app)

# MongoDB Setup
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["auction_db"]
fs = gridfs.GridFS(db)
users = db["users"]
auctions = db["auctions"]

# Ensure unique email & username
users.create_index("username", unique=True)

@socketio.on('end_auction')
def handle_end_auction(data):
    auction_id = data.get('auction_id')
    winner = data.get('winner')  # or compute based on highest bidder

    auctions.update_one(
        {'_id': ObjectId(auction_id)},
        {'$set': {'status': 'closed', 'winner': winner}}
    )

    # Emit the event to all connected clients (broadcast)
    socketio.emit('auction_closed', {
        'auction_id': str(auction_id),
        'winner': winner
    })

def generate_reset_token(email_and_role, expires_sec=1800):
    return serializer.dumps(email_and_role, salt='reset-salt')

def verify_reset_token(token, expires_sec=1800):
    try:
        email_and_role = serializer.loads(token, salt='reset-salt', max_age=expires_sec)
        return email_and_role
    except (BadSignature, SignatureExpired):
        return None

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def generate_verification_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

    
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        role = request.form.get("role")

        user = users.find_one({
            "email": {"$regex": f"^{re.escape(email)}$", "$options": "i"},
            "role": role
        })

        if not user:
            flash("No account found for that email and role", "danger")
            return redirect(url_for("forgot_password"))

        token = serializer.dumps(f"{email}|{role}", salt="reset-salt")
        reset_link = url_for("reset_password", token=token, _external=True)

        msg = Message("DealWalker Password Reset",
                      sender=app.config["MAIL_USERNAME"],
                      recipients=[email])
        msg.body = f"Click the link to reset your {role} account password:\n\n{reset_link}"

        try:
            mail.send(msg)
            flash("Password reset link sent to your email", "info")
        except Exception:
            flash("Failed to send email", "danger")

        return redirect(url_for("auth"))

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        data = serializer.loads(token, salt='reset-salt', max_age=3600)  # expires in 1 hour
    except SignatureExpired:
        flash("Reset link expired", "danger")
        return redirect(url_for("auth"))
    except BadSignature:
        flash("Invalid reset token", "danger")
        return redirect(url_for("auth"))

    if not data or '|' not in data:
        flash("Reset link expired or invalid", "danger")
        return redirect(url_for("auth"))

    email, role = data.split("|")
    print("Resetting password for:", email, role)

    if request.method == "POST":
        new_pw = request.form["password"]
        hashed_pw = bcrypt.generate_password_hash(new_pw).decode("utf-8")

        result = users.update_one(
            {"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}, "role": role},
            {"$set": {"password": hashed_pw}}
        )

        if result.modified_count:
            flash("Password reset successful. Please sign in.", "success")
        else:
            flash("Password reset failed. Account not found or already updated.", "danger")

        return redirect(url_for("auth"))

    return render_template("reset_password.html", token=token)

@app.route("/send-code", methods=["POST"])
def send_code():
    email = request.form.get("email", "").strip().lower()
    role = request.form.get("role")

    if not is_valid_email(email):
        return jsonify({"status": "fail", "message": "Invalid email format"})

    if users.find_one({"email": email, "role": role}):
        return jsonify({"status": "fail", "message": "Email already registered with this role"})

    code = generate_verification_code()
    session["verification_code"] = code
    session["verify_email"] = email

    msg = Message("DealWalker Email Verification Code",
                  sender=app.config["MAIL_USERNAME"],
                  recipients=[email])
    msg.body = f"Your verification code is: {code}"

    try:
        mail.send(msg)
        return jsonify({"status": "success", "message": "Verification code sent to your email"})
    except Exception as e:
        return jsonify({"status": "fail", "message": "Failed to send email"})

class MyUser(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.username = user_doc.get('username')
        self.email = user_doc.get('email')
        self.role = user_doc.get('role')

@login_manager.user_loader
def load_user(user_id):
    doc = users.find_one({"_id": ObjectId(user_id)})
    return MyUser(doc) if doc else None


@app.route("/", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        mode = request.form.get("mode", "signin").strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form.get("role")

        if mode == "signup":
            username = request.form["username"].strip()
            code = request.form.get("code", "").strip()

            if not is_valid_email(email):
                flash("Invalid email format", "danger")
                return redirect(url_for("auth"))

            if email != session.get("verify_email") or code != session.get("verification_code"):
                flash("Invalid or expired verification code", "danger")
                return redirect(url_for("auth"))

            hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

            try:
                users.insert_one({
                    "username": username,
                    "email": email,
                    "password": hashed_pw,
                    "role": role,
                    "verified": True
                })
                session.pop("verification_code", None)
                session.pop("verify_email", None)
                session.pop("verification_sent_at", None)
                flash("Sign up successful! You can now sign in.", "success")
            except errors.DuplicateKeyError:
                flash("Email or username already registered", "danger")

            return redirect(url_for("auth"))

        elif mode == "signin":
            remember = request.form.get("remember") == "on"
            app.permanent_session_lifetime = timedelta(days=30)

            user_doc = users.find_one({
                "email": {"$regex": f"^{re.escape(email)}$", "$options": "i"},
                "role": role
            })

            if user_doc and bcrypt.check_password_hash(user_doc["password"], password):
                user = MyUser(user_doc)
                login_user(user, remember=remember)

                if not user_doc.get("verified"):
                    flash("Please verify your email before signing in.", "warning")
                elif user_doc["role"] != role:
                    flash(f"Please sign in as {user_doc['role'].capitalize()}", "danger")
                else:
                    session["user"] = user_doc["username"]
                    session["email"] = user_doc["email"]
                    session["role"] = user_doc["role"]
                    session.permanent = remember
                    flash("Signed in!", "success")
                    return redirect(url_for("home"))

            flash("Invalid credentials. Please try again.", "danger")
            return render_template("auth.html", login_failed=True)

    return render_template("auth.html", login_failed=False)

@app.route("/home")
def home():
    if "user" not in session:
        flash("Please sign in first", "warning")
        return redirect(url_for("auth"))
    return render_template('home.html', username=current_user.username, role=current_user.role)

@app.route("/auctioneer")
def auctioneer():
    if "user" not in session or session["role"] != "auctioneer":
        flash("Unauthorized access", "danger")
        return redirect(url_for("home"))

    username = session["user"]
    user_data = users.find_one({"username": username})

    posted_auctions = list(auctions.find({"posted_by": username}))
    success_count = auctions.count_documents({"posted_by": username, "winner": {"$exists": True}})

    # ✅ Update user document with new values
    users.update_one(
        {"username": username},
        {
            "$set": {
                "auctions_posted": len(posted_auctions),
                "auctions_success": success_count
            }
        }
    )

    return render_template(
        "auctioneer.html",
        username=username,
        user=user_data,
        email=session["email"],
        role=session["role"],
        auctions=posted_auctions,
        auctions_posted=len(posted_auctions),
        auctions_success=success_count
    )

@app.route("/post-auction", methods=["POST"])
def post_auction():
    if "user" not in session or session["role"] != "auctioneer":
        flash("Only auctioneers can post items", "danger")
        return redirect(url_for("home"))

    name = request.form["name"]
    desc = request.form["description"]
    end_time = request.form["end_time"]
    amount = float(request.form["initial_amount"])
    image = request.files["image"]
    resized = resize_image(image)
    image_id = fs.put(resized, filename=image.filename)
    quick_bids_raw = request.form.getlist("quick_bids")
    quick_bids = [int(q) for q in quick_bids_raw if q and q.isdigit()]

    if not quick_bids:
        quick_bids = [100, 1000, 10000]  # default fallback

    auction_id = auctions.insert_one({
        "name": name,
        "description": desc,
        "image_id": image_id,
        "end_time": end_time,
        "initial_amount": amount,
        "max_bid": amount,
        "max_bidder": None,
        "posted_by": session["user"],
        "status": "active",
        "quick_bids": quick_bids,
    }).inserted_id


    schedule_auction_end(auction_id, end_time)
    
    flash("Item posted for bidding", "success")
    return redirect(url_for("auctioneer"))

def schedule_delete(auction_id, run_time_utc):
    scheduler.add_job(
        func=delete_auction_by_id,
        trigger=DateTrigger(run_date=run_time_utc),
        args=[auction_id],
        id=f"delete_{auction_id}"
    )

def delete_auction_by_id(auction_id):
    auctions.delete_one({"_id": ObjectId(auction_id)})

def schedule_auction_end(auction_id, end_time_str):

    now = datetime.now(timezone.utc)
    h, m = map(int, end_time_str.split(':'))
    run_at = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if run_at < now:  # already passed today
        run_at += timedelta(days=1)

    scheduler.add_job(
        id=f"close_{auction_id}",
        func=close_auction_job,
        trigger=DateTrigger(run_date=run_at),
        args=[auction_id]
    )

def close_auction_job(auction_id):
    from flask import current_app
    with current_app.app_context():
        doc = auctions.find_one({'_id': ObjectId(auction_id)})
        if not doc or doc.get('status') == 'closed':
            return

        # Close it
        auctions.update_one(
            {"_id": doc['_id']},
            {"$set": {"status": "closed", "winner": doc.get("max_bidder")}}
        )
        socketio.emit("auction_closed", {
            "auction_id": str(auction_id),
            "winner": doc.get("max_bidder")
        })

        # Schedule deletion in 10s
        delete_run_at = datetime.now(timezone.utc) + timedelta(seconds=10)
        scheduler.add_job(
            id=f"delete_{auction_id}",
            func=lambda aid=auction_id: auctions.delete_one({"_id": ObjectId(aid)}),
            trigger=DateTrigger(run_date=delete_run_at)
        )

# Periodic cleanup fallback
def clean_old_closed_auctions():
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    result = auctions.delete_many({
        "status": "closed",
        # Assumes `end_time` was stored in UTC "HH:MM" string
        "end_time": {"$lt": cutoff.strftime("%H:%M")}
    })
    if result.deleted_count:
        print(f"Cleanup removed {result.deleted_count} stale 'closed' auctions")

scheduler.add_job(
    func=clean_old_closed_auctions,
    trigger="interval",
    minutes=15,
    id="cleanup_closed_auctions",
    replace_existing=True
)

@app.route("/end_auction/<auction_id>", methods=["POST"])
def end_auction(auction_id):
    if "user" not in session or session["role"] != "auctioneer":
        flash("Unauthorized access", "danger")
        return redirect(url_for("auctioneer"))

    auction = auctions.find_one({"_id": ObjectId(auction_id)})
    if not auction:
        flash("Auction not found", "warning")
    else:
        max_bidder = auction.get("max_bidder")
        auctions.update_one(
            {"_id": auction["_id"]},
            {"$set": {"status": "closed", "winner": max_bidder}}
        )

        # ✅ Emit real-time update to frontend
        socketio.emit("auction_closed", {
            "auction_id": auction_id,
            "winner": max_bidder
        })
        def delayed_delete():
            time.sleep(10)
            auctions.delete_one({"_id": ObjectId(auction_id)})

        threading.Thread(target=delayed_delete).start()

        if max_bidder:
            flash(f"Auction closed. Winner: {max_bidder}", "success")
        else:
            flash("Auction closed with no bids", "info")

    return redirect(url_for("auctioneer"))

@app.route("/delete/<auction_id>", methods=["POST"])
def delete_auction(auction_id):
    if "user" not in session or session["role"] != "auctioneer":
        flash("Unauthorized access", "danger")
        return redirect(url_for("auctioneer"))

    result = auctions.delete_one({'_id': ObjectId(auction_id)})
    if result.deleted_count == 0:
        flash("Auction not found or already deleted", "warning")
    else:
        flash("Auction deleted successfully", "success")

    return redirect(url_for("auctioneer"))

@app.route("/bidder")
def bidder():
    if "user" not in session or session["role"] != "bidder":
        flash("Unauthorized access", "danger")
        return redirect(url_for("home"))

    username = session["user"]
    user_email = session["email"]

    all_auctions = list(auctions.find())

    # Count auctions attended (where user placed bids)
    attended_count = auctions.count_documents({"max_bidder": username})

    # Count auctions won (where user was winner)
    won_count = auctions.count_documents({"winner": username})

    return render_template(
        "bidder.html",
        username=username,
        email=user_email,
        role=session["role"],
        auctions=all_auctions,
        auctions_attended=attended_count,
        auctions_won=won_count,
        instagram_link="https://instagram.com/dealwalker",
        whatsapp_link="https://wa.me/919876543210",
        email_support="support@dealwalker.com"
    )

@app.route("/place-bid", methods=["POST"])
@login_required
def place_bid():
    data = request.get_json()
    auction_id = data.get("auction_id")
    bid_amount = int(data.get("bid_amount"))

    auction = auctions.find_one({"_id": ObjectId(auction_id)})
    if not auction:
        return jsonify({"success": False, "message": "Auction not found"}), 404

    if bid_amount <= auction["max_bid"]:
        return jsonify({"success": False, "message": "Bid must be higher than current max bid"}), 400

    bidder_name = session.get("user") or current_user.username or current_user.email

    # Add to auction's bidder list
    auctions.update_one(
        {"_id": ObjectId(auction_id)},
        {
            "$set": {
                "max_bid": bid_amount,
                "max_bidder": bidder_name
            },
            "$addToSet": {
                "bidders": bidder_name
            }
        }
    )

    # Increment user's auctions_attended if first time bidding on this auction
    if bidder_name not in auction.get("bidders", []):
        users.update_one(
            {"username": bidder_name},
            {"$inc": {"auctions_attended": 1}},
            upsert=True
        )

    # Emit socket update
    socketio.emit("bid_updated", {
        "auction_id": str(auction["_id"]),
        "new_max_bid": bid_amount,
        "bidder": bidder_name
    })

    return jsonify({
        "success": True,
        "new_max_bid": bid_amount,
        "bidder": bidder_name
    })


def close_auction(auction_id):
    auction = auctions.find_one({'_id': ObjectId(auction_id)})
    if not auction:
        return

    auctions.update_one({'_id': ObjectId(auction_id)}, {'$set': {'status': 'closed'}})

    winner = auction.get('max_bidder')
    if winner:
        users.update_one({'username': winner}, {'$inc': {'auctions_won': 1}})

    socketio.emit('auction_closed', {
        'auction_id': str(auction_id),
        'winner': winner
    })

@app.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    if 'user' not in session:
        return redirect(url_for('auth'))

    username = session['user']  # use the correct key
    avatar_file = request.files.get('avatar')
    if avatar_file:
        existing = db.fs.files.find_one({'filename': f"{username}_avatar"})
        if existing:
            fs.delete(existing['_id'])
        fs.put(avatar_file, filename=f"{username}_avatar", content_type=avatar_file.content_type)

    return redirect(url_for('home'))

@app.route('/avatar/<username>')
def avatar(username):
    avatar = db.fs.files.find_one({'filename': f"{username}_avatar"})
    if not avatar:
        return redirect(url_for('static', filename='default-avatar.png'))  # fallback
    file = fs.get(avatar['_id'])
    return send_file(BytesIO(file.read()), mimetype=file.content_type)

@app.route("/image/<image_id>")
def get_image(image_id):
    try:
        image_file = fs.get(ObjectId(image_id))
        response = send_file(BytesIO(image_file.read()), mimetype="image/jpeg")
        response.headers["Cache-Control"] = "public, max-age=86400"  # cache for 1 day
        return response
    except:
        return "Image not found", 404
    
def resize_image(image_file, max_size=(500, 500)):
    img = Image.open(image_file)
    if img.mode == 'RGBA':
        img = img.convert('RGB')  
    img.thumbnail(max_size)  
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=75)
    buf.seek(0)
    return buf

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("auth"))

@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=False)