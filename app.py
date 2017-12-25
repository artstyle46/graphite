from flask import Flask
from flask import g
from flask import got_request_exception
from flask import request
from flask_restful import reqparse, Api, Resource

app = Flask(__name__)
api = Api(app)

import os
import logging
from logging.handlers import TimedRotatingFileHandler

from pymongo import MongoClient
from user import Login, Register, UpdatePassword, VendorRegister
from orders import *

dbclient = MongoClient('localhost', 27017)['graphite']

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
    global dbclient, access_logger
    g.dbclient = dbclient
    g.logger = access_logger


def setup_app():
    global access_logger
    api = Api(app)

    #setup logging
    log_name = 'app'
    access_logger = get_logger(file_name='%s_access.log' % log_name, log_name='access')

    api.add_resource(Login, '/api/login', strict_slashes=False)
    api.add_resource(Register, '/api/signup', strict_slashes=False)
    api.add_resource(VendorRegister, '/api/vendor', strict_slashes=False)
    api.add_resource(UpdatePassword, '/api/update', strict_slashes=False)
    api.add_resource(Upload, '/api/upload/image', strict_slashes=False)
    api.add_resource(CreateOrder, '/api/order/create', strict_slashes=False)
    api.add_resource(Payment, '/api/order/payment', strict_slashes=False)
    api.add_resource(CancelOrder, '/api/order/cancel', strict_slashes=False)
    api.add_resource(ShowOrders, '/api/order/show', strict_slashes=False)
    api.add_resource(ShowOrders, '/api/order/show/id', strict_slashes=False)