FROM nginx:1.9.5

ADD backend-angular/index.html /usr/share/nginx/html/index.html
ADD backend-angular/app /usr/share/nginx/html/app
ADD backend-angular/vendor /usr/share/nginx/html/vendor
ADD nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf

WORKDIR /usr/share/nginx/html
