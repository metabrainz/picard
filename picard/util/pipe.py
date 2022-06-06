# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 skelly37
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


import concurrent.futures
import os
from sys import platform


IS_WIN: bool = False

if platform == "win32" or platform == "cygwin":
    import win32pipe  # type: ignore
    import win32file  # type: ignore
    from pywintypes import error as WinApiError  # type: ignore
    IS_WIN = True


class Pipe:
    NO_RESPONSE_MESSAGE: str = "No response from FIFO"
    NOT_FOUND_MESSAGE: str = "FIFO doesn't exist"
    MESSAGE_TO_IGNORE: str = "Ignore this message, just testing the pipe"

    def __init__(self, app_name: str, app_version: str, args=None):
        if args is None:
            args = []

        self.__app_name: str = app_name
        self.__app_version: str = app_version
        self.__is_win: bool = IS_WIN

        # named pipe values needed by windows API
        if self.__is_win:
            # win32pipe.CreateNamedPipe
            # more about the arguments: https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createnamedpipea
            self.__MAX_INSTANCES: int = 1
            self.__OUT_BUFFER_SIZE: int = 65536
            self.__IN_BUFFER_SIZE: int = 65536
            # timeout doesn't really matter, concurrent.futures ensures that connections are closed in declared time
            # the value is in milliseconds
            self.__DEFAULT_TIMEOUT: int = 300

            # win32file.CreateFile
            # more about the arguments: http://timgolden.me.uk/pywin32-docs/win32file__CreateFile_meth.html
            self.__SHARE_MODE: int = 0
            self.__FLAGS_AND_ATTRIBUTES: int = 0

        self.path: str = self.__generate_filename()

        self.is_pipe_owner: bool = False

        # test if pipe is listened to even if no args provided
        if type(args) == list:
            if len(args) == 0:
                args.append(self.MESSAGE_TO_IGNORE)
        else:
            raise ValueError("args argument MUST be a list")

        if self.__is_win:
            for arg in args:
                if not self.send_to_pipe(arg):
                    self.is_pipe_owner = True
                    break
        else:
            if self.__pipe_exists():
                for arg in args:
                    if not self.send_to_pipe(arg):
                        try:
                            os.unlink(self.path)
                        except Exception as e:
                            raise ValueError(f"There was a problem with removing the old pipe:\n{e}")

                        self.__create_unix_pipe()
                        break
            else:
                self.__create_unix_pipe()

    def __pipe_exists(self) -> bool:
        return os.path.exists(self.path)

    def __generate_filename(self) -> str:
        prefix: str = ""
        username: str = os.getlogin()
        if self.__is_win:
            prefix = "\\\\.\\pipe\\"
        else:
            prefix = "/tmp/"

        return f"{prefix}{self.__app_name}_v{self.__app_version}_{username}_pipe_file"

    def __create_unix_pipe(self) -> None:
        os.mkfifo(self.path)
        self.is_pipe_owner = True

    def __win_sender(self, message: str) -> bool:
        pipe = win32pipe.CreateNamedPipe(
            self.path,
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
            self.__MAX_INSTANCES,
            self.__OUT_BUFFER_SIZE,
            self.__IN_BUFFER_SIZE,
            self.__DEFAULT_TIMEOUT,
            None)
        try:
            win32pipe.ConnectNamedPipe(pipe, None)
            win32file.WriteFile(pipe, str.encode(message))
        finally:
            win32file.CloseHandle(pipe)

        return True

    def __unix_sender(self, message: str) -> bool:
        with open(self.path, 'a') as fifo:
            fifo.write(message)
        return True

    def send_to_pipe(self, message: str, timeout_secs: float = 1.5) -> bool:
        __pool = concurrent.futures.ThreadPoolExecutor()
        sender = None
        if self.__is_win:
            sender = __pool.submit(self.__win_sender, message)
        else:
            sender = __pool.submit(self.__unix_sender, message)

        try:
            if sender.result(timeout=timeout_secs):
                return True
        except concurrent.futures._base.TimeoutError:
            # hacky way to kill the sender
            self.read_from_pipe()

        return False

    def read_from_pipe(self, timeout_secs: float = 1.5) -> str:
        if self.__is_win:
            return str(self.__read_from_win_pipe(timeout_secs))
        else:
            return self.__read_from_unix_pipe(timeout_secs)

    def __win_reader(self) -> str:
        response = ""  # type: ignore

        try:
            pipe = win32file.CreateFile(
                self.path,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                self.__SHARE_MODE,
                None,
                win32file.OPEN_EXISTING,
                self.__FLAGS_AND_ATTRIBUTES,
                None
            )
            while not response:
                response = win32file.ReadFile(pipe, 64 * 1024)

        except WinApiError as err:
            if err.args[0] == 2:
                raise FileNotFoundError(Pipe.NOT_FOUND_MESSAGE)
            elif err.args[0] == 109:
                raise FileNotFoundError("Pipe is broken")
            else:
                raise FileNotFoundError(f"{err.args[0]}; {err.args[1]}; {err.args[2]}")

        if response:
            if response[0] == 0:
                return response[1].decode("utf-8")  # type: ignore
            else:
                raise ValueError(f"INVALID RESPONSE: {response[1].decode('utf-8')}")  # type: ignore
        else:
            return Pipe.NO_RESPONSE_MESSAGE

    def __read_from_win_pipe(self, timeout_secs: float) -> str:
        __pool = concurrent.futures.ThreadPoolExecutor()
        reader = __pool.submit(self.__win_reader)

        try:
            if reader.result(timeout=timeout_secs):
                res: str = reader.result()
                if res != self.MESSAGE_TO_IGNORE:
                    return res
        except concurrent.futures._base.TimeoutError:
            # hacky way to kill the file-opening loop
            self.send_to_pipe(self.MESSAGE_TO_IGNORE)

        return Pipe.NO_RESPONSE_MESSAGE

    def __unix_reader(self) -> str:
        response: str = ""
        while not response:
            try:
                fifo = open(self.path, 'r')
                response = fifo.read().strip()
            except FileNotFoundError:
                raise FileNotFoundError(Pipe.NOT_FOUND_MESSAGE)

        if response:
            return response
        else:
            return Pipe.NO_RESPONSE_MESSAGE

    def __read_from_unix_pipe(self, timeout_secs: float) -> str:
        __pool = concurrent.futures.ThreadPoolExecutor()
        reader = __pool.submit(self.__unix_reader)

        try:
            if reader.result(timeout=timeout_secs):
                res: str = reader.result()
                if res != self.MESSAGE_TO_IGNORE:
                    return res
        except concurrent.futures._base.TimeoutError:
            # hacky way to kill the file-opening loop
            self.send_to_pipe(self.MESSAGE_TO_IGNORE)

        return Pipe.NO_RESPONSE_MESSAGE
