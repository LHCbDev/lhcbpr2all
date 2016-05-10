FROM mazurov/debian-cern-sso

RUN cd /etc/shibboleth/ \
    && shib-keygen -f
COPY docker/apache2.conf /etc/apache2/apache2.conf    
EXPOSE 80 443
