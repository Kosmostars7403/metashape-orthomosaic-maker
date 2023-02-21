import json
import subprocess

from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'orthomosaic',
    auto_offset_reset='latest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for msg in consumer:
    subprocess.Popen([
        'python3',
        'main.py',
        '--flight_id',
        msg.value['id']
    ])
