import datetime

from flask import request, abort
from flask import g

import requests

from user import JSONEncoder

from flask_restful import Resource
from bson.json_util import ObjectId, loads
from random import randint
import os
from boto.s3.key import Key
from boto.s3.connection import S3Connection
import json
from os.path import expanduser
home = expanduser("~")

graphite_config = json.load(open(os.path.join(home, ".graphite.json")))

ACCESS_KEY = graphite_config["access_key"]
SECRET_ACCESS_KEY = graphite_config["secret_access_key"]
AWS_REGION = graphite_config["aws_region"]
BUCKET_NAME = graphite_config["bucket_name"]
S3_URL = graphite_config["s3_url"]

S3Conn = S3Connection(ACCESS_KEY, SECRET_ACCESS_KEY, host=AWS_REGION)
S3Bucket = S3Conn.get_bucket(BUCKET_NAME)

# update this rzp keys

RZP_KEY = graphite_config["rzp_key"]
RZP_AUTH_KEY = graphite_config["rzp_auth_key"]


# upload file to s3 return url.
class Upload(Resource):

    def post(self):
        global S3_URL, S3Bucket
        file = request.files.get('file')

        file_path_s3 = os.path.join(str(randint(1, 1000000)), 'image.jpg')
        img_key = S3Bucket.new_key(file_path_s3)
        img_key.set_metadata('Content-Type', 'image/png')
        img_key.set_contents_from_file(file)
        img_key.set_acl('public-read')
        image_url = S3_URL + file_path_s3
        return {'message': {'image_url': image_url, 'status': 200}}


class CreateOrder(Resource):

    def post(self):
        order_db = g.dbclient['orders']

        user_id = ObjectId(request.json['user_id'])
        created_at = datetime.datetime.now()
        marked_price = request.json['marked_price']
        discount = request.json['discount']
        selling_price = marked_price - discount
        order_status = 'created'
        payment_status = 'pending'
        required_at = request.json.get('required_at')
        image_url = request.json.get('file_path')

        order = {
            'user': user_id,
            'created_at': created_at,
            'marked_price': marked_price,
            'discount': discount,
            'selling_price': selling_price,
            'order_status': order_status,
            'payment_status': payment_status,
            'required_at': required_at,
            'image_url': image_url
        }

        order_id = order_db.insert_one(order).inserted_id

        if not order_id:
            abort(400, 'order not created')

        return {'message': {'msg': 'order successfully created', 'status': 200}}


class Payment(Resource):

    def post(self):
        global RZP_KEY, RZP_AUTH_KEY
        order_db = g.dbclient['orders']
        order_id = ObjectId(request.json['order_id'])

        import razorpay

        client = razorpay.Client(auth=(RZP_KEY, RZP_AUTH_KEY))

        payment_id = request.json['payment_id']

        payment_amount = request.json['payment_amount'] * 100

        capture_request = client.payment.capture(payment_id, payment_amount)

        capture_response = capture_request.json()
        if not capture_response.__contains__('status'):
            payment_status = 'authorized'
        else:
            payment_status = 'complete'
        order_status = 'processing'

        order = order_db.update_one({'_id': order_id},
                                    {'$set': {'payment_status': payment_status, 'order_status': order_status}})
        if not order.modified_count:
            abort(400, 'order not updated')
        return {'message': {'msg': 'order payment completed', 'status': 200}}


class CancelOrder(Resource):

    def post(self):
        order_db = g.dbclient['orders']
        order_id = ObjectId(request.json['order_id'])
        user_id = ObjectId(request.json['user_id'])
        order_status = "cancelled"

        order = order_db.update_one({'_id': order_id, 'user': user_id}, {'$set': {'order_status': order_status}})

        if not order.modified_count:
            abort(400, 'order not updated')

        return {'message': {'msg': 'order cancelled successfully', 'status': 200}}


class ShowOrders(Resource):

    def get(self):
        order_db = g.dbclient['orders']
        user_db = g.dbclient['users']
        user_id = ObjectId(request.args.get('user_id'))
        user = user_db.find({'_id': user_id})
        if not user:
            abort(400, 'user id not found')
        else:
            user = user[0]
        if user["user_type"] == 'vendor':
            try:
                orders = order_db.find()
            except Exception as e:
                return {'message': {'orders': [], 'status': 200}}
            return {'message': {'orders': JSONEncoder().encode(orders), 'status': 200}}
        elif user["user_type"] == 'customer':
            try:
                orders = order_db.find({'user': user_id})
                if not orders.count():
                    orders = []
            except Exception as e:
                return {'message': {'orders': [], 'status': 200}}
            return {'message': {'orders': JSONEncoder().encode(orders), 'status': 200}}
        abort(400, 'no user type found')


class ShowOrder(Resource):

    def get(self):
        order_db = g.dbclient['orders']
        order_id = ObjectId(request.args.get('order_id'))
        order = order_db.find({'_id': order_id})
        if not order.count():
            return {'message': {'orders': [], 'status': 200}}
        order = order[0]
        return {'message': {'order': JSONEncoder().encode(order), 'status': 200}}
