FROM python:3.6
<<<<<<< HEAD

RUN apt-get update
COPY . /app
WORKDIR /app
RUN pip install virtualenv
RUN pip install -r requirements.txt
=======
WORKDIR /app
COPY requirements.txt /app
COPY keyword_filter_pipeline.py /app
COPY pipeline_helper.py /app
COPY luigi.cfg /app
# add env variables

RUN pip install -r /app/requirements.txt
CMD ["luigid"]

>>>>>>> bd3ac94d8434f0fb2e589284ff19968e92fbbb19
