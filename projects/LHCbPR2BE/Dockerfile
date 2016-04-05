FROM python:2.7

RUN mkdir /app
WORKDIR /app
ADD . /app
RUN ./scripts/bootstrap
ADD data /lhcbprdata

VOLUME /lhcbprdata

CMD ["./scripts/runserver"]
