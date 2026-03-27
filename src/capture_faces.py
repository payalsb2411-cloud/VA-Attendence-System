import argparse
import csv
from datetime import datetime
from pathlib import Path

import cv2

DEFAULT_SAMPLES = 5
DEFAULT_CAMERA_INDEX = 0


def parse_args():
    parser = argparse.ArgumentParser(description="Capture face images for one person.")
    parser.add_argument(
        "--name",
        required=False,
        help="Person name (e.g. om). If omitted, asks interactively.",
    )
    parser.add_argument(
        "--mobile",
        required=False,
        help="Employee mobile number. If omitted, asks interactively.",
    )
    parser.add_argument(
        "--employee-id",
        required=False,
        help="Employee ID (e.g. EMP001).",
    )
    parser.add_argument(
        "--role",
        required=False,
        help="Employee role (Manager, Co Founder, Employee, Team Leader, Trainee).",
    )
    parser.add_argument(
        "--company-name",
        required=False,
        help="Company name to store with employee.",
    )
    parser.add_argument(
        "--logo-path",
        required=False,
        help="Path to company logo file.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=DEFAULT_SAMPLES,
        help=f"Number of face samples to capture (default: {DEFAULT_SAMPLES}).",
    )
    return parser.parse_args()


def sanitize_name(value):
    return value.strip().lower().replace(" ", "_")


def sanitize_mobile(value):
    return "".join(ch for ch in value if ch.isdigit())


def get_employee_info(args):
    name = args.name.strip() if args.name else input("Enter employee name: ").strip()
    while not name:
        name = input("Name cannot be empty. Enter employee name: ").strip()

    mobile = (
        args.mobile.strip() if args.mobile else input("Enter mobile number: ").strip()
    )
    mobile = sanitize_mobile(mobile)
    while len(mobile) < 10:
        mobile = sanitize_mobile(input("Enter valid mobile number (min 10 digits): "))

    employee_id = (
        args.employee_id.strip()
        if args.employee_id
        else input("Enter employee ID: ").strip()
    )
    while not employee_id:
        employee_id = input("Employee ID cannot be empty. Enter employee ID: ").strip()

    role = args.role.strip() if args.role else input("Enter role: ").strip()
    while not role:
        role = input("Role cannot be empty. Enter role: ").strip()

    company_name = (
        args.company_name.strip()
        if args.company_name
        else input("Enter company name: ").strip()
    )
    while not company_name:
        company_name = input("Company name cannot be empty. Enter company name: ").strip()

    logo_path = args.logo_path.strip() if args.logo_path else input("Enter logo path: ").strip()

    return name, mobile, employee_id, role, company_name, logo_path


def upsert_employee(name, mobile, employee_id, role, company_name, logo_path):
    employees_file = Path("data") / "employees.csv"
    employees_file.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    if employees_file.exists():
        with employees_file.open("r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    for row in rows:
        existing_mobile = row.get("Mobile", "").strip()
        existing_employee_id = row.get("EmployeeID", "").strip().lower()

        if existing_mobile == mobile:
            raise ValueError(f"Duplicate mobile number not allowed: {mobile}")
        if existing_employee_id == employee_id.strip().lower():
            raise ValueError(f"Duplicate employee ID not allowed: {employee_id}")

    rows.append(
        {
            "Name": name,
            "Mobile": mobile,
            "EmployeeID": employee_id,
            "Role": role,
            "CompanyName": company_name,
            "LogoPath": logo_path,
        }
    )

    with employees_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Name",
                "Mobile",
                "EmployeeID",
                "Role",
                "CompanyName",
                "LogoPath",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def append_capture_log(name, mobile, folder_name, captured_count):
    log_file = Path("data") / "capture_log.csv"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_exists = log_file.exists()

    with log_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Name",
                "Mobile",
                "Folder",
                "SamplesCaptured",
                "CapturedAt",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "Name": name,
                "Mobile": mobile,
                "Folder": folder_name,
                "SamplesCaptured": captured_count,
                "CapturedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )


def main():
    args = parse_args()
    name, mobile, employee_id, role, company_name, logo_path = get_employee_info(args)
    folder_name = f"{sanitize_name(name)}_{mobile}"
    person_dir = Path("data") / folder_name
    person_dir.mkdir(parents=True, exist_ok=True)
    upsert_employee(name, mobile, employee_id, role, company_name, logo_path)
    print(f"Capturing for: {name} ({mobile})")

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    cap = cv2.VideoCapture(DEFAULT_CAMERA_INDEX)

    if not cap.isOpened():
        raise RuntimeError("Could not open camera. Check webcam permissions/index.")

    count = 0
    print("Press 'q' to quit early.")

    while count < args.samples:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        for (x, y, w, h) in faces:
            face = gray[y : y + h, x : x + w]
            file_path = person_dir / f"{folder_name}_{count:03d}.jpg"
            cv2.imwrite(str(file_path), face)
            count += 1

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 0), 2)
            cv2.putText(
                frame,
                f"Captured: {count}/{args.samples}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            break

        cv2.imshow("Capture Faces", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    append_capture_log(name, mobile, folder_name, count)
    print(f"Saved {count} samples to {person_dir}")
    print("Employee list CSV: data/employees.csv")
    print("Capture log CSV: data/capture_log.csv")


if __name__ == "__main__":
    main()
