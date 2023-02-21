class ProgressRecorder:
    def __init__(self, debounce_percent_delta):
        self.progress_state = {}
        self.previous_saved_progress = 0.0
        self.current_process = None
        self.debounce_percent_delta = debounce_percent_delta

    def save_progress(self, process_name: str, progress: float):
        if self.current_process and self.current_process != process_name:
            self.previous_saved_progress = 0.0
            self.progress_state[self.current_process] = 100.00

        self.current_process = process_name

        self.progress_state[process_name] = round(progress, 2)

        if self.check_progress_for_save_in_db(progress):
            self.save_to_db()
            self.previous_saved_progress = progress

    def check_progress_for_save_in_db(self, progress: float) -> bool:
        return progress - self.previous_saved_progress > self.debounce_percent_delta

    def save_to_db(self):
        print('\n\n\n\n\n\n\n\n\nsaved to db', self.progress_state, '\n\n\n\n\n\n\n\n\n')
