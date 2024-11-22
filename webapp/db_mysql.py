from aws_advanced_python_wrapper import AwsWrapperConnection
from mysql.connector import Connect

with AwsWrapperConnection.connect(
    Connect,
    "host=quickbite-1.cluster-c7cs0ma46ikw.us-east-1.rds.amazonaws.com database=quickbite user=admin password=dVhypjOKEr3DOW3uiz1W",
    plugins="failover",
    wrapper_dialect="aurora-mysql",
    autocommit=True,
) as awsconn:
    awscursor = awsconn.cursor()
    awscursor.execute("SELECT CURRENT_TIMESTAMP;")
    awscursor.fetchone()
    for record in awscursor:
        print(record)
