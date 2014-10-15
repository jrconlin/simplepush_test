FROM debian:jessie
MAINTAINER JR Conlin <jrconlin@mozilla.com>

ADD . /simplepush_test
WORKDIR /simplepush_test

RUN apt-get update; \
	apt-get install --no-install-recommends -y -q python-pip; \
	pip install -r prod-reqs.txt; \
	python setup.py develop

CMD ["python", "run_all.py"]
