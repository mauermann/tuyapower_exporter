FROM python:3-slim

WORKDIR /

COPY requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt

COPY devices.json tuyapower_exporter.py /

ENV CONFIG /devices.json
ENV PORT 9067
EXPOSE 9067
EXPOSE 6666/udp
EXPOSE 6667/udp

CMD [ "python", "-u", "/tuyapower_exporter.py" ]
