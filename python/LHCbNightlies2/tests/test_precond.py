import json

from _utils import processFile

# Uncomment to disable the tests.
#__test__ = False

from .. import SlotPreconditions

def test_parseConfigFile():
    'SlotPreconditions.parseConfigFile()'
    expected = [{"name": "waitForFile",
                 "args": {"path": "path/to/file"}}]

    found = processFile(json.dumps({'preconditions': expected}),
                        SlotPreconditions.parseConfigFile)
    assert found == expected

    found = processFile(json.dumps({}),
                        SlotPreconditions.parseConfigFile)
    assert found == []

