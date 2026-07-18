FROM python:alpine3.24

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY ./src .
COPY README.md /app/templates

EXPOSE 443

CMD ["python", "envoy_sim.py"]
