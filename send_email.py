import os
import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

CHARSET = "utf-8"
AWS_REGION = "us-east-1"


def send(output):
    sender = os.environ['FROM_EMAIL']
    recipient = os.environ['TO_EMAILS'].split(',')

    BODY_HTML = """
    <html>
    <head></head>
    <body>
    <p>Please see the attached file for Client wise expected vs actual ping consumed</p>
    </body>
    </html>
    """

    client = boto3.client('ses', region_name=AWS_REGION)

    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    msg['Subject'] = os.environ['SUBJECT']
    msg['From'] = sender
    msg['To'] = ", ".join(recipient)

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')

    # Encode the text and HTML content and set the character encoding. This step is
    # necessary if you're sending a message with characters outside the ASCII range.
    html_part = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

    # Add the text and HTML parts to the child container.
    msg_body.attach(html_part)

    attachment = output.getvalue()

    # Define the attachment part and encode it using MIMEApplication.
    att = MIMEApplication(attachment)

    # Add a header to tell the email client to treat this part as an attachment,
    # and to give the attachment a name.
    att.add_header('Content-Disposition', 'attachment', filename=os.path.basename(os.environ['FILE_NAME'] + '.xlsx'))

    # Attach the multipart/alternative child container to the multipart/mixed parent container.
    # Add the attachment to the parent container.
    msg.attach(msg_body)
    msg.attach(att)
    print(msg)

    try:
        response = client.send_raw_email(
            Source=sender,
            Destinations=recipient,
            RawMessage={
                'Data': msg.as_string()
            })
        return response
    except ClientError as e:
        print(e.response['Error']['Message'])
    print("Email sent!")
