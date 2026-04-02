import csv
import sys
from pathlib import Path


def get_app_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


ROOT_DIR = get_app_root()
DATA_DIR = ROOT_DIR / "data"
ATTENDANCE_DIR = ROOT_DIR / "attendance"
EMPLOYEES_FILE = DATA_DIR / "employees.csv"


def _clean(value):
    return (value or "").strip()


def load_employees():
    rows = []
    if not EMPLOYEES_FILE.exists():
        return rows

    with EMPLOYEES_FILE.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "Name": _clean(row.get("Name")),
                    "Mobile": _clean(row.get("Mobile")),
                    "EmployeeID": _clean(row.get("EmployeeID")),
                    "Role": _clean(row.get("Role")),
                    "CompanyName": _clean(row.get("CompanyName")),
                    "LogoPath": _clean(row.get("LogoPath")),
                }
            )

    return rows


def load_attendance_records():
    records = []
    if not ATTENDANCE_DIR.exists():
        return records

    for file_path in sorted(ATTENDANCE_DIR.glob("attendance_*.csv")):
        with file_path.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if not any((value or "").strip() for value in row.values()):
                    continue

                records.append(
                    {
                        "Name": _clean(row.get("Name")),
                        "Date": _clean(row.get("Date")),
                        "CheckIn": _clean(row.get("CheckIn") or row.get("Time")),
                        "CheckOut": _clean(row.get("CheckOut")),
                        "CheckInLocation": _clean(row.get("CheckInLocation")),
                        "CheckOutLocation": _clean(row.get("CheckOutLocation")),
                        "WorkHours": _clean(row.get("WorkHours")),
                        "SourceFile": file_path.name,
                    }
                )

    records.sort(key=lambda row: (row["Date"], row["CheckIn"], row["Name"]))
    return records
