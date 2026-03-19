FROM mongo:7

WORKDIR /init
COPY init.sh /init/init.sh
RUN chmod +x /init/init.sh

ENTRYPOINT ["bash", "/init/init.sh"]
