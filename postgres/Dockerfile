FROM pgvector/pgvector:pg16

COPY ./postgres/init.sh /docker-entrypoint-initdb.d/init.sh

RUN apt -y update && \
    apt -y install postgresql-16-pgvector && \
    apt -y install postgis && \
    chmod +x /docker-entrypoint-initdb.d/init.sh    
