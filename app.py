import base64, flask, flask_login, gpano_exif, json, mimetypes, os, requests, struct, threading, time
from flask import abort, request, redirect, Response, send_from_directory
from flask_login import current_user, login_required, UserMixin
from google_login import GoogleLogin
from database import User, db_session, Panorama
from fovs import read_fovs
from typing import cast

from jinja2 import Environment, FileSystemLoader, select_autoescape
jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape())

os.chdir(os.path.dirname(os.path.realpath(__file__)))

app = flask.Flask(__name__)
app.secret_key = json.load(open("secrets/flask-secrets.json"))["secret_key"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

email_whitelist = [
    "randy.sargent@gmail.com",
    "ana@createlab.org",
    "atsuhlares@gmail.com",
    "pdille@andrew.cmu.edu",
    "paul.s.dille@gmail.com",
    "robmacl@cmu.edu", # listed on photo dir, but is it canonical?
    "robertm2@andrew.cmu.edu"
    ]

gl = GoogleLogin(app, login_manager, email_whitelist)

@app.before_request
def require_remote_ip():
    # valid_ips = [
    #     "71.182.150.189", # Randy's home network
    #     "96.236.147.52" # Randy's home network 
    # ]
    # remote_addr = request.remote_addr
    # if remote_addr == "127.0.0.1":
    #     remote_addr = request.headers['x-forwarded-for']
    # if not remote_addr in valid_ips:
    #     abort(403, f"Disallowing IP address {remote_addr}")
    pass

def get_google_provider_cfg():
    return requests.get("https://accounts.google.com/.well-known/openid-configuration").json()

@app.get("/test.html")
def show_test():
    template = jinja_env.get_template("test.html.j2")
    print("template", template)
    return Response(template.render(), mimetype="text/html")


@app.get("/")
@app.get("/p/<pano_id>")
@login_required
def show_panorama(pano_id = None):
    # if not current_user or not current_user.is_authenticated:
    #     gl.set_login_redirect(request.full_path)
    #     return redirect("/login")
    template = jinja_env.get_template("index.html.j2")
    print("template", template)
    panoramas = Panorama.query.all()
    if pano_id != None:
        panorama = Panorama.query.get(pano_id)
    else:
        panorama = None
    return Response(
        template.render(
            logged_in_name=cast(User, current_user).name, # ignore: type
            panorama=panorama,
            panoramas=panoramas,
            fovs=read_fovs()),
        mimetype="text/html")


@app.get("/favicon.ico")
def favicon():
    return Response(open("favicon.ico", "rb").read(), mimetype="image/png")

@app.get("/dist/<path:path>")
def compiled(path: str):
    # send_from_directory prevents attempts to traverse upwards
    return send_from_directory("dist", path)

@app.get("/image/<path:path>")
@login_required
def get_image(path: str):
    # send_from_directory prevents attempts to traverse upwards
    return send_from_directory("image", path)

@app.post("/upload")
@login_required
def upload():
    post = cast(dict, request.json)
    print("upload")
    mime_type = post["mimeType"]
    suffix = mimetypes.guess_extension(mime_type)
    if not suffix in [".jpg", ".png"]:
        return(flask.jsonify({"success":False, "msg":f"Cannot upload image format {post['mimeType']} {suffix}"}))
    tmp_image_path = Panorama.generate_tmp_image_path(suffix)
    image_data = base64.b64decode(post["image"])
    open(tmp_image_path, "wb").write(image_data)
    gpano_info = gpano_exif.GPanoInfo(tmp_image_path)

    # panorama = Panorama(
    #     name=post["name"], 
    #     image_suffix=suffix,
    #     image_mime_type=mime_type, 
    #     user=current_user,
    #     **gpano_info.as_dict())
    print(gpano_info.as_dict())

    panorama = Panorama(
        name=post["name"], 
        image_suffix=suffix,
        image_mime_type=mime_type, 
        user=current_user,
#        **{"image_cropped_width":gpano_info.as_dict()["image_cropped_width"]}
        **gpano_info.as_dict()
    )

    db_session.add(panorama)
    db_session.commit()
    image_path = panorama.image_path()
    os.rename(tmp_image_path, image_path)
    print(f"Wrote {len(image_data)} bytes to {image_path}")
    return(flask.jsonify({"success":True, "panorama":panorama.export_to_client()}))

@app.post("/delete")
@login_required
def delete():
    post = cast(dict, request.json)
    pano_id = post["pano_id"]
    print(f"deleting pano id {pano_id}")
    panorama = Panorama.query.get(pano_id)
    db_session.delete(panorama)
    db_session.commit()
    return(flask.jsonify({"success":True}))
    
