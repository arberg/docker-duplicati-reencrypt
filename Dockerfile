# syntax=docker/dockerfile:1
# https://docs.docker.com/language/python/build-images/
FROM python:3.11

WORKDIR /app

# COPY requirements.txt requirements.txt
# RUN pip3 install -r requirements.txt
RUN pip3 install pyAesCrypt python-gnupg joblib

# https://github.com/duplicati/duplicati/tree/master/Tools/Commandline/ReEncrypt
# https://github.com/duplicati/duplicati/wiki/Re-encrypt-remote-back-end-files
# wget https://raw.githubusercontent.com/duplicati/duplicati/master/Tools/Commandline/ReEncrypt/ReEncrypt.py
# wget https://raw.githubusercontent.com/duplicati/duplicati/master/Tools/Commandline/ReEncrypt/config.txt

COPY VERSION .
COPY app/ReEncrypt.py ReEncrypt.py
COPY app/.bash_aliases /root

# CMD ["python3", "ReEncrypt.py", "-c", "config.txt"]