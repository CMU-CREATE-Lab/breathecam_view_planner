import base64, flask, flask_login, json, mimetypes, os, requests, struct, threading, time
from flask import abort, request, redirect, Response, send_from_directory
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

def init_db(clear_all = False):
    if clear_all:
        engine.execute("DROP TABLE IF EXISTS panoramas")
        engine.execute("DROP TABLE IF EXISTS views")
        engine.execute("DROP TABLE IF EXISTS user_email_whitelist")
    engine.execute("""
        CREATE TABLE IF NOT EXISTS panoramas (
            id SERIAL PRIMARY KEY,
            data JSONB NOT NULL
        );""")
    engine.execute("""
        CREATE TABLE IF NOT EXISTS views (
            id SERIAL PRIMARY KEY,
            pano_id TEXT NOT NULL,
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
        return Response(open("index.html").read(), mimetype="text/html")

@app.get("/favicon.ico")
def favicon():
    return Response(open("favicon.ico", "rb").read(), mimetype="image/png")

@app.get("/compiled/<path:path>")
def compiled(path: str):
    # send_from_directory prevents attempts to traverse upwards
    return send_from_directory("compiled", path)

@app.post("/upload")
def upload():
    post = request.json
    print("upload")
    print(request.json)
    suffix = mimetypes.guess_extension(post["mimeType"])
    if not suffix in [".jpg", ".png"]:
        return(flask.jsonify({"success":False, "msg":f"Cannot upload image format {post['mimeType']} {suffix}"}))
    data = {"name": post["name"]}
    inserted = engine.insert("panoramas", {"data": json.dumps(data)})
    print(inserted)
    # How to get the unique ID?
    panorama_id = inserted["id"]
    print(f"panorama id is {panorama_id}")
    image_path = f"panos/{panorama_id}{suffix}"
    image_data = base64.b64decode(post["image"])
    open(image_path, "wb").write(image_data)
    data["imagePath"] = image_path
    engine.execute(f"UPDATE panoramas SET data=data || %s WHERE id={id}", (json.dumps({"imagePath"}),))
    print(f"Wrote {len(image_data)} bytes to {image_path}")
    return(flask.jsonify({"success":True, "id":panorama_id}))

