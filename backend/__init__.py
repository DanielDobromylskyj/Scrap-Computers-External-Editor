import os

from .connection import GameConnection

def upperFirst(x):
    return x[0].upper() + x[1:]

class FileObject:
    def __init__(self, fs, data, start_path):
        self.__fs = fs
        self.__data = data
        self.__start_path = start_path

    def __repr__(self):
        return f"<SC:{upperFirst(self.__data[1])}(\"{self.path}\")>"

    @property
    def is_file(self):
        return self.__data[1] == "file"

    @property
    def is_directory(self):
        return self.__data[1] == "directory"

    @property
    def path(self):
        return os.path.join(self.__start_path, self.__data[0]).replace("\\", "/")

    @property
    def name(self):
        return self.__data[0]

    def list(self):
        if not self.is_directory:
            raise NotADirectoryError("Not a directory")
        return self.__fs.list_dir(self.path)

    def read(self):
        if not self.is_file:
            raise FileNotFoundError("Not a file")
        return self.__fs.read_path(self.path)

    def write(self, data):
        if not self.is_file:
            raise FileNotFoundError("Not a file")
        return self.__fs.write_path(self.path, data)


class FileSystem:
    def __init__(self, mod_path):
        self.connection = GameConnection(mod_path)
        self.connected = False

        self.locked = False

    def get_available_computers(self):
        if self.locked:
            self.terminate_lock()

        return self.connection.execute("computers")

    def select_computer(self, computer_id):
        if self.locked:
            self.terminate_lock()

        res = self.connection.execute("select", id=computer_id)
        self.connected = res
        return res

    def list_dir(self, path="/"):
        if not self.connected:
            raise ConnectionError("Not connected")

        if self.locked:
            self.terminate_lock()


        data = self.connection.execute("files", path=path)
        if data:
            return [FileObject(self, file_dat, path) for file_dat in data]

        return []

    def file_object_from_path(self, path: str, is_dir=False) -> FileObject:
        file_name = path.split("/")[-1]
        path = path.removesuffix(file_name)

        return FileObject(self, [file_name, "file" if not is_dir else "directory"], path)

    def read_path(self, path):
        if not self.connected:
            raise ConnectionError("Not connected")

        if self.locked:
            return None

        return self.connection.execute("grab", path=path)


    def write_path(self, path, data):
        if not self.connected:
            raise ConnectionError("Not connected")

        if self.locked:
            self.terminate_lock()


        return self.connection.execute("update", path=path, data=data)

    def reset_print_log(self):
        if not self.connected:
            raise ConnectionError("Not connected")

        if self.locked:
            self.terminate_lock()

        return self.connection.execute("console-reset")

    def start_print_read(self):
        if not self.connected:
            raise ConnectionError("Not connected")

        if self.locked:
            return None

        self.connection.execute("console", await_response=False)
        self.locked = True

        return None

    def start_error_read(self):
        if not self.connected:
            raise ConnectionError("Not connected")

        if self.locked:
            return None

        self.connection.execute("error", await_response=False)
        self.locked = True

        return None

    def fetch_locked_response(self):
        if not self.connected:
            raise ConnectionError("Not connected")

        if not self.locked:
            return None

        if self.connection.has_responded():
            self.locked = False
            res = self.connection.read_response(timeout=1)
            return res if type(res) == list else [res] if type(res) is not None else []
        else:
            return False

    def terminate_lock(self):
        if not self.connected:
            raise ConnectionError("Not connected")

        self.connection.reset_response()
        self.locked = False
