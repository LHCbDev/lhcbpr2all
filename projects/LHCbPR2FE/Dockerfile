FROM mazurov/node-nginx-base:latest

RUN npm install -g bower gulp
RUN echo '{ "allow_root": true }' > /root/.bowerrc
RUN mkdir /app /html
COPY . /app
WORKDIR /app

ENV FE_DIST_DIR /html
ENV FE_URL_API /api
ENV FE_URL_ROOT /root
ENV FE_PORT 9000
ENV FE_LIVE_PORT 35729

RUN sh -x ./scripts/bootstrap && \
    rm -rf /usr/share/nginx/www && \
    ln -s  /html /usr/share/nginx/www

EXPOSE 80 9000 35729
VOLUME /app

CMD ["./scripts/runserver"]
