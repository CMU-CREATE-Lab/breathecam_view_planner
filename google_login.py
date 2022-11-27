# Based loosely on https://realpython.com/flask-google-login/

# Usage:
# gl = GoogleLogin(epsql_database_engine, flask_app, login_manager)
# Will serve /login, /login/callback, and /logout
# Redirect to or visit /login to prompt user to log in
#
# flask_logincurrent_user.is_authenticated should be true if currently logged in

import flask, flask_login, json, requests
from oauthlib.oauth2 import WebApplicationClient
from flask import abort, request, redirect

from utils import epsql
from utils.epsql import Engine

def get_google_provider_cfg():
    return requests.get("https://accounts.google.com/.well-known/openid-configuration").json()

class GoogleLogin:
    def __init__(self, engine: Engine, app: flask.Flask, login_manager):
        self.engine = engine
        self.app = app
        self.login_manager = login_manager

        self.engine.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        );""")
        google_client_info = json.load(open("secrets/google-oauth-client.json"))
        self.GOOGLE_CLIENT_ID = google_client_info["client_id"]
        self.GOOGLE_CLIENT_SECRET = google_client_info["client_secret"]
        self.client = WebApplicationClient(self.GOOGLE_CLIENT_ID)
        app.get("/login")(self.login)
        app.get("/login/callback")(self.login_callback)
        app.get("/logout")(self.logout)
        self.login_manager.user_loader(self.get_user)

    def get_user(self, user_id):
        users = self.engine.execute_returning_dicts(
            "SELECT * FROM users WHERE id = %s", (user_id,)
        )
        if len(users) == 0:
            return None

        user = users[0]

        print(user)

        user = User(
            user_id=user["id"], name=user["name"], email=user["email"]
        )
        return user

    def create_user(self, user_id, name, email):
        self.engine.insert("users", {"id": user_id, "name": name, "email": email})
    
    def login(self):
        # Find out what URL to hit for Google login
        google_provider_cfg = get_google_provider_cfg()
        print(google_provider_cfg)
        print(request.host)
        print(request.base_url)
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        redirect_uri = f"https://{request.host}/login/callback"
        print(redirect_uri)
        # Use library to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        request_uri = self.client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    
    def login_callback(self):
        # Get authorization code Google sent back to you
        code = request.args.get("code")
        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send a request to get tokens! Yay tokens!
        token_url, headers, body = self.client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http:", "https:"),
            redirect_url=request.base_url.replace("http:", "https:"),
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(self.GOOGLE_CLIENT_ID, self.GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens!
        self.client.parse_request_body_response(json.dumps(token_response.json()))

        # Now that you have tokens (yay) let's find and hit the URL
        # from Google that gives you the user's profile information,
        # including their Google profile image and email
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = self.client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # You want to make sure their email is verified.
        # The user authenticated with Google, authorized your
        # app, and now you've verified their email through Google!
        if userinfo_response.json().get("email_verified"):
            unique_id = userinfo_response.json()["sub"]
            users_email = userinfo_response.json()["email"]
            users_name = userinfo_response.json()["given_name"]
        else:
            abort(400, "User email not available or not verified by Google.")

        # Create a user in your db with the information provided
        # by Google
        user = User(user_id=unique_id, name=users_name, email=users_email)

        # Doesn't exist? Add it to the database.
        if not self.get_user(unique_id):
            print("Created new user")
            User.create(unique_id, users_name, users_email)
        else:
            # TODO: should we update the user info?
            print("User already exists")

        # Begin user session by logging the user in
        flask_login.login_user(user)

        # Send user back to homepage
        return redirect("/")

    def logout(self):
        flask_login.logout_user()
        return redirect("/")


class User(flask_login.UserMixin):
    def __init__(self, user_id: str, name: str, email: str):
        self.id = user_id
        self.name = name
        self.email = email