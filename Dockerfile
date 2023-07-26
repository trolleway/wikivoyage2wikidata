FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

RUN apt-get update --yes && apt-get  upgrade --yes
RUN apt-get install --no-install-recommends --fix-missing -y \
    jq python3-pip   gdal-bin proj-data libxml2-utils 
	
	
RUN apt-get install -y npm nodejs

RUN npm install -g wikibase-cli

RUN apt-get install -y libimage-exiftool-perl


RUN mkdir /opt/trolleway_wikidata

RUN chmod  --recursive 777 /opt/trolleway_wikidata

WORKDIR /opt/trolleway_wikidata
COPY requirements.txt requirements.txt
COPY photouploader/requirements.txt requirements2.txt
RUN pip3 install -r requirements.txt
RUN pip3 install -r requirements2.txt

RUN pip3 install pyexiftool




CMD ["/bin/bash"]
