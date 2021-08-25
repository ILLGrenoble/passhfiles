import collections
import logging

import yaml

PREFERENCES = collections.OrderedDict()
PREFERENCES['editor'] = ''

def setPreferences(preferences):
    """Set the preferences.
    """

    PREFERENCES.update(preferences)

def loadPreferences(preferencesFile):
    """Load the prferences from a preference (YAML) file.

    Args:
        preferencesFile (str): the path to the preferences file
    """

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
    """Save the preferences to a preference (YAML) file.

    Args:
        preferencesFile (str): the path to the preferences file
    """

    try:
        with open(preferencesFile,'w') as fout:
            yaml.dump(PREFERENCES,fout)
    except Exception as e:
        logging.error(str(e))
        return
    else:
        logging.info('Preferences saved to {}'.format(preferencesFile))