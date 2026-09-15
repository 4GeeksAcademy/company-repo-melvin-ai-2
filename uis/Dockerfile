FROM node:22-alpine

RUN apk add --no-cache libc6-compat wget

WORKDIR /workspace

COPY packages/auth /workspace/packages/auth
COPY src /workspace/src
COPY uis/website /workspace/uis/website
COPY uis/backoffice /workspace/uis/backoffice
COPY uis/start.sh /workspace/uis/start.sh

RUN chmod +x /workspace/uis/start.sh \
  && cd /workspace/uis/website && npm install --fetch-retries=5 --fetch-retry-maxtimeout=120000 \
  && cd /workspace/uis/backoffice && npm install --fetch-retries=5 --fetch-retry-maxtimeout=120000

EXPOSE 3000 3001

CMD ["/workspace/uis/start.sh"]
