import datetime

from flask import request, abort
from flask import g

import requests

from flask_restful import Resource
from bson.json_util import ObjectId
from random import randint
import os
from boto.s3.key import Key
from boto.s3.connection import S3Connection

S3_URL = 'https://s3-ap-southeast-1.amazonaws.com/'
ACCESS_KEY = ''
SECRET_ACCESS_KEY = ''
BUCKET_NAME = 'graphite-images'

S3Conn = S3Connection(ACCESS_KEY, SECRET_ACCESS_KEY)
S3Bucket = S3Conn.get_bucket(BUCKET_NAME)

# update this rzp keys

RAZORPAY = {'key': ''}
RZP_KEY = ""
RZP_AUTH_KEY = ""


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

        url = "https://api.razorpay.com/v1/payments/" + request.json['payment_key'] + "/capture"
        data = {
            "amount": int(request.json['fare'] * 100)
        }
        capture_request = requests.post(url, data=data,
                                        auth=(RZP_KEY, RZP_AUTH_KEY))
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
        if user.user_type == 'vendor':
            orders = order_db.find()
            return {'message': {'orders': orders, 'status': 200}}
        elif user.user_type == 'customer':
            orders = order_db.find({'user': user_id})
            return {'message': {'orders': orders, 'status': 200}}
        abort(400, 'no user type found')


class ShowOrder(Resource):

    def get(self):
        order_db = g.dbclient['orders']
        order_id = ObjectId(request.args.get('order_id'))
        order = order_db.find({'_id': order_id})
        if not order:
            abort(400, 'order id not found')
        else:
            order = order[0]
        return {'message': {'order': order, 'status': 200}}
