## Introduction

The keyword filter pipeline passes multilingual and multimodal social media / chat app content archived by Tattle through a data pipeline comprising of a series of Luigi tasks. When triggered, it executes all the tasks and adds a binary label to each item's Mongo DB record depending on whether it contains some defined keywords. These keywords are topic words extracted via LDA topic modelling on Tattle's database of fact-checking stories. The purpose of this pipeline is to flag content that is more relevant, i.e. more likely to contain misinformation.
Read more about Luigi pipelines [here](https://luigi.readthedocs.io/en/stable/index.html)

## Running locally

1. Fork the repo 
2. Create a new virtual environment and install the dependencies 
```
pip install requirements.txt
```
3. Create a .env file with the following environment variables
```
export DB_NAME = <Mongo DB name>
export DB_PASSWORD = <Mongo DB password>
export DB_COLLECTION = <Mongo collection name>
export GOOGLE_APPLICATION_CREDENTIALS = <path to Google Vision API credentials>
export LUIGI_CONFIG_PATH = <path to luigi.cfg"

```
4. Activate the virtual environment (Google Vision API may not work properly if you don't)
```
source env/bin/activate
```

5. Activate the task visualizer. Command line:
```
luigid --background --pidfile luigid.pid --logdir luigi --state-path luigi/state --address 0.0.0.0 --port 8082
```
6. Open localhost:8082 in a browser window to monitor the tasks
7. Trigger the pipeline. Command line:
```
python3 keyword_filter_pipeline.py StoreLabel 
``` 

## Notes

- To retry failed tasks from the task visualizer, click the 'Forgive failures' button next to the failed task after fixing the bug that caused the failure. This turns a failed task into a pending one. For this to work properly set the worker parameter ```keep_alive``` to ```True``` in [luigi.cfg](luigi.cfg)
- The scheduler parameters ```retry_delay``` and ```retry_count``` in [luigi.cfg](luigi.cfg) can be used to set auto-retry preferences. Read more about configuration parameters [here](https://luigi.readthedocs.io/en/stable/configuration.html) 
- The Mongo DB fields for keyword filter labels and extracted text are hardcoded, but could also be passed as parameters along with the db and collection names. 
- Despite their separate goals, StoreText needs to happen before StoreLabel because it requires a textfile that is deleted when the final task is completed. Deleting all the out_files ensures that the tasks can run again from the beginning.
- The luigi monitor sends success/failure reports to Slack. Read the [documentation](https://github.com/hudl/luigi-monitor) and beware of hyphens.