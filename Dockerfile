FROM centos:latest
MAINTAINER Darkheaven (darkheaven1983@gmail.com)

RUN yum update -y && yum clean all

RUN yum install -y python python-setuptools gcc python-devel libffi-devel openssl-devel

RUN easy_install pip

RUN pip install ndg-httpsclient alauda prometheus_client

EXPOSE 9104

ADD exporter.py /exporter.py

CMD ["python", "-u", "/exporter.py"]
