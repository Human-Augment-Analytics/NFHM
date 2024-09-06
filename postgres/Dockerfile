FROM pgvector/pgvector:pg16

# Copy init script
COPY ./postgres/init.sh /docker-entrypoint-initdb.d/init.sh

# Install required packages and Flyway
RUN apt-get update && \
    apt-get install -y \
        postgresql-16-pgvector \
        postgis \
        wget \
        default-jre && \
    chmod +x /docker-entrypoint-initdb.d/init.sh && \
    wget -qO- https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/8.5.13/flyway-commandline-8.5.13-linux-x64.tar.gz | tar xvz && \
    ln -s /flyway-8.5.13/flyway /usr/local/bin && \
    rm -rf /var/lib/apt/lists/*


# Set Flyway configuration
ENV FLYWAY_CONFIG_FILES=/flyway/conf/flyway.conf
COPY ./postgres/flyway/conf/flyway.conf /flyway/conf/

# Copy migration scripts
COPY ./postgres/migrations /flyway/sql

# Set the working directory
WORKDIR /

COPY ./postgres/run-migrations.sh /usr/local/bin/run-migrations.sh
RUN chmod +x /usr/local/bin/run-migrations.sh

# Set the entrypoint
COPY ./postgres/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]

CMD ["postgres"]

