FROM alpine:3.19.0
LABEL manteiner="mviudes@student.42madrid.com"

RUN echo "https://mirror.leaseweb.com/alpine/v3.19/main" > /etc/apk/repositories && \
    echo "https://mirror.leaseweb.com/alpine/v3.19/community" >> /etc/apk/repositories && \
    apk --no-cache update && \
    apk --no-cache upgrade && \
    apk add --no-cache nginx

COPY ./nginx.conf /etc/nginx/nginx.conf

ENTRYPOINT ["nginx","-g","daemon off;"]

