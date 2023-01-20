
FROM python

LABEL Maintainer="Daimakaimura"

WORKDIR /gennet
COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "gennet.py"]