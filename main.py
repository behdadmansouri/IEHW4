import jwt
import sqlite3
from functools import wraps

from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
app.config['SECRET_KEY'] = 'password'


def db_query(query):
    con = sqlite3.connect('website.db')
    cur = con.cursor()
    cur.execute(query)
    con.commit()
    result = cur.fetchall()
    con.close()
    return result


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if 'jwt_token' not in request.headers:
            return make_response({'message': 'a valid token is missing'}, 401)
        else:
            # print(jwt.encode({
            #     'user_id': 1,
            # }, app.config['SECRET_KEY']
            #     , algorithm='HS256'))
            token = request.headers['jwt_token']
            # with token
            try:
                our_jwt = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                user_id = our_jwt['user_id']

                query = 'SELECT ROLE FROM USER WHERE ID=%i' % user_id
                role = db_query(query)[0][0]
            except:
                return make_response({'message': 'token not found in database'}, 401)

        return f(role, *args, **kwargs)

    return decorator


@app.route("/admin/movie", methods=['POST'])
@token_required
def admin_movie_insert(role):
    try:
        if role < 1:
            return make_response({'message': 'Not Authorized'}, 401)
        content = request.json
        name = content.get('name')
        description = content.get('description')
        if (name is not None and description is not None and
                type(name) == str and type(description) == str):
            db_query('INSERT INTO MOVIE (NAME DESCRIPTION) VALUES ("%s", "%s")' % (name, description))

        # Bad Request
        else:
            return make_response({'message': 'Bad Request'}, 400)

        # SUCCESS
        return make_response({'message': 'ok'}, 204)
    except Exception:
        return make_response({'message': 'internal server error'}, 500)


@app.route("/admin/movie/<movie_id>", methods=['PUT', 'DELETE'])
@token_required
def admin_movie_update_delete(role, movie_id):
    try:
        if role < 1:
            return make_response({'message': 'Not Authorized'}, 401)

        if request.method == 'PUT':
            content = request.json
            name = content.get('name')
            description = content.get('description')
            if (name is not None and description is not None and
                    type(name) == str and type(description) == str):
                db_query('UPDATE MOVIE SET NAME="%s", DESCRIPTION="%s" WHERE ID=%i' % (name, description, movie_id))
            else:
                return make_response({'message': 'Bad Request'}, 400)
        elif request.method == 'DELETE':
            db_query('DELETE FROM MOVIE WHERE ID=%i' % movie_id)

        # SUCCESS
        return make_response(204, {'message': 'ok'})
    except Exception:
        return make_response({'message': 'internal server error'}, 500)


@app.route("/admin/comment/<comment_id>", methods=['PUT', 'DELETE'])
@token_required
def admin_comment_update_delete(role, comment_id):
    try:
        if role < 1:
            return make_response({'message': 'Not Authorized'}, 401)

        if request.method == 'PUT':
            content = request.json
            approved = content.get('approved')
            if approved is not None and type(approved) == bool:
                db_query('UPDATE COMMENTS SET APPROVED={0} WHERE COMMENT_ID={1}'.format(approved, comment_id))
            else:
                return make_response({'message': 'Bad Request'}, 400)

        elif request.method == 'DELETE':
            db_query('DELETE FROM COMMENTS WHERE COMMENT_ID=%i' % comment_id)

        # SUCCESS
        return make_response({'message': 'ok'}, 204)
    except Exception:
        return make_response({'message': 'internal server error'}, 500)


@app.route("/user/comment", methods=['POST'])
@token_required
def user_comment(role):
    # try:
    if role < 0:
        return make_response({'message': 'Not Authorized'}, 401)

    user_id = jwt.decode(request.headers['jwt_token'], app.config['SECRET_KEY'], algorithms=['HS256'])['user_id']
    content = request.json
    movie_id = content.get('movie_id')
    comment_body = content.get('comment_body')
    if (movie_id is not None and comment_body is not None and
            type(movie_id) == int and type(comment_body) == str):
        db_query('INSERT INTO COMMENTS (USER_ID, MOVIE_ID, COMMENT, CREATEDAT)'
                 ' VALUES (%i, %i, "%s", datetime(\'now\'))' % (user_id, movie_id, comment_body))

        # SUCCESS
        return make_response({'message': 'ok'}, 204)
    else:
        return make_response({'message': 'Bad Request'}, 400)
    # except Exception:
    #     return make_response({'message': 'internal server error'}, 500)


@app.route("/user/vote", methods=['POST'])
@token_required
def user_vote(role):
    try:
        if role < 0:
            return make_response({'message': 'Not Authorized'}, 401)
        user_id = jwt.decode(request.headers['jwt_token'])['user_id']
        content = request.json
        movie_id = content.get('movie_id')
        vote = content.get('vote')

        if (movie_id is not None and vote is not None and
                type(movie_id) == int and type(vote) == int):
            db_query('INSERT INTO COMMENTS (USER_ID, MOVIE_ID, RATING) VALUES (%i, %i, %d)'
                     % (user_id, movie_id, vote / 10))
        else:
            return make_response({'message': 'Bad Request'}, 400)
        # SUCCESS
        return make_response({'message': 'ok'}, 204)
    except Exception:
        return make_response({'message': 'internal server error'}, 500)


@app.route("/comments/<movie_id>", methods=['GET'])
def comments(movie_id):
    try:
        args = request.args
        movie_id = args.get('movie_id')
        if movie_id is not None and type(movie_id) == int:
            query = 'SELECT C.ID, U.USERNAME, C.COMMENT ' \
                    'FROM COMMENTS AS C AND USER AS U AND MOVIE AS M ' \
                    'WHERE C.USER_ID=U.ID AND M.ID=C.MOVIE_ID ' \
                    'AND M.ID=%i AND C.APPROVED=1;' % movie_id  # TODO use _Join_ instead of _Where_
            comment_list = []
            for row in db_query(query):
                comment_list.append({'author': row[0], 'body': row[1]})

            return make_response(comment_list, 200)
    except Exception:
        return make_response({'message': 'internal server error'}, 500)


@app.route("/movies", methods=['GET'])
def public_list_movies():
    try:
        query = 'SELECT ID, NAME, DESCRIPTION, RATING FROM MOVIE'
        movie_list = []
        for row in db_query(query):
            movie_list.append({'id': row[0], 'name': row[1], 'description': row[2], 'rating': row[3]})

        return make_response(jsonify('movies', movie_list), 200)
    except Exception:
        return make_response({'message': 'internal server error'}, 500)


@app.route("/movie/<movie_id>", methods=['GET'])
def public_movie(movie_id):
    try:
        query = ('SELECT ID, NAME, DESCRIPTION, RATING FROM MOVIE WHERE id=%i' % movie_id)
        movie_info = {}
        for row in db_query(query):
            movie_info = {'id': row[0], 'name': row[1], 'description': row[2], 'rating': row[3]}
            break
        return make_response(jsonify(movie_info), 200)
    except Exception:
        # return make_response({'message': 'internal server error'}, 500)
        pass


app.run(debug=True)
