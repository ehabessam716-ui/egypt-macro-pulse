"""Write ops/windows/*.xml + ops/cron.txt for the SPEC §10 schedule and (on Windows) register them.

  python scripts/install_schedule.py            # write files + register with schtasks
  python scripts/install_schedule.py --write    # only write files
  python scripts/install_schedule.py --remove   # unregister the tasks

Times are Africa/Cairo. This machine's time zone must be Egypt Standard Time for the Windows tasks to
fire at Cairo times (checked below). Tasks run as the current user, only while logged on (no password stored).
"""
from __future__ import annotations

import getpass
import os
import platform
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops"
WIN = OPS / "windows"
PY_WIN = ROOT / ".venv" / "Scripts" / "pythonw.exe"  # no console window
FOLDER = "EgyptMacroPulse"
DAYS = {"SUN": "Sunday", "MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday", "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday"}

# name, job, triggers: ("weekly", [days], "HH:MM") | ("daily", None, "HH:MM") | ("monthly", day, "HH:MM")
TASKS = [
    ("daily_0930", "daily", [("weekly", ["SUN", "MON", "TUE", "WED", "THU"], "09:30")]),
    ("daily_1830", "daily", [("weekly", ["SUN", "MON", "TUE", "WED", "THU"], "18:30")]),
    ("global_2330", "global", [("weekly", ["MON", "TUE", "WED", "THU", "FRI"], "23:30")]),
    ("weekly_thu2000", "weekly", [("weekly", ["THU"], "20:00")]),
    ("gpr_mon1200_and_2nd", "gpr", [("weekly", ["MON"], "12:00"), ("monthly", 2, "12:00")]),
    ("calendar_0700", "calendar", [("daily", None, "07:00")]),
    ("server_at_logon", "serve", [("logon", None, None)]),
]
CRON_DOW = {"SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6}


def trigger_xml(kind, arg, hhmm) -> str:
    if kind == "logon":
        return f"<LogonTrigger><Enabled>true</Enabled><UserId>{escape(_user())}</UserId><Delay>PT30S</Delay></LogonTrigger>"
    start = f"2026-10-18T{hhmm}:00"
    if kind == "daily":
        sched = "<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>"
    elif kind == "weekly":
        days = "".join(f"<{DAYS[d]} />" for d in arg)
        sched = f"<ScheduleByWeek><DaysOfWeek>{days}</DaysOfWeek><WeeksInterval>1</WeeksInterval></ScheduleByWeek>"
    else:
        months = "".join(f"<{m} />" for m in ["January", "February", "March", "April", "May", "June", "July", "August",
                                              "September", "October", "November", "December"])
        sched = f"<ScheduleByMonth><DaysOfMonth><Day>{arg}</Day></DaysOfMonth><Months>{months}</Months></ScheduleByMonth>"
    return f"<CalendarTrigger><StartBoundary>{start}</StartBoundary><Enabled>true</Enabled>{sched}</CalendarTrigger>"


def _user() -> str:
    return os.environ.get("USERDOMAIN", "") + "\\" + getpass.getuser() if os.name == "nt" else getpass.getuser()


def task_xml(name: str, job: str, triggers, user: str) -> str:
    trig = "".join(trigger_xml(*t) for t in triggers)
    args = "-m pulse.cli serve" if job == "serve" else f"-m pulse.cli run --job {job}"
    limit = "PT0S" if job == "serve" else "PT2H"
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Egypt Macro Pulse — pulse run --job {job} (Africa/Cairo schedule, SPEC §10)</Description><URI>\\{FOLDER}\\{name}</URI></RegistrationInfo>
  <Triggers>{trig}</Triggers>
  <Principals><Principal id="Author"><UserId>{escape(user)}</UserId><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <ExecutionTimeLimit>{limit}</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec><Command>{escape(str(PY_WIN))}</Command><Arguments>{args}</Arguments><WorkingDirectory>{escape(str(ROOT))}</WorkingDirectory></Exec>
  </Actions>
</Task>
"""


def cron_lines() -> list[str]:
    root = ROOT.as_posix() if os.name != "nt" else "/path/to/Economic Horizon"
    py = f"{root}/.venv/bin/python"
    lines = ["# Egypt Macro Pulse — crontab (times are Africa/Cairo; CRON_TZ needs cronie/systemd-cron)",
             "# Generated on Windows: replace /path/to/Economic Horizon with the project path on macOS/Linux.",
             "CRON_TZ=Africa/Cairo"]
    for name, job, triggers in TASKS:
        if job == "serve":
            lines.append(f'@reboot cd "{root}" && "{py}" -m pulse.cli serve >> "{root}/logs/serve.log" 2>&1  # {name}')
            continue
        for kind, arg, hhmm in triggers:
            h, m = map(int, hhmm.split(":"))
            if kind == "daily":
                spec = f"{m} {h} * * *"
            elif kind == "weekly":
                spec = f"{m} {h} * * {','.join(str(CRON_DOW[d]) for d in arg)}"
            else:
                spec = f"{m} {h} {arg} * *"
            lines.append(f'{spec} cd "{root}" && "{py}" -m pulse.cli run --job {job} >> "{root}/logs/cron.log" 2>&1  # {name}')
    return lines


def write_files(user: str) -> list[Path]:
    WIN.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, job, triggers in TASKS:
        p = WIN / f"{name}.xml"
        p.write_text(task_xml(name, job, triggers, user), encoding="utf-16")
        paths.append(p)
    (OPS / "cron.txt").write_text("\n".join(cron_lines()) + "\n", encoding="utf-8")
    return paths


def windows_tz() -> str:
    try:
        return subprocess.run(["tzutil", "/g"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return "?"


def main(argv: list[str]) -> int:
    user = os.environ.get("USERDOMAIN", "") + "\\" + getpass.getuser() if os.name == "nt" else getpass.getuser()
    if "--remove" in argv:
        for name, _, _ in TASKS:
            subprocess.run(["schtasks", "/Delete", "/TN", f"\\{FOLDER}\\{name}", "/F"])
        return 0
    paths = write_files(user)
    print(f"wrote {len(paths)} Task Scheduler XML files to {WIN} and {OPS / 'cron.txt'}")
    if "--write" in argv:
        return 0
    if platform.system() != "Windows":
        print("Not Windows: install with  (crontab -l; cat ops/cron.txt) | crontab -")
        return 0
    tz = windows_tz()
    if tz != "Egypt Standard Time":
        print(f"WARNING: machine time zone is {tz!r}, not Egypt Standard Time — tasks fire at local clock times.")
    rc = 0
    for p, (name, _, _) in zip(paths, TASKS):
        r = subprocess.run(["schtasks", "/Create", "/TN", f"\\{FOLDER}\\{name}", "/XML", str(p), "/F"],
                           capture_output=True, text=True)
        print(f"{name}: {(r.stdout or r.stderr).strip()}")
        rc |= r.returncode
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
