from allocation.service_layer import unit_of_work


def allocations(orderid: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = list(uow.session.execute(
            f"""
            SELECT b.sku, b.reference
               FROM allocations as a
               JOIN order_lines AS o ON o.id = a.orderline_id
               JOIN batches AS b ON b.id = a.batch_id
               WHERE o.orderid = :orderid
            """,
            dict(
                orderid=orderid
            )))
    return [{'sku': sku, 'batchref': batchref} for sku, batchref in results]
