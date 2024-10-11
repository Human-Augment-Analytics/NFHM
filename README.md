# Project Name

The Natural Florida History Museum HAAG project. A ML-backed search engine of ecological data.

![BioCosmos Image Search of lepidoptera iridescence](https://github.com/user-attachments/assets/4859901d-c0da-4f17-9596-7b3d899f5493)

## Table of Contents

- [Local Setup](#local-setup)
  - [Super Quick Start](#super-quick-start)
  - [Less Quick Start](#less-quick-start)
  - [Least Quick Start](#least-quick-start)
- [Seeding Mongo with Raw Data](#seeding-mongo-with-raw-data)
  - [Seeding Mongo with a sample of iDigBio data](#seeding-mongo-with-a-sample-of-idigbio-data)
  - [Seeding Mongo with a sample of GBIF data](#seeding-mongo-with-a-sample-of-gbif-data)
- [Generate Embeddings](#generate-embeddings)

- [Jupyter Notebooks](#jupyter-notebooks)
- [Accessing the Mongo Database](#accessing-the-mongo-database)
- [Accessing the Postgres Database](#accessing-the-postgres-database)
- [Accessing the Mongo Database](#accessing-the-mongo-database)
- [Database Versioning](#database-versioning)
- [Running and tagging experiments](#running-and-tagging-experiments)
- [Accessing Redis](#accessing-redis)
- [Useful Commands](#useful-commands)
  - [Sharing Data](#sharing-data)

## Local Setup

Docker is a prerequisite.

1. Download project: `git clone git@github.com:BioCosmos-AI/BioCosmos.git biocosmos`

### Super Quick Start

1. Open and run project in dev container with [VSCode](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Set up postgres db with initital data: `bin/import_vector_db`
3. Run the backend API (from within the dev container): `bin/dev`
4. Navigate to http://localhost:3000 in your browser

### Less Quick Start

If the Super Quick Start above doesn't work (for example, you're not using a mac), then the following steps capture the essential idea. Modify as necessary for your local computing environment.

1. Open and run project in dev container with [VSCode](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Download the sample vector database:
   - (With Mac's `unzip`): `curl "https://drive.usercontent.google.com/download?id={17QGJ3o7rx88A51KjUije6RX_j4kV0WXr}&confirm=xxx" -o tmp.pgsql.zip && unzip tmp.pgsql.zip`
3. Copy that file to the postgres docker container
   - `docker ps | grep 'nfhm' | grep 'postgres'` to get container name
   - `docker cp vector_embedder_data_only.pgsql nfhm_devcontainer-postgres-1:/tmp/import.pgsql` (Replace `nfhm_devcontainer-postgres-1` and `vector_embedder_data_only.pgsql` with container and filename, respectively, as appropriate.)
4. Run import.
   - `docker exec -it nfhm_devcontainer-postgres-1 bash`
   - `psql -U postgres -d nfhm -f /tmp/import.pgsq`
5. From a _new_ terminal tab in the dev container, run `bin/dev`
6. Navigate to http://localhost:3000 in your browser

### Least Quick Start

For optimal portability, this app uses [Dev Containers](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers) to configure and manage the development environment. This means any developer with Docker installed and an appropriate IDE (e.g., [VSCode](https://code.visualstudio.com/docs/devcontainers/containers), [GitHub Codespaces](https://docs.github.com/en/codespaces/overview), a [JetBrains IDE](https://www.jetbrains.com/help/idea/connect-to-devcontainer.html) if you like debugging) or the [Dev Container CLI](https://github.com/devcontainers/cli) should be able to get this project running locally in just a few steps.

To run locally:

1.  Open the repository in a devcontainer. Here's an example with VSCode using the [VSCode Dev Container extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers). From the command palette (CMD+P on MacBooks), type `Dev Containers: Reopen in Container`:
    ![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/ba3aec85-a5f2-42a3-bf87-2d1f423305eb)

2.  (SUBJECT TO CHANGE): run `bin/dev` to start the python backend.
3.  Visit `http://localhost:8000/`
4.  (SUBJECT TO CHANGE) Here is a mock screenshot of how you can expect the website to look:
5.  Next you'll need to import data.
    - [Import the raw data into Mongo](#seeding-mongo-with-raw-data)
    - [Running the vector embedder job]()

## Jupyter Notebooks

This project's dev container runs a docker image of jupyter notebooks at http://localhost:8888. The `/work/` (fullpath: `/home/jovyan/work/`) directory of this container is mounted to this repository on your local filesystem at `./NFHM/jupyter-workpad` so you can check in your notebooks to version control.

Alternatively, you can use a local installation of Jupyter if you prefer. Regardless, by convention, check your work into the `./jupyter-workpad` subdirectory.

## Seeding Mongo with Raw Data

We use [Mongo](#accessing-the-mongo-database) to house the raw data we import from iDigBio, GBIF, and any other external sources. We use [Redis](#accessing-redis) as our queueing backend. To seed your local environment with a sample of data to work with, you'll need to first follow the instructions above for [local setup](#local-setup).

### Seeding Mongo with a sample of iDigBio data:

1. From within a dev container: `$ bin/ingest_idigbio`
2. Navigate in a browser to the [Redis](#accessing-redis) server via Redis Insight at http://localhost:8001, or connect to port `6379` via your preferred Redis client.
3. Decide what sample of data you want to [query from iDigBio](https://github.com/iDigBio/idigbio-search-api/wiki/Additional-Examples#q-how-do-i-search-for-nsf_tcn-in-dwcdynamicproperties). For this example, we'll limit ourselves to records of the order `lepidoptera` (butterflies and related winged insects) with associated image data from the Yale Peabody Museum.
4. We'll `LPUSH` that query onto the `idigbio` queue from the Redis Insight workbench:

   ```
   LPUSH idigbio '{"search_dict":{"order":"lepidoptera","hasImage":true,"data.dwc:institutionCode":"YPM"},"import_all":true}'
   ```

   - `search_dict` is the verbatim query passed to the iDigBio API. Consult the [wiki](https://www.idigbio.org/wiki/index.php/Wiki_Home) and [the github wiki](https://github.com/iDigBio/idigbio-search-api/wiki) for search options.
   - `import_all` is a optional param (default: False) that'll iteratre through all pages of results and import the raw data into Mongo. Otherwise, only the first page of results are fetched. Consequently, please be mindful when setting this param as there are _a lot_ (~200 GB, not including media data) of records in iDigBio.
   - ![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/0bbc0cc7-fff1-4b1a-927f-1fe9f153de06)

5. Navigate to Mongo Express (or use your preferred Mongo client) at http://localhost:8081 and navigate to the `idigbio` collection inside the `NFHM` database to see the imported data.
   ![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/c02e6279-92fa-4dca-81d4-21deb53dbf2c)

### Seeding Mongo with a sample of GBIF data:

The basic process of seeding Mongo with raw GBIF data is essentially the same as with iDigBio. However, you'll need make sure you have the GBIF worker up-and-running in your dev container with the correct environment inputs:

- `$ bin/ingest_gbif`
- From the workbench of Redis Insight, pass a simple search string to the `gbif` queue:
  - `LPUSH gbif "puma concolor"`

## Generate Embeddings

Once we've imported raw-form data into Mongo, we'll want to generate vector embeddings for the data and store them to Postgres. This is where the web api serves query results from.

The process is very similar to importing data into Mongo. Again, if you've just started up the dev container, make sure to open a new terminal tab (assuming you're using VSCode) so that conda will init. Similarly, we can run a script to activate the embedder, or run it ourselves:

`$ bin/ingest_embedder`

As this ingestor is running, it is waiting a signal from the Redis queue to begin the embedding process. This will work very similarly to the `gbif` and `idigbio` queues above:
From the workbench of Redis Insight, pass a simple search string to the `embedder` queue:

`LPUSH embedder '{}'`

## Accessing the Postgres Database

Postgres serves as the primary backend database for vector/embedding storage, as well as other backend storage critical to running and serving the app.

You can directly access the Postgres database from your local machine by connecting to port `5432` on `localhost` using username `postgres` and password `postgres`. For example, with [Postico](https://eggerapps.at/postico2/), you would:
![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/4310ab04-ea99-4a3a-8759-07800991818d)

## Accessing the Mongo Database

This project uses Mongo to store raw data from iDigBio, GBIF, etc. This allows us to more readily run experiments with re-indexing, re-vectorizing/embedding, etc. without having to reach out across the internet to the canonical data sources everytime we want to re-access the same raw data.

Once you have your development environment running, you can access MongoDB locally by going to http://localhost:8081/. Alternatively, you can connect to port 27018 on localhost with your preferred Mongo client (e.g., `mongosh`). The local database is, unoriginally, named `NFHM`.

![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/7c3354ba-8a6f-4ab2-8791-2b1c28e21729)

## Accessing Redis

Redis -- as of this writing -- is used as a queueing backend during data ingestion and processing. In the future, we may use redis for other things, too.

To access the local Redis server with [Redis Insight](https://redis.io/insight/) during development, navigate to http://localhost:8001/. You should also be able to directly connect your preferred Redis client (e.g., `redis-cli`) by directly connecting to your local host at the default Redis port `6379`.

![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/cf36476e-6b8e-4832-afa4-0bead6da7214)

## Useful Commands

### Sharing Data

We expect to do a lot experiments that vary the content of the DB. Consequently, it's imperative to be able to share our _exact_ data with each other. This way we can avoid repeating ourselves with the lengthy process of importing data from external sources and generating embeddings. You can use `pg_dump` to do so:

`docker exec  nfhm_devcontainer-postgres-1 bash -c "pg_dump -U postgres nfhm" > <FILE_NAME>.pgsql`

And then zip it up and send.
