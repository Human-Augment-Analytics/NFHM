# Project Name

The Natural Florida History Museum HAAG project.  A ML-backed search engine of ecological data.


## Table of Contents

- [Local Setup](#local-setup)
- [Seeding Mongo with Raw Data](#seeding-mongo-with-raw-data)
   - [Seeding Mongo with a sample of iDigBio data](#seeding-mongo-with-a-sample-of-idigbio-data)
   - [Seeding Mongo with a sample of GBIF data](#seeding-mongo-with-a-sample-of-gbif-data)
- [Jupyter Notebooks](#jupyter-notebooks)
- [Accessing the Mongo Database](#accessing-the-mongo-database)
- [Accessing the Postgres Database](#accessing-the-postgres-database)
- [Accessing the Mongo Database](#accessing-the-mongo-database)
- [Accessing Redis](#accessing-redis)
- [Contributing](#contributing)
- [License](#license)

## Local Setup

For optimal portability, this app uses [Dev Containers](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers) to configure and manage the development environment. This means any developer with Docker installed and an appropriate IDE (e.g., [VSCode](https://code.visualstudio.com/docs/devcontainers/containers), [GitHub Codespaces](https://docs.github.com/en/codespaces/overview), a [JetBrains IDE](https://www.jetbrains.com/help/idea/connect-to-devcontainer.html) if you like debugging) or the [Dev Container CLI](https://github.com/devcontainers/cli) should be able to get this project running locally in just a few steps.

To run locally:
1)  Open the repository in a devcontainer.  Here's an example with VSCode using the [VSCode Dev Container extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).  From the command palette (CMD+P on MacBooks), type `Dev Containers: Reopen in Container`:
   ![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/ba3aec85-a5f2-42a3-bf87-2d1f423305eb)

  
2) (SUBJECT TO CHANGE): run `$ conda activate backend_api && bin/dev` to start the python backend.
3) Visit `http://localhost:8000/`

## Jupyter Notebooks

This project's dev container runs a docker image of jupyter notebooks at http://localhost:8888.  The `/work/` (fullpath: `/home/jovyan/work/`) directory of this container is mounted to this repository on your local filesystem at `./NFHM/jupyter-workpad` so you can check in your notebooks to version control.

Alternatively, you can use a local installation of Jupyter if you prefer.  Regardless, by convention, check your work into the `./jupyter-workpad` subdirectory.

## Seeding Mongo with Raw Data

We use [Mongo](#accessing-the-mongo-database) to house the raw data we import from iDigBio, GBIF, and any other external sources.  We use [Redis](#accessing-redis) as our queueing backend.  To seed your local environment with a sample of data to work with, you'll need to first follow the instructions above for [local setup](#local-setup).

### Seeding Mongo with a sample of iDigBio data:
1) Activate the ingestor_worker conda environment: `$ conda activate ingestor_worker`
2) Start by spinning up the iDigBio worker.
   - The worker pulls in environment variables to determine which queue to pull from and which worker functions to call.  Consequently, you can either set those variables in `.devcontainer/devcontainer.json` -- which will require a rebuild and restart of the dev container -- or you can pass them in via the command line.  We'll do the latter:
      - (from within the dev container): 
         - `$ SOURCE_QUEUE="idigbio" INPUT="inputs.idigbio_search" python ingestor/ingestor.py`
       ![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/b77126f5-288f-4c55-b2b0-69768903e011)

3) Navigate in a browser to the [Redis](#accessing-redis) server via Redis Insight at http://localhost:8001, or connect to port `6379` via your preferred Redis client.
4) Decide what sample of data you want to [query from iDigBio](https://github.com/iDigBio/idigbio-search-api/wiki/Additional-Examples#q-how-do-i-search-for-nsf_tcn-in-dwcdynamicproperties).  For this example, we'll limit ourselves to records of the order `lepidoptera` (butterflies and related winged insects) with associated image data from the Yale Peabody Museum.
5) We'll `LPUSH` that query onto the `idigbio` queue from the Redis Insight workbench:
   - `LPUSH idigbio '{"search_dict":{"order":"lepidoptera","hasImage":true,"data.dwc:institutionCode":"YPM"},"import_all":true}'`
   -  `search_dict` is the verbatim query passed to the iDigBio API.  Consult the [wiki](https://www.idigbio.org/wiki/index.php/Wiki_Home) and [the github wiki](https://github.com/iDigBio/idigbio-search-api/wiki) for search options.
   - `import_all` is a optional param (default: False) that'll iteratre through all pages of results and import the raw data into Mongo.  Otherwise, only the first page of results are fetched.  Consequently, please be mindful when setting this param as there are _a lot_ (~200 GB, not including media data) of records in iDigBio.
   - ![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/0bbc0cc7-fff1-4b1a-927f-1fe9f153de06)

6) Navigate to Mongo Express (or use your preferred Mongo client) at http://localhost:8081 and navigate to the `idigbio` collection inside the `NFHM` database to see the imported data.
![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/c02e6279-92fa-4dca-81d4-21deb53dbf2c)

### Seeding Mongo with a sample of GBIF data:
The basic process of seeding Mongo with raw GBIF data is essentially the same as with iDigBio.  However, you'll need make sure you have the GBIF worker up-and-running in your dev container with the correct environment inputs:
- `$ SOURCE_QUEUE="gbif" INPUT="inputs.gbif_search" python ingestor/ingestor.py`
- From the workbench of Redis Insight, pass a simple search string to the `gbif` queue:
   - `LPUSH gbif "puma concolor"`

## Accessing the Postgres Database

Postgres serves as the primary backend database for vector/embedding storage, as well as other backend storage critical to running and serving the app.  

You can directly access the Postgres database from your local machine by connecting to port `5432` on `localhost` using username `postgres` and password `postgres`.  For example, with [Postico](https://eggerapps.at/postico2/), you would:
![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/4310ab04-ea99-4a3a-8759-07800991818d)



## Accessing the Mongo Database

This project uses Mongo to store raw data from iDigBio, GBIF, etc.  This allows us to more readily run experiments with re-indexing, re-vectorizing/embedding, etc. without having to reach out across the internet to the canonical data sources everytime we want to re-access the same raw data.

Once you have your development environment running, you can access MongoDB locally by going to http://localhost:8081/.  Alternatively, you can connect to port 27018 on localhost with your preferred Mongo client (e.g., `mongosh`).  The local database is, unoriginally, named `NFHM`.

![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/7c3354ba-8a6f-4ab2-8791-2b1c28e21729)


## Accessing Redis

Redis -- as of this writing -- is used as a queueing backend during data ingestion and processing.  In the future, we may use redis for other things, too.

To access the local Redis server with [Redis Insight](https://redis.io/insight/) during development, navigate to http://localhost:8001/.  You should also be able to directly connect your preferred Redis client (e.g., `redis-cli`) by directly connecting to your local host at the default Redis port `6379`.

![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/cf36476e-6b8e-4832-afa4-0bead6da7214)


## Usage

Instructions on how to use your project and any relevant examples.

## Contributing

Guidelines on how others can contribute to your project.

## License

Information about the license for your project.
