FROM python:3.9.17-alpine3.18
RUN pip install requests beautifulsoup4 python-dotenv pythorhead
RUN mkdir -p /opt/overseer-eye/
ADD update_blacklist.py /opt/overseer-eye/update_blacklist.py
CMD ["python3", "/opt/overseer-eye/update_blacklist.py"]