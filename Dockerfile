FROM nginx:stable-alpine

RUN apk update && apk upgrade && apk add curl
RUN curl -sLo /usr/local/bin/ep https://github.com/kreuzwerker/envplate/releases/download/v0.0.7/ep-linux && chmod +x /usr/local/bin/ep
RUN mkdir /html

COPY ./docker/nginx /etc/nginx



ENV APP_SERVER_NAME prl-dev

RUN mkdir /etc/ssl/nginx
# RUN openssl genrsa -des3 -out /etc/ssl/nginx/${APP_SERVER_NAME}.key 2048 &&\
#     openssl req -new -key /etc/ssl/nginx/${APP_SERVER_NAME}.key -out /etc/nginx/ssl/nginx/${APP_SERVER_NAME}.csr && \
#     openssl x509 -req -days 365 -in /etc/nginx/ssl/nginx/${APP_SERVER_NAME}.csr -signkey /etc/nginx/ssl/nginx/${APP_SERVER_NAME}.key -out /etc/nginx/ssl/${APP_SERVER_NAME}.crt
RUN openssl req \
    -new \
    -newkey rsa:4096 \
    -days 365 \
    -nodes \
    -x509 \
    -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=www.example.com" \
    -keyout  /etc/ssl/nginx/${APP_SERVER_NAME}.key \
    -out  /etc/ssl/nginx/${APP_SERVER_NAME}.crt

EXPOSE 80 443

CMD ["/usr/local/bin/ep", "-v", "/etc/nginx/sites-enabled/default.conf", "--", "/usr/sbin/nginx", "-g", "daemon off;"]