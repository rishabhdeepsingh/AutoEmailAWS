import os
from datetime import datetime
from requests import get
from helper import get_all_users, get_eta_days, get_eta_hrs

all_users = get_all_users()


def get_ping_rate(trip):
    if 'pingrate' in trip.keys():
        return int(trip['pingrate'])
    else:
        return 3600000


def get_user_ping_rate(username):
    for user in all_users:
        if user['username'] == username:
            return user['config']['pingrate']
    print("ERR user.config.pingrate not found for user {}".format(username))
    return None


def get_sla(trip):
    """
    :param: Data Object
    :rtype: time in minutes
    """
    try:
        fmt = '%Y-%m-%dT%H:%M:%S.%fz'

        eta_hrs = get_eta_hrs(trip)
        if eta_hrs is not None:
            return eta_hrs * 60 * 60 * 1000

        if 'base_google_time' in trip.keys():
            return trip['base_google_time'] * os.environ['GOOGLE_TIME_FACTOR'] * 1000
        if 'eta_time' in trip.keys():
            start_time = datetime.strptime(trip['startTime'], fmt)
            end_time = datetime.strptime(trip['eta_time'], fmt)
            return (end_time - start_time).days * 24 * 60 * 60 * 1000  # Time in milliseconds
        if 'src' in trip.keys() and 'dest' in trip.keys():
            src = trip['src']
            dest = trip['dest']
            return get_google_time(src, dest) * 1000
        return -1
    except Exception as err:
        print(err)


def get_google_time(src, dest):
    if isinstance(src, str):
        src = map(int, src.split(','))
    if isinstance(dest, str):
        dest = map(int, dest.split(', '))
    """
    :arg : src, dest in [lat, lng]
    :rtype: time in minutes * GOOGLE Time Factor as extra time
    """
    response = get("https://maps.googleapis.com/maps/api/directions/json?",
                   params={
                       'origin': str(src[0]) + ',' + str(src[1]),
                       'destination': str(dest[0]) + ',' + str(dest[1]),
                       'key': str(os.environ['API_KEY'])
                   })
    # Could have multiple routes but first is always quicker
    try:
        route = response.json()['routes'][0]
        legs = route['legs']
        total_distance = 0
        total_time = 0
        for leg in legs:
            distance = leg['distance']['value']  # meters
            time = leg['duration']['value'] * 1000  # milli Seconds
            total_distance += distance
            total_time += time
        return total_time * os.environ['GOOGLE_TIME_FACTOR']
    except Exception as e:
        print("ERR GET GOOGLE TIME " + str(e))
        return 240000


def expected_pings(trip, eta_hrs):
    """
    :param: data for trip
    :rtype: Number of pings
    """
    time = get_sla(trip)
    if time is None or time == '':
        print(trip)
        return -1
    time = float(time) or time
    ping_rate = get_ping_rate(trip)
    if ping_rate is not None:
        return time / ping_rate
    ping_rate = get_user_ping_rate(trip['started_by'])
    if ping_rate is not None:
        return time / ping_rate
    pings = (8 * time) / (1000 * 60 * 24 * 60)
    return pings
