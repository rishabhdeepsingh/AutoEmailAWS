import datetime
import os
from pymongo import MongoClient


def get_database():
    server, port = str(os.environ['DATABASE_SERVER']).rsplit(':', 1)
    client = MongoClient(server, port=int(port))
    database = client['telenitytracking']
    return database


def get_trips():
    database = get_database()
    collection = database['trips']
    data = collection.find({'running': True, 'user': {
        '$nin': os.environ['BLACKLIST_CLIENTS'].split(',')
    }, 'client_client': {
        '$nin': os.environ['BLACKLIST_CLIENT_CLIENT'].split(',')
    }
                            })
    return list(x for x in data)


def get_all_users():
    database = get_database()
    collection = database['users']
    data = collection.find({})
    return list(x for x in data)


def get_actual_pings(trips_list):
    database = get_database()
    collection = database['status']
    data = collection.aggregate([{
        '$match': {
            'tripId': {'$in': trips_list}
        }
    }, {'$group': {
        '_id': '$tripId',
        'count': {'$sum': 1}
    }}])
    return [x for x in data]


def get_all_pings(trips_list):
    trips_ids = [x['_id'] for x in trips_list]
    database = get_database()
    collection = database['status']
    try:
        data = collection.aggregate([{
            '$match': {
                'tripId': {
                    '$in': trips_ids
                }
            }
        }, {
            '$group': {
                '_id': '$tripId', 'pings': {'$push': '$$ROOT'}
            }
        }])
        return list(x for x in data)
    except Exception as e:
        print(trips_ids)
        print(str(e))
        return []


def get_days(diff):
    return diff.total_seconds() / (24 * 60 * 60)


def get_last_expected_pings(start_time, eta_hrs):
    now_time = datetime.datetime.now()
    now_time24 = now_time - datetime.timedelta(days=1)
    end_time = start_time + datetime.timedelta(hours=eta_hrs)
    if now_time24 < start_time:
        diff = now_time - start_time
        return get_days(diff)
    if start_time <= now_time24 <= end_time and start_time <= now_time <= end_time:
        return get_days(datetime.timedelta(days=1))
    if start_time <= now_time24 <= end_time:
        return get_days(end_time - now_time24)
    return 0


def get_last_actual_pings(all_pings, trip_id):
    pings_list = []
    try:
        for pings in all_pings:
            if pings['_id'] == trip_id:
                pings_list = pings['pings']
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(1)
        cnt = 0
        for ping in pings_list:
            if start_time < ping['createdAt'] < end_time:
                cnt += 1
        return cnt
    except Exception as e:
        print(e, trip_id)


def get_eta_days(trip):
    if 'eta_days' in trip.keys():
        eta_days = trip['eta_days']
        eta_days = str(eta_days) or eta_days  # to remove that None shit in the eta_days
        try:
            return float(eta_days)
        except Exception as e:
            # print("ERR {0} {1} in {2}".format(e, 'eta_days', trip['_id']))
            return None
    else:
        # print("ERR No {0} in {1}".format('eta_days', trip['_id']))
        return None


def get_eta_hrs(trip):
    eta_days = get_eta_days(trip)
    if eta_days is None:
        if 'eta_hrs' in trip.keys():
            eta_hrs = str(trip['eta_hrs']) or trip['eta_hrs']  # to remove that None shit in the eta_hrs
            try:
                return float(eta_hrs)
            except Exception as e:
                print("ERR {} For Trip {}".format(e, trip['_id']))
    if eta_days is not None:
        return eta_days * 24
    else:
        try:
            return trip['base_google_time'] / 3600
        except Exception as e:
            print(e)
            return -1
