FROM ubuntu
RUN apt-get update \
&& apt-get install  -y python3 \
&& apt-get install -y  python3-pip \
COPY . /app
WORKDIR /app
RUN pip3 --no-cache-dir install -r requirements.txt
CMD python3 test.py