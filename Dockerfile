FROM python:3.8

COPY . /app

# RUN apk add --no-cache --virtual .build-deps build-base
# RUN apk add --no-cache openldap-dev libxml2-dev libxslt-dev
# RUN pip install --no-cache-dir lxml python-ldap
# RUN apk del .build-deps
#
# RUN apk add --update --no-cache g++ gcc libxslt-dev libxml2 py-lxml
#
# RUN apk add --update --no-cache g++ gcc libxslt-dev
# RUN pip install lxml

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 5050

#ENTRYPOINT [ "python" ]

 CMD ["python", "-u", "main.py"]