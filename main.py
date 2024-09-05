import requests
import random
import string
from flask import Flask, render_template, redirect, request, url_for, jsonify
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from helpers import is_access_token_valid, is_id_token_valid, config
from user import User
import datetime
import uuid
import jwt # type: ignore

app = Flask(__name__)
app.config.update({'SECRET_KEY': ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=32))})

login_manager = LoginManager()
login_manager.init_app(app)


APP_STATE = 'ApplicationState'
NONCE = 'SampleNonce'

secretId = "ea8a889f-0c9c-4044-b3cb-f7e7e1574ed9"
secretValue = "8zi6UsnFasZnwy4hhj5/4vBRzAC7aUWy8Av9nfwHy9M="
clientId = "c0a2f4b9-d484-4573-9452-1f95ad3cc3ce"

@app.after_request  
def apply_csp(response):  
    csp_policy = "frame-ancestors 'self' https://10ay.online.tableau.com"  
    response.headers['Content-Security-Policy'] = csp_policy  
    return response

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login")
def login():
    # get request params
    query_params = {'client_id': config["client_id"],
                    'redirect_uri': config["redirect_uri"],
                    'scope': "openid email profile",
                    'state': APP_STATE,
                    'nonce': NONCE,
                    'response_type': 'code',
                    'response_mode': 'query'}

    # build request_uri
    request_uri = "{base_url}?{query_params}".format(
        base_url=config["auth_uri"],
        query_params=requests.compat.urlencode(query_params)
    )

    return redirect(request_uri)


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)

@app.route('/get_jwt_token', methods=['POST'])
@login_required
def get_jwt_token():  
    user_email = request.json.get('email')  # Fetch the email from the request  

    if not user_email:  
        return jsonify({"error": "Email is required"}), 400  

    # Generate the JWT token  
    payload = {
        "iss": clientId,  
        "sub": user_email,  
        "aud": "tableau",  
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15),  
        "nbf": datetime.datetime.utcnow(),  
        "jti": str(uuid.uuid4()),
        "scp": ["tableau:views:embed"]  
    }  

    token = jwt.encode(payload, secretValue, headers={
            "kid": secretId,
            "iss": clientId,
            "alg": "HS256",
        })  
    return jsonify({"token": token})  


@app.route("/oidc/callback")
def callback():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    code = request.args.get("code")
    if not code:
        return "The code was not returned or is not accessible", 403
    query_params = {'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': request.base_url
                    }
    query_params = requests.compat.urlencode(query_params)
    exchange = requests.post(
        config["token_uri"],
        headers=headers,
        data=query_params,
        auth=(config["client_id"], config["client_secret"]),
    ).json()

    # Get tokens and validate
    if not exchange.get("token_type"):
        return "Unsupported token type. Should be 'Bearer'.", 403
    access_token = exchange["access_token"]
    id_token = exchange["id_token"]

    if not is_access_token_valid(access_token, config["issuer"]):
        return "Access token is invalid", 403

    if not is_id_token_valid(id_token, config["issuer"], config["client_id"], NONCE):
        return "ID token is invalid", 403

    # Authorization flow successful, get userinfo and login user
    userinfo_response = requests.get(config["userinfo_uri"],
                                     headers={'Authorization': f'Bearer {access_token}'}).json()

    unique_id = userinfo_response["sub"]
    user_email = userinfo_response["email"]
    user_name = userinfo_response["given_name"]

    user = User(
        id_=unique_id, name=user_name, email=user_email
    )

    if not User.get(unique_id):
        User.create(unique_id, user_name, user_email)

    login_user(user)

    return redirect(url_for("profile"))


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(host="localhost", port=8002, debug=True)