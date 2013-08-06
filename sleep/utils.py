import datetime, pytz, math

def overlap(a,b):
    """Calculates the overlap present in two seperate time intervals"""
    return max(min(a[1], b[1]) - max(a[0],b[0]), datetime.timedelta(0))

def dgsin(degree):
    return math.sin(math.radians(degree))

def julian(date):
    """Takes a Gregorian calendar date and turns into a Julian calender date"""
    a = (14.0 - date.month)//12
    y = date.year + 4800 - a
    m = date.month + 12*a - 3

    return date.day + (153*m + 2)//5 +365*y +y//4 - y//100 + y//400 - 32045

#def sunriseset(date, lat, lon):
#    """Takes a Gregorian calendar date and calculates the sunrise and sunset times"""
#    j = julian(date)
#    n = j - 2451545.0009 - lon/360.0 + 0.5
#    solarNoon = 2451545.0009 + lon/360.0 + n
#    solarMean = (357.5291 + 0.98560028*(solarNoon - 2451545))% 360
#    center = 1.9148*dgsin(solarMean) + 0.02*dgsin(2*solarMean) + 0.0003*dgsin(3*solarMean)
#    eclipticLongitude = (solarMean + 102.9372 + center + 180) % 360
#    jTransit = solarNoon + 0.0053*dgsin(solarMean) - 0.0069*dgsin(2*eclipticLongitude)
#    declination = math.asin(dgsin(eclipticLongitude)*dgsin(23.45))
#    print declination
#    h = (dgsin(-0.83) - dgsin(lat)*math.sin(declination)) / (math.cos(math.radians(lat))*math.cos(declination))
#    print h
#    hourAngle = math.acos(h)
#    jSet = 2451545.0009 + (hourAngle + lon)/360.0 + n + 0.0053*dgsin(solarMean) - 0.0069*dgsin(2*eclipticLongitude)
#    jRise = (2*jTransit - jSet)%1
#    jSet = jSet%1
#    return jSet, jRise
