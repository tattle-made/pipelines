import pandas as pd
import numpy as np
import pika
import dask.dataframe as dd
from dask.multiprocessing import get
from datetime import datetime
import json

# Create dummy data
df = pd.DataFrame(
    {
    "title": ["A", "B", "C"],
    "timestamp": [str(datetime.now()), str(datetime.now()), str(datetime.now())],
    "url": ["abc", "def", "ghi"]})

def extract_data1(row):
    return row["title"]

def extract_data2(row):
    return row["timestamp"]

def extract_data3(row):
    return row["url"]

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='direct', exchange_type='direct', durable=True)
channel.confirm_delivery()

# Apply helper functions to extract different data from each record in the df
df["data1"] = df.apply(lambda row: extract_data1(row), axis=1)
df["data2"] = df.apply(lambda row: extract_data2(row), axis=1)
df["data3"] = df.apply(lambda row: extract_data3(row), axis=1)

# Or parallelize data extraction
# ddf = dd.from_pandas(df, npartitions=12)
# ddf["data1"] = ddf.map_partitions(extract_data1, axis=1, meta=("data1", str)).compute(get=get)
# ddf["data2"] = ddf.map_partitions(extract_data2, axis=1, meta=("data2", int)).compute(get=get)
# ddf["data3"] = ddf.map_partitions(extract_data3, axis=1, meta=("data3", str)).compute(get=get)

def publish_messages(message, routing_key):
    try:
        channel.basic_publish(
        exchange='direct', 
        routing_key=routing_key, 
        properties=pika.BasicProperties(delivery_mode=2), # make message persistent
        body=json.dumps(message))
        print("Published {} via {}".format(message, routing_key))
    except pika.exceptions.UnroutableError:
        print('Message could not be confirmed') 

# Send extracted data to appropriate queues via routing keys 
df["data1"].apply(publish_messages, args=("route1",))
df["data2"].apply(publish_messages, args=("route2",))
df["data3"].apply(publish_messages, args=("route3",))

