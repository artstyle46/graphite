from flask import Flask
from flask import g
from flask import got_request_exception
from flask import request
from flask_restful import reqparse, Api, Resource
from flask_mail import Mail, Message
from flask_cors import CORS
import json, os

from os.path import expanduser
home = expanduser("~")

graphite_config = json.load(open(os.path.join(home, ".graphite.json")))

app = Flask(__name__)
mail = Mail(app)
app.config['MAIL_SERVER']='smtp.zoho.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = graphite_config['email']
app.config['MAIL_PASSWORD'] = graphite_config['password']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
CORS(app)

mail = Mail(app)
api = Api(app)


import os
import logging
from logging.handlers import TimedRotatingFileHandler

from pymongo import MongoClient
from user import *
from orders import *
from coupon import *

dbclient = MongoClient('localhost', 27017)['graphite']

STRING_CONSTANTS = {}
STRING_CONSTANTS['NEW_PASSWORD_SUBJECT'] = 'New Password Generated'
STRING_CONSTANTS['NEW_PASSWORD_BODY'] = 'Your new password has been successfully generated. Please update your ' \
                                        'password after logging in. Your system generated password is: '
STRING_CONSTANTS['ORDER_CREATION_SUBJECT'] = 'Order Successfully Created'
STRING_CONSTANTS['ORDER_CREATION_BODY'] = 'Your order has been successfully created. Current status of your order is: '

@app.before_request
def set_start_time():
    global dbclient, mail, STRING_CONSTANTS, graphite_config
    g.dbclient = dbclient
    g.mail = mail
    g.string_constants = STRING_CONSTANTS
    g.graphite_config = graphite_config

def setup_app():
    api = Api(app)

    #setup logging

    api.add_resource(Login, '/api/login', strict_slashes=False)
    api.add_resource(Register, '/api/signup', strict_slashes=False)
    api.add_resource(VendorRegister, '/api/vendor', strict_slashes=False)
    api.add_resource(UpdatePassword, '/api/update', strict_slashes=False)
    api.add_resource(Upload, '/api/upload/image', strict_slashes=False)
    api.add_resource(CreateOrder, '/api/order/create', strict_slashes=False)
    api.add_resource(Payment, '/api/order/payment', strict_slashes=False)
    api.add_resource(UpdateOrderStatus, '/api/order/update', strict_slashes=False)
    api.add_resource(ShowOrders, '/api/order/show', strict_slashes=False)
    api.add_resource(ShowOrder, '/api/order/show/id', strict_slashes=False)
    api.add_resource(NewPassword, '/api/mail/password', strict_slashes=False)
    api.add_resource(SendOrderCreationMail, '/api/mail/<email>/<order_status>', strict_slashes=False)
    api.add_resource(createCoupon, '/api/coupon/create', strict_slashes=False)
    api.add_resource(editCoupon, '/api/coupon/edit', strict_slashes=False)
    api.add_resource(getCouponDiscount, '/api/coupon/get', strict_slashes=False)
    api.add_resource(showAllCoupons, '/api/coupon/show', strict_slashes=False)