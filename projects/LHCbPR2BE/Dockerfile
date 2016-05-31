FROM python:2.7

RUN mkdir /app
WORKDIR /app
ADD . /app

ENV DJANGO_STATIC_ROOT=/html/api/static

RUN ./scripts/bootstrap
ADD data /lhcbprdata

VOLUME ["/lhcbprdata", "/html"]

EXPOSE 80

CMD ["./scripts/runserver"]
