from flask import Flask
from flask import g
from flask import got_request_exception
from flask import request
from flask_restful import reqparse, Api, Resource
from flask_mail import Mail, Message
from flask_cors import CORS
import json

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

dbclient = MongoClient('localhost', 27017)['graphite']

STRING_CONSTANTS = {}
STRING_CONSTANTS['NEW_PASSWORD_SUBJECT'] = 'New Password Generated'
STRING_CONSTANTS['NEW_PASSWORD_BODY'] = 'Your new password has been successfully generated. Please update your ' \
                                        'password after logging in. Your system generated password is: '
STRING_CONSTANTS['ORDER_CREATION_SUBJECT'] = 'Order Successfully Created'
STRING_CONSTANTS['ORDER_CREATION_BODY'] = 'Your order has been successfully created. Current status of your order is: '

class Logger(object):
    def __init__(self, name, path, debug_flag, console_log, rotate_flag=False):

        # Read for detailed info:
        # https://docs.python.org/2/howto/logging.html
        level_def = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL}

        level = level_def.get(debug_flag,logging.NOTSET)

        logging.basicConfig(level=level)
        logger = logging.getLogger(name)
        if rotate_flag:
            hdlr = TimedRotatingFileHandler(path, when='H', interval=1, backupCount=168) ##log rotation for 1 (H)our and backing up max of 24*7 (=168) files.
            hdlr.suffix = "%Y%m%dT%H"
        else:
            hdlr = logging.FileHandler(path)
        formatter = logging.Formatter(u'%(asctime)s|%(process)d|%(threadName)s|%(levelname)s|%(filename)s|%(funcName)s|%(lineno)d|%(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

        if console_log:
            logger.propagate = True
        else:
            logger.propagate = False

        self.logger = logger

    def get_logger(self):
        return self.logger
loggers = {}
def get_logger(file_name=None, log_name='default', console_log=False, mode='info', rotate_flag=True):
    global loggers
    if log_name not in loggers:
        assert file_name is not None
        loggers[log_name] = (
            Logger(
                log_name,
                os.path.join('../logs/', file_name),
                mode,
                console_log,
                rotate_flag=rotate_flag
            )
            .get_logger()
        )
    return loggers[log_name]


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