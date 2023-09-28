FROM python:3.10

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt

RUN pip install --debug --no-cache-dir --upgrade -r /code/requirements.txt \
    --index-url  https://repos.tech.orange/artifactory/api/pypi/pythonproxy/simple/

COPY . /code

RUN pip install --no-cache-dir .

#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]

# TLS Termination Proxy (load balancer)
 CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
