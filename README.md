# Project Name



## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

To run locally:
- Open as a devcontainer using VSCode (or any other IDE; However, only tested and confirmed to work with VSCode) or the devcontainer CLI
- (SUBJECT TO CHANGE): run bin/dev


## Accessing the Mongo Database

This project uses Mongo to store raw data from iDigBio, GBIF, etc.  This allows us to more readily run experiments with re-indexing, re-vectorizing/embedding, etc. without having to reach out across the internet to the canonical data sources everytime we want to re-access the same raw data.

Once you have your development environment running, you can access MongoDB locally by going to http://localhost:8081/.  Alternatively, you can connect to port 27018 on localhost with your preferred Mongo client (e.g., `mongosh`).  The local database is, unoriginally, named `local`.

![image](https://github.com/Human-Augment-Analytics/NFHM/assets/3391824/7c3354ba-8a6f-4ab2-8791-2b1c28e21729)


## Usage

Instructions on how to use your project and any relevant examples.

## Contributing

Guidelines on how others can contribute to your project.

## License

Information about the license for your project.
