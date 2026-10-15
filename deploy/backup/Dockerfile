FROM postgres:16.10-alpine3.22

# Cliente 16 acompanha o servidor da aplicação. Sem compiladores no runtime.
RUN apk add --no-cache bash openssl aws-cli curl coreutils tini \
    && mkdir /backup && chown postgres:postgres /backup
WORKDIR /backup
COPY --chown=postgres:postgres agendar.sh backup.sh comum.sh restaurar.sh ./
COPY --chown=postgres:postgres coletor_local.py ./
USER postgres
ENV TZ=UTC
ENTRYPOINT ["/sbin/tini", "-g", "--", "bash", "/backup/agendar.sh"]
