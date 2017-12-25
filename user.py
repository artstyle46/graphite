from flask import request, abort
from flask import g
import json
from flask_restful import Resource
from passlib.hash import sha256_crypt

from bson.json_util import loads, dumps, ObjectId


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

class Login(Resource):

    def post(self):
        email = request.json['email'].strip().lower()
        password = request.json['password']
        user = g.dbclient['users'].find({'email': email})
        if not user:
            g.logger.error('user email %s not found aborting:' % email)
            abort(400, {'message': 'email not found'})
        else:
            user = user[0]
        if not sha256_crypt.verify(password, user['password']):
            abort(400, {'message': 'password didn\'t match'})

        return {'message': {'user': JSONEncoder().encode(user), 'status': 200}}


class Register(Resource):

    def post(self):
        user_db = g.dbclient['users']
        email = request.json['email'].strip().lower()
        password = request.json['password']
        hash_password = sha256_crypt.encrypt(password)
        user_type = 'customer'
        try:
            mobile_no = int(request.json['mobile_no'])
        except Exception as e:
            abort(400, 'invalid mobile number')
        user = {
            'email': email,
            'password': hash_password,
            'mobile_no': mobile_no,
            'user_type': user_type
        }
        inserted_id= user_db.insert_one(user).inserted_id
        g.logger.info('user created with id: %s' % str(inserted_id))

        return {'message': {'msg': 'registration successful', 'status': 200}}

class VendorRegister(Resource):

    def post(self):
        user_db = g.dbclient['users']
        email = request.json['email'].strip().lower()
        password = request.json['password']
        hash_password = sha256_crypt.encrypt(password)
        user_type = 'vendor'
        try:
            mobile_no = int(request.json['mobile_no'])
        except Exception as e:
            abort(400, 'invalid mobile number')
        user = {
            'email': email,
            'password': hash_password,
            'mobile_no': mobile_no,
            'user_type': user_type
        }
        inserted_id = user_db.insert_one(user).inserted_id
        g.logger.info('user created with id: %s' % str(inserted_id))

        return {'message': {'msg': 'registration successful', 'status': 200}}

class UpdatePassword(Resource):

    def post(self):
        user_db = g.dbclient['users']
        email = request.json['email'].strip().lower()
        password = request.json['password']
        hash_password = sha256_crypt.encrypt(password)
        user_upd = user_db.update_one({'email': email}, {'$set': {'password': hash_password}})
        if not user_upd.modified_count:
            abort(400, 'unable to update password')
        return {'message': {'msg': 'password updated successfully', 'status': 200}}

