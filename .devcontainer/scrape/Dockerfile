FROM python:3.8

ENV PYTHONUNBUFFERED 1
ENV DISPLAY=:99

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive
RUN apt-get -y install --no-install-recommends chromium chromium-driver

COPY .devcontainer/scrape/requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
   && rm -rf /tmp/pip-tmp

WORKDIR /workspace

CMD ["python", "app/scrape.py"]