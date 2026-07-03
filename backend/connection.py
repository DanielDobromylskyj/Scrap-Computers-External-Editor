import json
import time
import os


class GameConnection:
    def __init__(self, mod_path):
        self.path = mod_path

        if not os.path.exists(self.path):
            raise FileNotFoundError("Mod directory not found")

        self.send_path = os.path.join(self.path, 'mod_in.json')
        self.recv_path = os.path.join(self.path, 'mod_out.json')

        self.last_recv_time = 0

        if not self.is_connected():
            raise ConnectionError("Failed to connect to mod. Is the game running / block placed?")

    def reset_response(self):
        self.last_recv_time = os.path.getmtime(self.recv_path)

        with open(self.recv_path, 'w') as f:
            f.write('')

    def has_responded(self):
        return os.path.getmtime(self.recv_path) != self.last_recv_time

    def read_response(self, timeout):
        start = time.time()
        while os.path.getmtime(self.recv_path) == self.last_recv_time:
            if time.time() - start < timeout:
                return None

        time.sleep(0.1)
        with open(self.recv_path, 'r') as f:
            data = f.read()

        if data:
            return json.loads(data)["result"]
        return None

    def execute(self, command, timeout=3, await_response=True, **kwargs):
        self.reset_response()

        kwargs["command"] = command  # add our command to query
        with open(self.send_path, 'w') as f:
            f.write(json.dumps(kwargs))

        if await_response:
            return self.read_response(timeout)
        return None

    def is_connected(self):
        return self.execute('ping') == "pong"



