FROM python

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/ .

RUN pip install -e .

COPY tests/ .

WORKDIR src

#ENV FLASK_APP=allocation/entrypoints/flask_app.py
CMD flask --app allocation.entrypoints.flask_app run --host=0.0.0.0 --port=80