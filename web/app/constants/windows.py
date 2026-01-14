WINDOWS_SYSTEM_PORTS = {135, 137, 138, 139, 445, 5357}


WINDOWS_ALLOWED_USER_PATHS = (
    "C:\\Users",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData",
    "C:\\Windows",
)

WINDOWS_SYSTEM_PROCS = {
    "system",
    "registry",
    "memcompression",
    "vmmemwsl",
    "smss.exe",
    "csrss.exe",
    "svchost.exe",
    "lsass.exe",
    "services.exe",
    "wininit.exe",
    "winlogon.exe",
}

WINDOWS_DEV_PROCS = {
    "code.exe",
    "idea64.exe",
    "pycharm64.exe",
    "node.exe",
    "python.exe"
}
