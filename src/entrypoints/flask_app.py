from datetime import datetime

from flask import request, jsonify, Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import src.service_layer.unit_of_work
from src.adapters import orm, repository
from src.domain import model
from src.service_layer import services

app = Flask(__name__)
orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))


@app.route("/batch/add", methods=['POST'])
def batch_add_endpoint():
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    services.add_batch(
        request.json['ref'],
        request.json['sku'],
        request.json['qty'],
        eta,
        src.service_layer.unit_of_work.SqlUnitOfWork()
    )
    return 'OK', 201


@app.route("/batch/allocate", methods=['POST'])
def batch_allocate_endpoint():
    try:
        batch_ref = services.allocate(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty']
            , src.service_layer.unit_of_work.SqlUnitOfWork())
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400
    return jsonify({'batch_ref': batch_ref}), 201


@app.route("/batch/deallocate", methods=['POST'])
def batch_deallocate_endpoint():
    try:
        batch_ref = services.deallocate(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty'],
            src.service_layer.unit_of_work.SqlUnitOfWork())
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400
    return jsonify({'batch_ref': batch_ref}), 202


app.run()
