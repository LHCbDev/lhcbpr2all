'''
Common functions to deal with the configuration files.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import re

def loadFromOldXML(source, slot):
    '''
    Read an old-style XML configuration and generate the corresponding
    dictionary in the new-style configuration.

    @param source: XML path, file object, URL
    @param slot: name of the slot to extract
    '''
    from xml.etree.ElementTree import parse
    doc = parse(source)

    def fixPlaceHolders(s):
        s = s.replace('%DAY%', '${TODAY}')
        s = s.replace('%YESTERDAY%', '${YESTERDAY}')
        s = s.replace('%PLATFORM%', '${CMTCONFIG}')
        return s

    data = {'slot': slot,
            'env': []}
    try:
        slotEl = (el for el in doc.findall('slot')
                  if el.attrib.get('name') == slot).next()

        cmtProjPath = ':'.join([fixPlaceHolders(el.attrib['value'])
                                for el in slotEl.findall('cmtprojectpath/path')])
        if cmtProjPath:
            data['env'].append('CMTPROJECTPATH=' + cmtProjPath)

        el = slotEl.find('cmtextratags')
        if el is not None:
            data['env'].append('CMTEXTRATAGS=' + el.attrib['value'])

        el = slotEl.find('waitfor')
        if el is not None:
            path = fixPlaceHolders(el.attrib['flag'])
            data['preconditions'] = [{"name": "waitForFile",
                                      "args": {"path": path}}]

        data['default_platforms'] = [p.attrib['name']
                                     for p in slotEl.findall('platforms/platform')
                                     if 'name' in p.attrib]

        allProjs = []
        for proj in slotEl.findall('projects/project'):
            name = proj.attrib['name']
            version = proj.attrib['tag'].split('_', 1)[1]
            overrides = {}
            for el in proj.findall('addon') + proj.findall('change'):
                overrides[el.attrib['package']] = el.attrib['value']
            # since dependencies are declared only to override versions, but the
            # new config needs them for the ordering, we fake dependencies on
            # all the projects encountered so far
            dependencies = [p['name'] for p in allProjs]
            # check if we have dep overrides
            for el in proj.findall('dependence'):
                depName = el.attrib['project']
                if depName not in dependencies:
                    dependencies.append(depName)
                    depVer = el.attrib['tag']
                    if depVer == 'LCGCMT-preview':
                        depVer = 'preview'
                    else:
                        depVer = depVer.split('_', 1)[1]
                    allProjs.append({'name': depName,
                                     'version': depVer,
                                     'overrides': {},
                                     'dependencies': [],
                                     'checkout': 'noCheckout'})

            projData = {'name': name,
                        'version': version,
                        'overrides': overrides,
                        'dependencies': dependencies}
            if proj.attrib.get('disabled', 'false').lower() != 'false':
                projData['checkout'] = 'noCheckout'

            allProjs.append(projData)

        data['projects'] = allProjs

        # we assume that all slots from old config use CMT
        data['USE_CMT'] = True

        def el2re(el):
            '''Regex string for ignored warning or error.'''
            v = el.attrib['value']
            if el.attrib.get('type', 'string') == 'regex':
                return v
            else:
                return re.escape(v)
        data['error_exceptions'] = map(el2re, doc.findall('general/ignore/error'))
        data['warning_exceptions'] = map(el2re, doc.findall('general/ignore/warning'))

        return data
    except StopIteration:
        raise RuntimeError('cannot find slot {0}'.format(slot))


def load(path):
    '''
    Load the configuration from a file.

    By default, the file is assumed to be a JSON file, unless it ends with
    '#<slot-name>', in which case the XML parsing is used.
    '''
    try:
        source, slot = path.rsplit('#', 1)
        return loadFromOldXML(source, slot)
    except ValueError:
        import json
        return json.load(open(path, 'rb'))

def save(dest, config):
    '''
    Helper function to dump the current configuration to a file.
    '''
    import json
    f = open(dest, 'wb')
    json.dump(config, f, sort_keys=True, indent=2, separators=(',', ': '))
    f.close()
