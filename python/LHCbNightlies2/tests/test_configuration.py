import json

from _utils import processFile

# Uncomment to disable the tests.
#__test__ = False

from .. import Configuration

def test_loadJSON():
    'Configuration.load(json_file)'
    expected = {'slot': 'slot-name',
                'projects':[{"name": "Gaudi",
                             "version": "v23r5",
                             "checkout": "specialCheckoutFunction"},
                            {"name": "LHCb",
                             "version": "v32r5",
                             "dependencies": ["Gaudi"]}]}

    found = processFile(json.dumps(expected), Configuration.load)
    assert found == expected
