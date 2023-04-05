from flask import app, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.adapters import orm, repository
from src.domain import model
from src.service_layer import services

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))


@app.route("/batch/allocate", methods=['POST'])
def batch_allocate_endpoint():
    session = get_session()
    repo = repository.SqlRepository(session)
    line = model.OrderLine(
        request.json['orderid'],
        request.json['sku'],
        request.json['qty'],
    )
    try:
        batch_ref = services.allocate(line, repo, session)
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400
    return jsonify({'batch_ref': batch_ref}), 201