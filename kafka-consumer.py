import json
import subprocess

from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'orthomosaic',
    auto_offset_reset='latest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for msg in consumer:
    print(msg.value['image_folder'])
    subprocess.Popen([
        'python3',
        'main.py',
        '--flight_id',
        msg.value['id'],
        '--image_dir',
        msg.value['image_folder']
    ])
