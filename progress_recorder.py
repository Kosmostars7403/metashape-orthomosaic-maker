from pymongo import MongoClient
from bson.objectid import ObjectId


class ProgressRecorder:
    def __init__(self, debounce_percent_delta, flight_id):
        self.progress_state = {'status': 'PROCESSING'}
        self.debounce_percent_delta = debounce_percent_delta
        self.flight_id = flight_id
        self.previous_saved_progress = 0.0
        self.current_process = None
        self.db = None
        self.connect_mongo()

    def save_progress(self, process_name: str, progress: float):
        if self.current_process and self.current_process != process_name:
            self.previous_saved_progress = 0.0
            self.progress_state[self.current_process] = 100.00

        self.current_process = process_name

        self.progress_state[process_name] = round(progress, 2)

        if self.check_progress_for_save_in_db(progress):
            self.save_to_db()
            self.previous_saved_progress = progress

    def finish_pipeline(self):
        self.progress_state[self.current_process] = 100.00
        self.progress_state['status'] = 'COMPLETE'
        self.save_to_db()

    def check_progress_for_save_in_db(self, progress: float) -> bool:
        return progress - self.previous_saved_progress > self.debounce_percent_delta

    def save_to_db(self):
        self.db['flight-reports'].update_one(
            {"_id": ObjectId(self.flight_id)},
            {'$set': {'orthomosaic_progress': self.progress_state}}
        )

    def connect_mongo(self):
        client = MongoClient('mongodb://user:pass@localhost:27017')
        self.db = client['flight-reports']
