FROM mazurov/cern-root:latest
LABEL description="ROOT json service"
ENV CODE /app
ENV ROOT_DATA /lhcbprdata

ENV FLASK_PORT 80
ENV FLASK_HOST 0.0.0.0

RUN mkdir $ROOT_DATA
ADD . $CODE
WORKDIR $CODE

RUN pip install -r requirements.txt
COPY data/* $ROOT_DATA/

EXPOSE $FLASK_PORT

CMD ["./scripts/bootstrap"]
