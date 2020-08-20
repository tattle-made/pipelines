from dotenv import load_dotenv
load_dotenv()
import os
import pymongo
from pymongo import MongoClient
import luigi 
from luigi.contrib.mongodb import MongoCollectionTarget, MongoCellTarget, MongoRangeTarget
from luigi.mock import MockTarget
from luigi.task import flatten
from luigi_monitor import monitor
import pandas as pd
import datetime
from datetime import datetime
from datetime import timedelta
from pipeline_helper import initialize_mongo, initialize_googleapi, extract_text, initialize_translator, translate_text, filter_text
import requests
import json
import time
from random import uniform
import logging



class SourceData(luigi.Task):

    """ Gets URLs of recently scraped images from the Mongo DB where they are stored.
    db and collection must be passed as strings """

    db = luigi.Parameter()
    collection = luigi.Parameter()
    
    def output(self):
        return luigi.LocalTarget('urls.txt')
        
    def run(self):
        print("Beginning SourceData() task ...")
        print("Getting image urls from MongoDB ...")
        client = initialize_mongo()
        target = MongoCollectionTarget(client, self.db, self.collection)
        coll = target.get_collection()
        end = datetime.utcnow() - timedelta(days=20) # testing filter on old data
        start = end - timedelta(days=1)
        with self.output().open("w") as out_file:
            dump = {}
            for i in coll.find({"scraped_date": {'$gte':start,'$lt':end}}).limit(2): #limit for testing
                if i["media_type"] == "image":
                    url = i["s3_url"]
                    doc_id = str(i["_id"])
                    dump[doc_id] = url
            out_file.write(json.dumps(dump))
            print("SourceData() task complete")
            print("Image urls written to out_file")


class ExtractText(luigi.Task):

    """ Gets images from their S3 URLs and extracts the text from them.
    db and collection must be passed as strings """

    db = luigi.Parameter()
    collection = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget("extracted_text.txt")

    def run(self):
        print("Beginning ExtractText() task ...")
        print("Extracting text from images ...")
        client = initialize_googleapi()
        with self.output().open("w") as out_file:
            dump = {}
            with self.input().open("r") as in_file:
                for mongo_data in in_file:
                    mongo_data = json.loads(mongo_data)
                    for doc_id, url in mongo_data.items():
                        text = extract_text(client, url)
                        dump[doc_id] = text
            out_file.write(json.dumps(dump))
            print("ExtractText() task complete")
            print("Extracted text written to out_file")

    def requires(self):
        return SourceData(self.db, self.collection)

class TranslateText(luigi.Task):

    """ Translates the text extracted from images into English.
    db and collection must be passed as strings """

    db = luigi.Parameter()
    collection = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget("translated_text.txt")

    def run(self):
        print("Beginning TranslateText() task ...")
        print("Transating text to English ...")
        translator = initialize_translator()
        with self.output().open("w") as out_file:
            dump = {}
            with self.input().open("r") as in_file:
                for extracted_text in in_file:
                    extracted_text = json.loads(extracted_text)
                    for doc_id,text in extracted_text.items():
                        translation = translate_text(text, translator)
                        dump[doc_id] = translation 
                        time.sleep(uniform(3,5))
            out_file.write(json.dumps(dump))
            print("TranslateText() task complete")
            print("Translated text written to out_file")
              
    def requires(self):
        return ExtractText(self.db, self.collection)


class FilterText(luigi.Task):

    """ Checks if the translated text contains relevant keywords and generates binary labels accordingly. 
    Text is first cleaned up, tokenized and converted to lowercase.
    db and collection must be passed as strings """

    db = luigi.Parameter()
    collection = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget("filtered_text.txt")

    def run(self):
        print("Beginning FilterText() task ...")
        print("Applying keyword filter to text ...")
        with self.output().open("w") as out_file:
            dump = {}
            with self.input().open("r") as in_file:
                for translated_text in in_file:
                    translated_text = json.loads(translated_text)
                    for doc_id,translation in translated_text.items():
                        label = filter_text(translation)
                        dump[doc_id] = label
            out_file.write(json.dumps(dump))
            print("FilterText() task complete")
            print("Keyword filter labels written to out_file")
                        
    def requires(self):
        return TranslateText(self.db, self.collection)


class StoreExtraction(luigi.Task):
    """ Stores the extracted text in the image's Mongo DB record.
    db and collection must be passed as strings """

    db = luigi.Parameter()
    collection = luigi.Parameter()
    field = "extracted_text"

    def output(self):
        return luigi.LocalTarget("dummy_extraction.txt")
        #return MockTarget("StoreExtraction", mirror_on_stderr=True)

    def run(self):
        print("Beginning StoreExtraction() task ...")
        print("Storing extracted text in MongoDB ...")
        client = initialize_mongo()
        dump = {}
        with self.input().open("r") as in_file:
            for extracted_text in in_file:
                extracted_text = json.loads(extracted_text)
                for doc_id,text in extracted_text.items():
                    # target = MongoCellTarget(client, self.db, self.collection, doc_id, self.field)
                    # target.write(label)
                    dump[doc_id] = text
        doc_ids = list(dump.keys())
        target = MongoRangeTarget(client, self.db, self.collection, doc_ids, self.field)
        target.write(dump)
        print("StoreExtraction() task complete")
        print("{} image text extractions stored in MongoDB".format(len(doc_ids)))

        # Write a dummy output file so that StoreLabel's dependency is fulfilled
        with self.output().open("w") as out_file:
            out_file.write("done")
                        
    def requires(self):
        return ExtractText(self.db, self.collection)

class StoreTranslation(luigi.Task):
    """ Stores the translated text in the image's Mongo DB record.
    db and collection must be passed as strings """

    db = luigi.Parameter()
    collection = luigi.Parameter()
    field = "translated_text"

    def output(self):
        return luigi.LocalTarget("dummy_translation.txt")
        #return MockTarget("StoreTranslation", mirror_on_stderr=True)

    def run(self):
        print("Beginning StoreTranslation() task ...")
        print("Storing translated text in MongoDB ...")
        client = initialize_mongo()
        dump = {}
        with self.input().open("r") as in_file:
            for translated_text in in_file:
                translated_text = json.loads(translated_text)
                for doc_id,text in translated_text.items():
                    # target = MongoCellTarget(client, self.db, self.collection, doc_id, self.field)
                    # target.write(label)
                    dump[doc_id] = text
        doc_ids = list(dump.keys())
        target = MongoRangeTarget(client, self.db, self.collection, doc_ids, self.field)
        target.write(dump)
        print("StoreTranslation() task complete")
        print("{} image text translations stored in MongoDB".format(len(doc_ids)))

        # Write a dummy output file so that StoreLabel's dependency is fulfilled
        with self.output().open("w") as out_file:
            out_file.write("done")
                        
    def requires(self):
        return TranslateText(self.db, self.collection)

class StoreLabel(luigi.Task):

    """ Adds the keyword filter label to the image's Mongo DB record.
    db and collection must be passed as strings """

    db = luigi.Parameter()
    collection = luigi.Parameter()
    field = "keyword_label"

    def run(self):
        print("Beginning StoreLabel() task ...")
        print("Storing keyword filter labels in MongoDB ...")
        client = initialize_mongo()
        dump = {}
        with self.input().open("r") as in_file:
            for filtered_text in in_file:
                filtered_text = json.loads(filtered_text)
                for doc_id,label in filtered_text.items():
                    # target = MongoCellTarget(client, self.db, self.collection, doc_id, self.field)
                    # target.write(label)
                    # target.exists()
                    dump[doc_id] = label
        doc_ids = list(dump.keys())
        target = MongoRangeTarget(client, self.db, self.collection, doc_ids, self.field)
        target.write(dump)
        target.exists()
        print("StoreLabel() task complete")
        print("{} new labels stored in MongoDB".format(len(doc_ids)))
        print("{} posts contain keywords".format(sum(value == 1 for value in dump.values())))
        print("Clearing all out_files ...")
        os.remove("urls.txt")
        os.remove("extracted_text.txt")
        os.remove("translated_text.txt")
        os.remove("filtered_text.txt")
        os.remove("dummy_extraction.txt")
        os.remove("dummy_translation.txt")
        print("Out_files cleared")
                        
    def requires(self):
        return FilterText(self.db, self.collection)

    # The _requires method lets StoreLabel depend on StoreText's completion without consuming StoreText's output
    def _requires(self):
        return flatten([StoreExtraction(self.db, self.collection), StoreTranslation(self.db, self.collection), super(StoreLabel, self)._requires()])



if __name__ == "__main__": 
    #with monitor(slack_url=<webhook>, max_print=10, username= "Luigi-Slack-Bot"):
    luigi.build([StoreLabel(db=os.environ.get("SHARECHAT_DB_NAME"), collection=os.environ.get("SHARECHAT_DB_COLLECTION"))]) 

