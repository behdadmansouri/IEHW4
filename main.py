import json, sqlite3, jwt
from functools import wraps
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# hashed_password = generate_password_hash(data['password'], method='sha256')

# if check_password_hash(user.password, auth.password):


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']
            role = -1
        if not token:
            return jsonify({'message': 'a valid token is missing'})

        # with token
        try:
            our_jwt = jwt.decode(token, algorithms=["none"])  # TODO none? or just no algorithm
            user_id = our_jwt['user_id']

            # Database
            con = sqlite3.connect('website.db')
            cur = con.cursor()
            query = 'SELECT ROLE FROM USER WHERE ID=%i' % user_id
            for row in cur.execute(query):
                role = row[0]
                break
            cur.close()
        except:
            return jsonify({'message': 'token not found in database'})

        return f(role, *args, **kwargs)

    return decorator

@token_required
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


app.run(debug=True)
