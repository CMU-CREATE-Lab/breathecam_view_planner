# Based loosely on https://realpython.com/flask-google-login/

# Usage:
# gl = GoogleLogin(epsql_database_engine, flask_app, login_manager)
# Will serve /login, /login/callback, and /logout
# Redirect to or visit /login to prompt user to log in
#
# flask_logincurrent_user.is_authenticated should be true if currently logged in

import flask, flask_login, json, requests, urllib
from oauthlib.oauth2 import WebApplicationClient
from flask import abort, request, redirect, session

from utils import epsql
from utils.epsql import Engine
from database import engine, User, db_session

def get_google_provider_cfg():
    return requests.get("https://accounts.google.com/.well-known/openid-configuration").json()

class GoogleLogin:
    def __init__(self, app: flask.Flask, login_manager, email_whitelist: None):
        self.app = app
        self.login_manager = login_manager
        self.email_whitelist = email_whitelist

        # self.engine.execute("""
        # CREATE TABLE IF NOT EXISTS users (
        #     id TEXT PRIMARY KEY,
        #     name TEXT NOT NULL,
        #     email TEXT UNIQUE NOT NULL
        # );""")
        google_client_info = json.load(open("secrets/google-oauth-client.json"))
        self.GOOGLE_CLIENT_ID = google_client_info["client_id"]
        self.GOOGLE_CLIENT_SECRET = google_client_info["client_secret"]
        self.client = WebApplicationClient(self.GOOGLE_CLIENT_ID)
        app.get("/login")(self.login)
        app.get("/login/callback")(self.login_callback)
        app.get("/logout")(self.logout)
        self.login_manager.user_loader(self.get_user)

    def get_user(self, user_id):
        return User.query.get(user_id)

    def set_login_redirect(self, url):
        session["login_redirect"] = url

    def login(self):
        # Find out what URL to hit for Google login
        google_provider_cfg = get_google_provider_cfg()
        print(google_provider_cfg)
        print(request.host)
        print(request.base_url)
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        redirect_uri = f"https://{request.host}/login/callback"
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
        print("in login_callback")
        print(token_response.status_code)
        print(token_response.text)
        print(token_response.json())

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

        if self.email_whitelist:
            if not users_email in self.email_whitelist:
                print(f"Email address {users_email} not in whitelist; refusing login")
                abort(400, f"Email address {users_email} not in whitelist;  please ask admin to add you.")
            else:
                print(f"Email address {users_email} found in whitelist.")
        else:
            print(f"No email whitelist; allowing {users_email}")

        # Create a user in your db with the information provided
        # by Google
        user = self.get_user(unique_id)
        if user:
            print("User already exists")
            user.name = users_name
            user.email = users_email
            db_session.commit()
        else:
            print("Created new user")
            user = User(id=unique_id, name=users_name, email=users_email)
            db_session.add(user)
            db_session.commit()

        # Begin user session by logging the user in
        flask_login.login_user(user)

        # Send user back to homepage, or "login_redirect" from session, if set
        return redirect(session.get("login_redirect", "/"))

    def logout(self):
        flask_login.logout_user()
        return redirect("/")


