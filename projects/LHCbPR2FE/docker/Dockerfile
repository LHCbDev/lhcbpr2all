FROM nginx:1.9.5

ADD dist/prod /usr/share/nginx/html
ADD nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf

VOLUME ["/etc/nginx/conf.d", "/usr/share/nginx/html"]
EXPOSE 80
WORKDIR /usr/share/nginx/html
