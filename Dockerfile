FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

RUN apt-get update 
RUN apt-get install --no-install-recommends -y \
    jq python3-pip nodejs npm gdal-bin proj-data libxml2-utils



RUN npm install -g wikibase-cli


RUN mkdir /opt/trolleway_wikidata

RUN chmod  --recursive 777 /opt/trolleway_wikidata

WORKDIR /opt/trolleway_wikidata
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt


#RUN pip3 install -r /opt/trolleway_wikidata/requirements.txt

CMD ["/bin/bash"]
