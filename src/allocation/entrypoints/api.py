from dataclasses import replace
from datetime import datetime

import uvicorn
from fastapi import FastAPI, status, HTTPException
from flask import request, jsonify

from allocation.domain.commands import CreateBatch, Allocate, DeAllocate
import bootstrap
from allocation import views, config
from allocation.service_layer.handlers import InvalidSku

app = FastAPI()
bus = bootstrap.bootstrap()


@app.post("/add_batch", status_code=status.HTTP_201_CREATED)
def batch_add_endpoint(create_batch: CreateBatch):
    bus.handle(create_batch)


@app.post("/allocate", status_code=status.HTTP_201_CREATED)
def batch_allocate_endpoint(allocate: Allocate):
    try:
        bus.handle(allocate)
    except InvalidSku as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/deallocate", status_code=status.HTTP_204_NO_CONTENT)
def batch_deallocate_endpoint(deallocate: DeAllocate):
    try:
        bus.handle(deallocate)
    except InvalidSku as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/allocations/{orderid}")
def allocations_view_endpoint(orderid: str):
    result = views.allocations(orderid, bus.uow)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"orderid {orderid} not found")
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
