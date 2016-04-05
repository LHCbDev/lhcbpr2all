FROM mazurov/node-nginx:latest

RUN npm install -g bower gulp
RUN echo '{ "allow_root": true }' > /root/.bowerrc
RUN mkdir /app
COPY . /app
WORKDIR /app
RUN ./scripts/bootstrap

ENV FE_PORT 9000
ENV FE_LIVE_PORT 35729

EXPOSE 80 9000 35729
VOLUME /app

CMD ["./scripts/runserver"]
