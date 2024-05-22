# Project Name

The Natural Florida History Museum HAAG project.  A ML-backed search engine of ecological data.


## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

For optimal portability, this app uses [Dev Containers](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers) to configure and manage the development environment. This means any developer with Docker installed and an appropriate IDE (e.g., [VSCode](https://code.visualstudio.com/docs/devcontainers/containers), [GitHub Codespaces](https://docs.github.com/en/codespaces/overview), a [JetBrains IDE](https://www.jetbrains.com/help/idea/connect-to-devcontainer.html) if you like debugging) or the [Dev Container CLI](https://github.com/devcontainers/cli) should be able to get this project running locally in just a few steps.

To run locally:
1)  Open the repository in a devcontainer.  Here's an example with VSCode using the [VSCode Dev Container extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).  From the command palette (CMD+P on MacBooks), type `Dev Containers: Reopen in Container`:
   ![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/ba3aec85-a5f2-42a3-bf87-2d1f423305eb)

  
2) (SUBJECT TO CHANGE): run `$ bin/dev` to start the python backend.
3) Visit `http://localhost:8000/`

## Accessing the Postgres Database

Postgres serves as the primary backend database for vector/embedding storage, as well as other backend storage critical to running and serving the app.  

You can directly access the Postgres database from your local machine by connecting to port `5432` on `localhost` using username `postgres` and password `postgres`.  For example, with [Postico](https://eggerapps.at/postico2/), you would:
![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/4310ab04-ea99-4a3a-8759-07800991818d)



## Accessing the Mongo Database

This project uses Mongo to store raw data from iDigBio, GBIF, etc.  This allows us to more readily run experiments with re-indexing, re-vectorizing/embedding, etc. without having to reach out across the internet to the canonical data sources everytime we want to re-access the same raw data.

Once you have your development environment running, you can access MongoDB locally by going to http://localhost:8081/.  Alternatively, you can connect to port 27018 on localhost with your preferred Mongo client (e.g., `mongosh`).  The local database is, unoriginally, named `local`.

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
