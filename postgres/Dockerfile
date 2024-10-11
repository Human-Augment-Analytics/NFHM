FROM pgvector/pgvector:pg16

# Install required packages and Java
RUN apt-get update && \
    apt-get install -y \
        postgresql-16-pgvector \
        postgresql-16-postgis-3 \
        wget \
        openjdk-17-jre-headless \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Install Flyway (x64 version)
ENV FLYWAY_VERSION=9.20.0
RUN curl -L -o flyway.tar.gz https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/${FLYWAY_VERSION}/flyway-commandline-${FLYWAY_VERSION}-linux-x64.tar.gz && \
    tar -xzf flyway.tar.gz && \
    rm flyway.tar.gz && \
    ln -s /flyway-${FLYWAY_VERSION}/flyway /usr/local/bin && \
    flyway --version

# Set Flyway configuration
ENV FLYWAY_CONFIG_FILES=/flyway/conf/flyway.conf
COPY ./postgres/flyway/conf/flyway.conf /flyway/conf/

# Copy migration scripts
COPY ./postgres/migrations /flyway/sql

# Set the working directory
WORKDIR /

# Copy the custom entrypoint script
COPY ./postgres/custom-entrypoint.sh /usr/local/bin/custom-entrypoint.sh
RUN chmod +x /usr/local/bin/custom-entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/bin/bash", "/usr/local/bin/custom-entrypoint.sh"]

CMD ["postgres"]
