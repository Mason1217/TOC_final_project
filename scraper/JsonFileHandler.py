import json
import os
from typing import Any, Optional

class JsonFileHandler():
    """
    Handles JSON file operations including creation, reading, and writing.
    Automatically handles file naming conflicts by appending incrementing numbers.
    """

    def __init__(self, path: str, name: str, mode: str = "r"):
        """
        Initialize the JsonFileHandler.

        Args:
            path (str): The directory path.
            name (str): The desired file name (e.g., 'data.json').
            mode (str): File open mode ('r' for read, 'w' for write/create).
        """
        if not os.path.exists(path):
            os.makedirs(path)

        self.__store_path = path
        self.__file_name_base, self.__file_extension = os.path.splitext(name)
        self.__file_path = os.path.join(self.__store_path, name)
        self.__mode = mode
        self.__file = None

        if mode == "r":
            self.__open_read()
        elif mode == "w":
            self.__open_write()
        else:
            raise ValueError(f"Unsupported mode: {mode}")

    def __open_read(self) -> None:
        """Opens an existing file for reading."""
        if os.path.exists(self.__file_path):
            self.__file = open(self.__file_path, mode="r", encoding="utf-8")
        else:
            # 如果讀取模式下檔案不存在，轉為寫入模式建立新檔
            print(f"File {self.__file_path} not found, creating new.")
            self.__open_write()
            self.__mode = "w"

    def __open_write(self) -> None:
        """Creates a new file for writing, handling naming conflicts."""
        # 邏輯：如果要寫入 evidence.json 但已存在，自動變成 evidence1.json
        base_name = self.__file_name_base
        ext = self.__file_extension
        i = 1
        
        target_path = self.__file_path
        
        # 尋找一個不存在的檔名
        while os.path.exists(target_path):
            current_name = f"{base_name}{i}{ext}"
            target_path = os.path.join(self.__store_path, current_name)
            i += 1
        
        self.__file_path = target_path
        self.__file = open(self.__file_path, mode="w", encoding="utf-8")

    def get_filename(self) -> str:
        """Returns the actual filename being used."""
        return os.path.basename(self.__file_path)

    def write(self, data: Any) -> None:
        """Writes data to the JSON file."""
        if self.__mode == "w" and self.__file:
            # seek(0) 和 truncate() 確保覆寫
            self.__file.seek(0)
            self.__file.truncate()
            json.dump(data, self.__file, indent=4, ensure_ascii=False)
        else:
            raise IOError("File not open in write mode")

    def read(self) -> Any:
        """Reads data from the JSON file."""
        if self.__mode == "r" and self.__file:
            try:
                self.__file.seek(0)
                return json.load(self.__file)
            except json.JSONDecodeError:
                return {}
        else:
            raise IOError("File not open in read mode")

    def close(self) -> None:
        """Closes the file handle."""
        if self.__file:
            self.__file.close()

    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        if exc_type:
            print(f"Error handling file: {exc_type}, {exc_value}")
