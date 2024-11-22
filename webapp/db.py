from aws_advanced_python_wrapper import AwsWrapperConnection
from psycopg import Connection

with AwsWrapperConnection.connect(
    Connection.connect,
    "host=database.cluster-xyz.us-east-1.rds.amazonaws.com dbname=db user=john password=pwd",
    plugins="failover",
    wrapper_dialect="aurora-pg",
    autocommit=True,
) as awsconn:
    awscursor = awsconn.cursor()
    awscursor.execute("SELECT aurora_db_instance_identifier()")
    awscursor.fetchone()
    for record in awscursor:
        print(record)
