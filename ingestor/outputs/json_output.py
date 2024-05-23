import json


def dump_to_json(file_name, data):
    with open(file_name, 'w') as outfile:
        json.dump(data, outfile, indent=4)
