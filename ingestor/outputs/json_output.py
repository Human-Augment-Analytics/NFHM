import json


def dump_to_json(data, file_name, **kwargs):
    with open(file_name, 'w') as outfile:
        json.dump(data, outfile, indent=4)
