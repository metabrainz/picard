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
from typing import Optional

#from picard.const.sys import (
#    IS_MACOS,
#    IS_WIN,
#)

IS_WIN = False

if IS_WIN:
    import win32pipe  # type: ignore
    import win32file  # type: ignore
    from pywintypes import error as WinApiError  # type: ignore


class PipeError(Exception):
    pass


class PipeErrorInvalidArgs(PipeError):
    MESSAGE = "ERROR: Pipe() args argument has to be iterable"

    def __init__(self, msg):
        super().__init__(f"{self.MESSAGE}: {msg}.")


class PipeErrorNotFound(PipeError):
    MESSAGE = "ERROR: Pipe doesn't exist."

    def __init__(self):
        super().__init__(self.MESSAGE)


class PipeErrorBroken(PipeError):
    MESSAGE = "ERROR: Pipe is broken."

    def __init__(self):
        super().__init__(self.MESSAGE)


class PipeErrorInvalidResponse(PipeError):
    MESSAGE = "ERROR: Invalid response from pipe:"

    def __init__(self, response):
        super().__init__(f"{self.MESSAGE} {response}")


class PipeErrorWin(PipeError):
    MESSAGE = "ERROR: Windows API error\n"

    def __init__(self, winerror):
        super().__init__(f"{self.MESSAGE}{winerror}")


class Pipe:
    NO_RESPONSE_MESSAGE: str = "No response from FIFO"
    MESSAGE_TO_IGNORE: str = "Ignore this message, just testing the pipe"
    TIMEOUT_SECS: float = 1.5

    def __init__(self, app_name: str, app_version: str, args=None):
        if args is None:
            args = tuple()
        elif isinstance(args, str):
            args = (args,)
        else:
            try:
                args = tuple(args)
            except TypeError as exc:
                raise PipeErrorInvalidArgs(exc)

        if not args:
            args = (self.MESSAGE_TO_IGNORE,)

        self.__app_name: str = app_name
        self.__app_version: str = app_version
        self.__is_mac: bool = IS_MACOS
        self.__is_win: bool = IS_WIN

        # named pipe values needed by windows API
        if self.__is_win:
            self.__app_version = self.__app_version.replace(".", "-")

            # win32pipe.CreateNamedPipe
            # more about the arguments: https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createnamedpipea
            self.__MAX_INSTANCES: int = 1
            self.__BUFFER_SIZE: int = 65536
            # timeout doesn't really matter, concurrent.futures ensures that connections are closed in declared time
            # the value is in milliseconds
            self.__DEFAULT_TIMEOUT: int = 300

            # win32file.CreateFile
            # more about the arguments: http://timgolden.me.uk/pywin32-docs/win32file__CreateFile_meth.html
            self.__SHARE_MODE: int = 0
            self.__FLAGS_AND_ATTRIBUTES: int = 0

            # pywintypes.error error codes
            # more about the error codes: https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/18d8fbe8-a967-4f1c-ae50-99ca8e491d2d
            self.__FILE_NOT_FOUND_ERROR_CODE: int = 2
            self.__BROKEN_PIPE_ERROR_CODE: int = 109

        self.path: str = self.__generate_filename()

        self.is_pipe_owner: bool = False
        self.permission_error_happened: bool = False

        if self.__is_win:
            for arg in args:
                if not self.send_to_pipe(arg):
                    self.is_pipe_owner = True
                    break
        else:
            try:
                self.__create_unix_pipe()
            except FileExistsError:
                for arg in args:
                    if not self.send_to_pipe(arg):
                        self.__create_unix_pipe()
                        break

    def __generate_filename(self) -> str:
        if self.__is_win:
            self.__pipe_parent_dir = "\\\\.\\pipe\\"
        elif self.__is_mac:
            self.__pipe_parent_dir = os.path.expanduser("~/Library/Application Support/MusicBrainz/Picard/pipes/")
        else:
            self.__pipe_parent_dir = f"{os.getenv('XDG_RUNTIME_DIR')}/"
            # just in case the $XDG_RUNTIME_DIR is not declared, fallback dir
            if not self.__pipe_parent_dir:
                self.__pipe_parent_dir = os.path.expanduser("~/.config/MusicBrainz/Picard/pipes/")

        return f"{self.__pipe_parent_dir}{self.__app_name}_v{self.__app_version}_pipe_file"

    def __create_unix_pipe(self) -> None:
        try:
            try:
                # just to be sure that there's no broken pipe left
                os.unlink(self.path)
            except FileNotFoundError:
                pass
            try:
                os.mkfifo(self.path)
            # no parent dirs detected, need to create them
            except FileNotFoundError:
                os.makedirs(self.__pipe_parent_dir, exist_ok=True)
                os.mkfifo(self.path)
        except PermissionError:
            self.permission_error_happened = True
        self.is_pipe_owner = True

    def __win_sender(self, message: str) -> bool:
        pipe = win32pipe.CreateNamedPipe(
            self.path,
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
            self.__MAX_INSTANCES,
            self.__BUFFER_SIZE,
            self.__BUFFER_SIZE,
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

    def send_to_pipe(self, message: str, timeout_secs: Optional[float] = None) -> bool:
        if timeout_secs is None:
            timeout_secs = self.TIMEOUT_SECS

        __pool = concurrent.futures.ThreadPoolExecutor()

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

    def read_from_pipe(self, timeout_secs: Optional[float] = None) -> str:
        if timeout_secs is None:
            timeout_secs = self.TIMEOUT_SECS

        __pool = concurrent.futures.ThreadPoolExecutor()

        if self.__is_win:
            reader = __pool.submit(self.__win_reader)
        else:
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
                response = win32file.ReadFile(pipe, self.__BUFFER_SIZE)

        except WinApiError as err:
            if err.winerror == self.__FILE_NOT_FOUND_ERROR_CODE:
                raise PipeErrorNotFound from None
            elif err.winerror == self.__BROKEN_PIPE_ERROR_CODE:
                raise PipeErrorBroken from None
            else:
                raise PipeErrorWin(f"{err.winerror}; {err.funcname}; {err.strerror}") from None

        # response[0] stores an exit code while response[1] an actual response
        if response:
            if response[0] == 0:
                return str(response[1].decode("utf-8"))  # type: ignore
            else:
                raise PipeErrorInvalidResponse(response[1].decode('utf-8'))  # type: ignore
        else:
            return Pipe.NO_RESPONSE_MESSAGE

    def __unix_reader(self) -> str:
        response: str = ""
        while not response:
            try:
                with open(self.path, 'r') as fifo:
                    response = fifo.read().strip()
            except FileNotFoundError:
                raise PipeErrorNotFound from None

        return response or Pipe.NO_RESPONSE_MESSAGE
