import datetime

def overlap(a,b):
    """Calculates the overlap present in two seperate time intervals"""
    return max(min(a[1], b[1]) - max(a[0],b[0]), datetime.timedelta(0))

def zephyrDisplay(stats, um = None):
    """Takes a table of stats and displays it in a zephyr-friendly pretty way."""
    usermetrics = stats.keys() if um == None else set(str(m) for m in um) & stats.viewkeys()
    return '\n'.join((i + ": ").rjust(15) + str(stats[i]) for i in usermetrics)
