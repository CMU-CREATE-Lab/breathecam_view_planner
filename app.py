import flask, flask_login, json, os, requests, struct, threading, time
from flask import abort, request, redirect
from utils import epsql
from flask_login import current_user, login_required
from google_login import GoogleLogin

engine = epsql.Engine(db_name="breathecam")

os.chdir(os.path.dirname(os.path.realpath(__file__)))

app = flask.Flask(__name__)
app.secret_key = json.load(open("secrets/flask-secrets.json"))["secret_key"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

gl = GoogleLogin(engine, app, login_manager)

def init_db():
    engine.execute("""
        CREATE TABLE IF NOT EXISTS panoramas (
            filename TEXT PRIMARY KEY,
            data JSONB NOT NULL
        );""")
    engine.execute("""
        CREATE TABLE IF NOT EXISTS views (
            id SERIAL PRIMARY KEY,
            pano_filename TEXT NOT NULL,
            data JSONB NOT NULL
        )""");
    # Create user_email_whitelist
    engine.execute("""
        CREATE TABLE IF NOT EXISTS user_email_whitelist (
            email TEXT UNIQUE NOT NULL
        );""")
    engine.insert_unless_conflict("user_email_whitelist", {"email": "randy.sargent@gmail.com"})

init_db()

@app.before_request
def require_remote_ip():
    valid_ips = [
        "71.182.150.189" # Randy's home network
    ]
    remote_addr = request.remote_addr
    if remote_addr == "127.0.0.1":
        remote_addr = request.headers['x-forwarded-for']
    if not remote_addr in valid_ips:
        abort(403, f"Disallowing IP address {request.remote_addr}")

def get_google_provider_cfg():
    return requests.get("https://accounts.google.com/.well-known/openid-configuration").json()

@app.get("/")
def index():
    if not current_user.is_authenticated:
        return redirect("/login")
    else:
        return f"""
            <p>Hello, {current_user.name}! You're logged in! Email: {current_user.email}</p>
            <a class="button" href="/logout">Logout</a>"""


