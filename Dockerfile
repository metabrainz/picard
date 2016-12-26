FROM python:2.7.12
RUN apt-get update && apt-get install -y build-essential \
										python-dev \
										gettext \
										qt4-default \
										python-qt4 \
										libdiscid0 \
										libdiscid-dev \
										python-mutagen
RUN mkdir -p /build/
ADD . /build/
WORKDIR /build/
ENV PYTHONPATH /usr/lib/python2.7/dist-packages
RUN python setup.py build_ext -i										
RUN python setup.py build_locales -i										
CMD python setup.py test
