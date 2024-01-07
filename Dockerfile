FROM ubuntu:23.10
ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

RUN apt-get update 
RUN apt-get install --no-install-recommends --fix-missing -y \
    jq python3-pip  gdal-bin proj-data libxml2-utils nano
RUN apt-get install -y npm nodejs
RUN npm install -g wikibase-cli
RUN apt-get install -y libimage-exiftool-perl
RUN mkdir /opt/trolleway_wikidata

RUN chmod  --recursive 777 /opt/trolleway_wikidata

WORKDIR /opt/trolleway_wikidata
COPY requirements.txt requirements.txt
RUN pip3 install --break-system-packages -r requirements.txt
RUN pip3 install pyexiftool

CMD ["/bin/bash"]
