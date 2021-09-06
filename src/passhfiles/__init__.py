import logging 
import sys
import traceback

def passhfilesExcepthook(errorType, error, tback):
    '''
    Called when an exception is raised and uncaught.
    
    Redirect the exception information to the logger at the critical level.
        
    Args:
        errorType (type): the error type
        error (Error): the error
        tback (traceback): the traceback of the error
    '''

    tback = traceback.extract_tb(tback)

    trace = []                        

    for tb in tback:
        trace.append(' -- '.join([str(t) for t in tb]))
    
    trace.append('{}: {}'.format(errorType.__name__,error))

    trace = '\n'.join(trace)
                
    logging.critical(trace)

sys.excepthook = passhfilesExcepthook
