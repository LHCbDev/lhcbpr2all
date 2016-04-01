FROM python:2.7

RUN mkdir /code
WORKDIR /code
ADD . /code
ADD data /lhcbprdata
VOLUME ["/lhcbprdata"]
EXPOSE 80

CMD ["./scripts/runserver"]
