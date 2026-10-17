"""Win32 sampling: process category and idle flag only; never read window text."""
import ctypes
import sys
from ctypes import wintypes
from presence import Observation, classify, IDLE_SECONDS


class WindowsSource:
    def __init__(self):
        if sys.platform != 'win32':
            raise RuntimeError('Windows is required for collection')
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.user.GetForegroundWindow.restype = wintypes.HWND
        self.user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.user.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.kernel.GetTickCount.restype = wintypes.DWORD
        self.user.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.user.OpenInputDesktop.restype = wintypes.HANDLE
        self.user.GetUserObjectInformationW.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        self.user.GetUserObjectInformationW.restype = wintypes.BOOL
        self.user.CloseDesktop.argtypes = [wintypes.HANDLE]
        self.user.CloseDesktop.restype = wintypes.BOOL

    def sample(self):
        desktop = self.user.OpenInputDesktop(0, False, 0x0001)  # DESKTOP_READOBJECTS
        if not desktop:
            return Observation(None, 'unknown')  # locked, secure desktop, or unavailable
        try:
            name = ctypes.create_unicode_buffer(256)
            needed = wintypes.DWORD()
            if not self.user.GetUserObjectInformationW(desktop, 2, name, ctypes.sizeof(name), ctypes.byref(needed)):
                return Observation(None, 'unknown')
            if name.value.casefold() != 'default':
                return Observation(None, 'locked')
        finally:
            self.user.CloseDesktop(desktop)

        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [('cbSize', wintypes.UINT), ('dwTime', wintypes.DWORD)]

        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(info)
        self.user.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
        self.user.GetLastInputInfo.restype = wintypes.BOOL
        if not self.user.GetLastInputInfo(ctypes.byref(info)):
            return Observation(None, 'unknown')
        idle = ((self.kernel.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000
        hwnd = self.user.GetForegroundWindow()
        if not hwnd:
            return Observation(None, 'unknown')
        pid = wintypes.DWORD()
        if not self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)):
            return Observation(None, 'unknown')
        process = self.kernel.OpenProcess(0x1000, False, pid.value)
        if not process:
            return Observation(None, 'unknown')
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(buffer))
            if not self.kernel.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
                return Observation(None, 'unknown')
            category = classify(buffer.value)
            # buffer and process path are not returned, logged, or persisted.
        finally:
            self.kernel.CloseHandle(process)
        return Observation(category, 'idle' if idle >= IDLE_SECONDS else 'active')
