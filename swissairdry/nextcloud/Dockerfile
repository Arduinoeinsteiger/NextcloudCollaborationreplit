FROM php:8.1-apache

# Systemabhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    libzip-dev \
    zip \
    unzip \
    libpng-dev \
    libicu-dev \
    libxml2-dev \
    && docker-php-ext-install \
    zip \
    gd \
    intl \
    xml \
    mysqli \
    pdo_mysql \
    opcache

# Apache-Konfiguration
RUN a2enmod rewrite headers env dir mime ssl

# Arbeitsverzeichnis
WORKDIR /var/www/html

# Kopieren der App-Dateien
COPY app /var/www/html/custom_apps/swissairdry

# Berechtigungen setzen
RUN chown -R www-data:www-data /var/www/html

# PHP-Konfiguration für Nextcloud optimieren
RUN { \
    echo 'opcache.enable=1'; \
    echo 'opcache.interned_strings_buffer=16'; \
    echo 'opcache.max_accelerated_files=10000'; \
    echo 'opcache.memory_consumption=128'; \
    echo 'opcache.save_comments=1'; \
    echo 'opcache.revalidate_freq=1'; \
    } > /usr/local/etc/php/conf.d/opcache-recommended.ini

RUN { \
    echo 'memory_limit=512M'; \
    echo 'upload_max_filesize=500M'; \
    echo 'post_max_size=500M'; \
    } > /usr/local/etc/php/conf.d/nextcloud.ini

# Apache-VHost-Konfiguration
RUN { \
    echo '<VirtualHost *:80>'; \
    echo '  DocumentRoot /var/www/html'; \
    echo '  ErrorLog ${APACHE_LOG_DIR}/error.log'; \
    echo '  CustomLog ${APACHE_LOG_DIR}/access.log combined'; \
    echo '  <Directory /var/www/html>'; \
    echo '    Options FollowSymLinks'; \
    echo '    AllowOverride All'; \
    echo '    Require all granted'; \
    echo '  </Directory>'; \
    echo '</VirtualHost>'; \
    } > /etc/apache2/sites-available/000-default.conf

# Port freigeben
EXPOSE 80

# Entrypoint-Skript hinzufügen
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2-foreground"]