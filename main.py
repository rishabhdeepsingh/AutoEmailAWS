from create_sheet import create_sheet
import send_email
from datetime import datetime


def run(event, context):
    output = create_sheet()
    send_email.send(output)
    output.close()

#
# start = datetime.now()
# run(1, 1)
# end = datetime.now()
# print((end - start).seconds)
#
# # print(os.environ['TO_EMAILS'].split(','))
# print(os.environ['SUBJECT'])
