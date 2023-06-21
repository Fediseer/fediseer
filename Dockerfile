FROM python:3.9.17-alpine3.18
RUN pip install requests beautifulsoup4 python-dotenv
RUN mkdir -p /opt/overseer
ADD overseer /opt/overseer
ADD requirements.txt /opt/overseer/requirements.txt
RUN pip install -r /opt/overseer/requirements.txt
CMD ["python3", "/opt/overseer/server.py"]