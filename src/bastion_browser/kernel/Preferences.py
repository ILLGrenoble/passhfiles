import collections
import logging

import yaml

PREFERENCES = collections.OrderedDict()
PREFERENCES['editor'] = ''
PREFERENCES['auto-connect'] = True

def setPreferences(preferences):
    PREFERENCES.update(preferences)

def loadPreferences(preferencesFile):

    try:
        with open(preferencesFile,'r') as fin:
            preferences = yaml.unsafe_load(fin)
    except Exception as e:
        logging.error(str(e))
        return
    else:
        PREFERENCES.update(preferences)
        logging.info('Preferences successfully loaded')
    
def savePreferences(preferencesFile):

    try:
        with open(preferencesFile,'w') as fout:
            yaml.dump(PREFERENCES,fout)
    except Exception as e:
        logging.error(str(e))
        return
    else:
        logging.info('Preferences saved to {}'.format(preferencesFile))
