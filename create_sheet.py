import io
import json
import xlsxwriter
from expectation import *
from helper import *
from datetime import datetime


def ping_percentage(exp, act):
    mx = max(exp, act)
    mn = min(exp, act)
    if mx == 0:
        return 100
    return ((mx - mn) / mx) * 100


def add_new_sheet(workbook, headings, data, name):
    name = name.replace('\\', ' ')
    name = name.replace('/', ' ')
    worksheet = workbook.add_worksheet(name)
    column = 0
    heading_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#457DC0'})
    for heading_key, heading_val in headings.items():
        if heading_val is None:
            continue
        worksheet.write(0, column, heading_val, heading_format)
        row = 1
        for result in data:
            worksheet.write(row, column, str(result[str(heading_key)]))
            row += 1
        column += 1
        worksheet.set_column(column, column, len(heading_key) + 7)
    worksheet.set_column(0, 0, 25)
    worksheet.set_column(1, 1, 15)
    worksheet.set_column(2, 2, 25)


def create_sheet():
    config_file = json.load(open('config.json', 'r'))
    headings = config_file['headings']
    trips = get_trips()
    actual_pings = get_actual_pings(list(trip['_id'] for trip in trips))
    all_pings = get_all_pings(trips)
    res = []
    cnt = 0
    cnt_client_client = 0
    for trip in trips:
        trip_keys = trip.keys()
        client_client = ''
        if 'client_client' in trip_keys:
            client_client = trip['client_client']
        if client_client != '':
            cnt_client_client += 1
        actual_ping = 0
        for pings in actual_pings:
            if pings['_id'] == trip['_id']:
                actual_ping = pings['count']

        start_time = trip['startTime'] if 'startTime' in trip_keys else trip['createdAt']
        expire_time = trip['expiresAt'] if 'expiresAt' in trip_keys else None
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S.%fz')
        eta_hrs = get_eta_hrs(trip)
        if eta_hrs == -1:
            continue
        if eta_hrs is None:
            if expire_time is not None:
                eta_hrs = get_days(expire_time - start_time) * 24
        exp_pings = expected_pings(trip, eta_hrs)
        if exp_pings == -1:
            continue
        ping_rate = get_ping_rate(trip)
        exp_pings = eta_hrs * 60 * 60 / ((float(ping_rate) or ping_rate) / 1000)

        expected_pings_last = 0
        try:
            expected_pings_last = int(
                (get_last_expected_pings(start_time, eta_hrs) * 24 * ping_rate / (1000 * 60 * 60)) + 0.5)
        except Exception as e:
            print("EXP PING LAST ", e, trip['_id'])
        actual_ping_last = 0
        try:
            actual_ping_last = get_last_actual_pings(all_pings, trip['_id'])
        except Exception as e:
            print("ACT PING LAST ", e, trip['_id'])
        try:
            if ping_percentage(expected_pings_last, actual_ping_last) >= 20.0:
                res.append({
                    '_id': str(trip['_id']),
                    'user': trip['user'],
                    'client_client': client_client,
                    'start_time': start_time.strftime("%d/%m/%Y %H:%M"),
                    'actual_ping': actual_ping,
                    'pings': int(exp_pings),
                    'ping_rate': ping_rate,
                    'eta_days': round(eta_hrs / 24, 2),
                    'expected_pings': round(expected_pings_last, 2),
                    'actual_pings': actual_ping_last
                })
        except Exception as e:
            print(trip['_id'], e)
        cnt += 1
    if cnt_client_client == 0:
        headings['client_client'] = None

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    add_new_sheet(workbook, headings, res, "ALL Trips")
    workbook.close()
    print("Sheet written")
    return output
