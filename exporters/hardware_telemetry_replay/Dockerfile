FROM python:3.12-slim

WORKDIR /app

COPY exporters/hardware_telemetry_replay/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY exporters/hardware_telemetry_replay/ .

EXPOSE 9202

CMD ["python", "main.py"]