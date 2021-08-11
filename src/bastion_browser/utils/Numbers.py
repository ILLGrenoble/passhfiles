def sizeOf(num, suffix='B'):
    """Converts a given size to human format.

    Returns:
        sts: the size in human format 
    """
    
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
