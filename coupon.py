import datetime

from flask import request, abort
from flask import g

from user import JSONEncoder
from flask_restful import Resource

class createCoupon(Resource):

    def post(self):
        coupon_db = g.dbclient['coupons']
        coupon_id = request.json['coupon_id']
        coupon_discount = request.json['coupon_discount']
        enabled = True
        created_at = datetime.datetime.now()
        coupon_json = {
            "coupon_id": coupon_id,
            "coupon_discount": int(coupon_discount),
            "enabled": enabled,
            "created_at": created_at
        }
        coupon_id = coupon_db.insert_one(coupon_json).inserted_id

        if not coupon_id:
            abort(400, 'unable to create coupon')
        return {'message': {'msg': 'successfully created coupon', 'status': 400}}


class editCoupon(Resource):

    def post(self):
        coupon_db = g.dbclient['coupons']
        coupon_id = request.json.get('coupon_id')
        if not coupon_id:
            abort(400, 'no coupon id provided to edit')
        new_discount = request.json.get('new_discount', 0)
        update_coupon = False
        update_json = {}
        if new_discount:
            update_json['coupon_discount'] = int(new_discount)
            update_coupon = True
        enabled = request.json.get('enabled', None)
        if enabled is not None:
            update_json['enabled'] = enabled
            update_coupon = True
        update_json['updated_at'] = datetime.datetime.now()
        coupon = coupon_db.find({'coupon_id': coupon_id})
        if not coupon.count():
            abort(400, 'coupon id doesn\'t exist in the db to update')
        if update_coupon:
            updated_coupon = coupon_db.update_one({'coupon_id': coupon_id}, {'$set': update_json})
            if not updated_coupon.modified_count:
                abort(400, 'coupon not updated')
            return {'message': {'msg': 'successfully updated the coupon %s' % coupon_id, 'status': 200}}
        else:
            abort(400, 'nothing to update in coupons')


class getCouponDiscount(Resource):

    def get(self):
        coupon_db = g.dbclient['coupons']
        coupon_id = request.args.get('coupon_id')
        if not coupon_id:
            abort(400, 'no coupon id provided')
        coupon_detail = coupon_db.find({'coupon_id': coupon_id, 'enabled': True})
        if not coupon_detail.count():
            abort(400, 'sorry, coupon doesn\'t exist')
        coupon_detail = coupon_detail[0]
        return {'message': {'msg': 'coupon applied successfully', 'status': 200,
                            'data': {'discount': coupon_detail.get('coupon_discount', 0)}}}
