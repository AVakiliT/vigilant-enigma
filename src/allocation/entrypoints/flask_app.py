from datetime import datetime

from flask import request, jsonify, Flask
from sqlalchemy import create_engine

import allocation.domain.commands
import bootstrap
from allocation import config, views
from allocation.adapters import orm
from allocation.service_layer import messagebus
from allocation.service_layer import unit_of_work
from allocation.service_layer.handlers import InvalidSku

app = Flask(__name__)
engine = create_engine(config.get_postgres_uri(), echo=True)
bus = bootstrap.bootstrap()


# get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))


@app.route("/add_batch", methods=['POST'])
def batch_add_endpoint():
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    bus.handle(allocation.domain.commands.CreateBatch(
        request.json['ref'],
        request.json['sku'],
        request.json['qty'],
        eta, )
    )
    return 'OK', 201


@app.route("/allocate", methods=['POST'])
def batch_allocate_endpoint():
    try:
        batch_ref = bus.handle(allocation.domain.commands.Allocate(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty']))[0]
    except InvalidSku as e:
        return jsonify({'message': str(e)}), 400
    return jsonify({'batch_ref': batch_ref}), 201

@app.route("/deallocate", methods=['POST'])
def batch_deallocate_endpoint():
    try:
        batch_ref = bus.handle(allocation.domain.commands.DeAllocate(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty']))[0]
    except InvalidSku as e:
        return jsonify({'message': str(e)}), 400
    return jsonify({'batch_ref': batch_ref}), 202


@app.route("/allocations/<string:orderid>", methods=["GET"])
def allocations_view_endpoint(orderid):
    result = views.allocations(orderid, bus.uow)
    if not result:
        return "not found", 404
    return jsonify(result), 200


if __name__ == '__main__':
    app.run()
