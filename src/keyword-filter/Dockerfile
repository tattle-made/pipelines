FROM python:3.6
WORKDIR /app
COPY requirements.txt /app
COPY keyword_filter_pipeline.py /app
COPY pipeline_helper.py /app
COPY luigi.cfg /app
# add env variables

RUN pip install -r /app/requirements.txt
CMD ["luigid"]

