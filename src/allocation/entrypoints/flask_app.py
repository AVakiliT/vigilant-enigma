from datetime import datetime

from flask import request, jsonify, Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from allocation import config
import allocation.domain.commands
import allocation.service_layer.unit_of_work
from allocation.adapters import orm
from allocation.service_layer import messagebus
from allocation.service_layer.handlers import InvalidSku

app = Flask(__name__)
orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))


@app.route("/batch/add", methods=['POST'])
def batch_add_endpoint():
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    messagebus.handle(allocation.domain.commands.CreateBatch(
        request.json['ref'],
        request.json['sku'],
        request.json['qty'],
        eta,),
        allocation.service_layer.unit_of_work.SqlAlchemyUnitOfWork()
    )
    return 'OK', 201


@app.route("/batch/allocate", methods=['POST'])
def batch_allocate_endpoint():
    try:
        batch_ref = messagebus.handle(allocation.domain.commands.Allocate(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty'])
            , allocation.service_layer.unit_of_work.SqlAlchemyUnitOfWork())[0]
    except InvalidSku as e:
        return jsonify({'message': str(e)}), 400
    return jsonify({'batch_ref': batch_ref}), 201


@app.route("/batch/deallocate", methods=['POST'])
def batch_deallocate_endpoint():
    try:
        batch_ref = messagebus.handle(allocation.domain.commands.DeAllocate(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty']),
            allocation.service_layer.unit_of_work.SqlAlchemyUnitOfWork())[0]
    except InvalidSku as e:
        return jsonify({'message': str(e)}), 400
    return jsonify({'batch_ref': batch_ref}), 202


app.run()
