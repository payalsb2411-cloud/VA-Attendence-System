import threading
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from data_store import ROOT_DIR, load_attendance_records, load_employees
from capture_faces import capture_employee
from mark_attendance import start_attendance as run_attendance
from train_model import train_faces


DEFAULT_COMPANY_NAME = "Vickhardth Automation"
DEFAULT_SAMPLES = "5"
ROLES = ["Manager", "Co Founder", "Employee", "Team Leader", "Trainee"]
ADMIN_ROLES = {"Manager", "Co Founder"}
DEFAULT_LOGO_PATH = ROOT_DIR / "assets" / "company_logo.png"


class AttendanceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Vickhardth Automation - Employee Access Portal")
        self.root.geometry("1220x820")
        self.root.configure(bg="#0f172a")
        self.is_busy = False
        self.logo_image = None

        self.name_var = tk.StringVar()
        self.mobile_var = tk.StringVar()
        self.employee_id_var = tk.StringVar()
        self.registration_role_var = tk.StringVar(value=ROLES[2])
        self.company_var = tk.StringVar(value=DEFAULT_COMPANY_NAME)
        self.logo_var = tk.StringVar(value=str(DEFAULT_LOGO_PATH) if DEFAULT_LOGO_PATH.exists() else "")
        self.samples_var = tk.StringVar(value=DEFAULT_SAMPLES)
        self.viewer_role_var = tk.StringVar(value=ROLES[0])
        self.viewer_query_var = tk.StringVar()

        self.total_employees_var = tk.StringVar(value="0")
        self.visible_employees_var = tk.StringVar(value="0")
        self.visible_attendance_var = tk.StringVar(value="0")
        self.access_scope_var = tk.StringVar(value="Full access")
        self.hint_var = tk.StringVar(value="")

        self._build_ui()
        self.viewer_role_var.trace_add("write", lambda *_: self.refresh_dashboard())
        self.viewer_query_var.trace_add("write", lambda *_: self.refresh_dashboard())
        self.refresh_dashboard()

    def _build_ui(self):
        self._build_header()
        self._build_body()

    def _build_header(self):
        header = tk.Frame(self.root, bg="#111827", padx=20, pady=16)
        header.pack(fill="x", padx=16, pady=(16, 10))

        brand = tk.Frame(header, bg="#111827")
        brand.pack(side="left", fill="x", expand=True)

        tk.Label(
            brand,
            text=DEFAULT_COMPANY_NAME,
            fg="#f8fafc",
            bg="#111827",
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand,
            text="FACE RECOGNITION ATTENDANCE WITH ROLE-AWARE EMPLOYEE ACCESS",
            fg="#93c5fd",
            bg="#111827",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(4, 0))

        self._render_logo(header)

    def _build_body(self):
        body = tk.Frame(self.root, bg="#0f172a")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        notebook = ttk.Notebook(body)
        notebook.pack(fill="both", expand=True)

        self.register_tab = tk.Frame(notebook, bg="#0f172a")
        self.dashboard_tab = tk.Frame(notebook, bg="#0f172a")
        self.activity_tab = tk.Frame(notebook, bg="#0f172a")

        notebook.add(self.register_tab, text="Register")
        notebook.add(self.dashboard_tab, text="Dashboard")
        notebook.add(self.activity_tab, text="Activity")

        self._build_register_tab()
        self._build_dashboard_tab()
        self._build_activity_tab()

    def _build_register_tab(self):
        container = tk.Frame(self.register_tab, bg="#0f172a", padx=18, pady=18)
        container.pack(fill="both", expand=True)

        form = tk.Frame(container, bg="#111827", padx=18, pady=18)
        form.pack(side="left", fill="y", padx=(0, 12))

        tk.Label(
            form,
            text="Employee Registration",
            bg="#111827",
            fg="#f8fafc",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self._field(form, "Employee Name", self.name_var, 1)
        self._field(form, "Mobile Number", self.mobile_var, 2)
        self._field(form, "Employee ID", self.employee_id_var, 3)

        tk.Label(form, text="Role", bg="#111827", fg="#cbd5e1", font=("Segoe UI", 10)).grid(
            row=4, column=0, sticky="w", pady=6
        )
        ttk.Combobox(
            form,
            textvariable=self.registration_role_var,
            values=ROLES,
            state="readonly",
            width=27,
        ).grid(row=4, column=1, sticky="w", pady=6)

        self._field(form, "Company Name", self.company_var, 5)
        self._field(form, "Logo Path", self.logo_var, 6)
        self._field(form, "Face Samples", self.samples_var, 7)

        button_row = tk.Frame(form, bg="#111827")
        button_row.grid(row=8, column=0, columnspan=2, sticky="w", pady=(18, 0))

        self.capture_btn = tk.Button(
            button_row,
            text="Register & Capture",
            command=self.capture_employee,
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=8,
        )
        self.capture_btn.pack(side="left", padx=(0, 10))

        self.train_btn = tk.Button(
            button_row,
            text="Train Model",
            command=self.train_model,
            bg="#7c3aed",
            fg="white",
            activebackground="#6d28d9",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=8,
        )
        self.train_btn.pack(side="left", padx=(0, 10))

        self.attendance_btn = tk.Button(
            button_row,
            text="Start Attendance",
            command=self.start_attendance,
            bg="#059669",
            fg="white",
            activebackground="#047857",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=8,
        )
        self.attendance_btn.pack(side="left")

        info = tk.Frame(container, bg="#111827", padx=18, pady=18)
        info.pack(side="left", fill="both", expand=True)

        tk.Label(
            info,
            text="How it works",
            bg="#111827",
            fg="#f8fafc",
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")

        notes = (
            "1. Register an employee once with name, mobile, employee ID, and role.\n"
            "2. Capture face samples from the webcam.\n"
            "3. Train the model.\n"
            "4. Start attendance to mark IN/OUT.\n\n"
            "Manager and Co Founder can view every employee and every attendance record\n"
            "from the Dashboard tab. Other roles can filter to their own record."
        )
        tk.Label(
            info,
            text=notes,
            bg="#111827",
            fg="#cbd5e1",
            justify="left",
            anchor="nw",
            font=("Segoe UI", 11),
            wraplength=520,
        ).pack(anchor="w", pady=(12, 0), fill="x")

        self._stat_card(info, "Current access", self.access_scope_var, "#1d4ed8")

        tk.Label(
            info,
            text="Tip: leave Logo Path empty if you do not have a company logo file.",
            bg="#111827",
            fg="#93c5fd",
            font=("Segoe UI", 10, "italic"),
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(18, 0))

    def _build_dashboard_tab(self):
        container = tk.Frame(self.dashboard_tab, bg="#0f172a", padx=18, pady=18)
        container.pack(fill="both", expand=True)

        controls = tk.Frame(container, bg="#111827", padx=14, pady=14)
        controls.pack(fill="x")

        tk.Label(controls, text="Viewer role", bg="#111827", fg="#cbd5e1").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Combobox(
            controls,
            textvariable=self.viewer_role_var,
            values=ROLES,
            state="readonly",
            width=18,
        ).grid(row=0, column=1, sticky="w", padx=(8, 18))

        tk.Label(controls, text="Search employee", bg="#111827", fg="#cbd5e1").grid(
            row=0, column=2, sticky="w"
        )
        tk.Entry(
            controls,
            textvariable=self.viewer_query_var,
            width=34,
            bg="#0b1220",
            fg="#f8fafc",
            insertbackground="#f8fafc",
            relief="flat",
        ).grid(row=0, column=3, sticky="w", padx=(8, 18))

        self.refresh_btn = tk.Button(
            controls,
            text="Refresh",
            command=self.refresh_dashboard,
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=7,
        )
        self.refresh_btn.grid(row=0, column=4, sticky="w")

        tk.Label(
            controls,
            textvariable=self.hint_var,
            bg="#111827",
            fg="#93c5fd",
            anchor="w",
            justify="left",
            wraplength=1080,
        ).grid(row=1, column=0, columnspan=5, sticky="w", pady=(10, 0))

        stats = tk.Frame(container, bg="#0f172a")
        stats.pack(fill="x", pady=(14, 12))

        self._stat_card(stats, "Employees in view", self.visible_employees_var, "#0f766e")
        self._stat_card(stats, "Attendance rows", self.visible_attendance_var, "#7c3aed")
        self._stat_card(stats, "Total employees", self.total_employees_var, "#b45309")

        employee_panel = tk.Frame(container, bg="#111827", padx=12, pady=12)
        employee_panel.pack(fill="both", expand=True, pady=(0, 12))
        tk.Label(
            employee_panel,
            text="Employees",
            bg="#111827",
            fg="#f8fafc",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.employee_tree = self._build_tree(
            employee_panel,
            ["Name", "Mobile", "EmployeeID", "Role", "CompanyName"],
            {"Name": 180, "Mobile": 120, "EmployeeID": 140, "Role": 140, "CompanyName": 220},
        )

        attendance_panel = tk.Frame(container, bg="#111827", padx=12, pady=12)
        attendance_panel.pack(fill="both", expand=True)
        tk.Label(
            attendance_panel,
            text="Attendance",
            bg="#111827",
            fg="#f8fafc",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.attendance_tree = self._build_tree(
            attendance_panel,
            ["Date", "Name", "CheckIn", "CheckOut", "WorkHours", "SourceFile"],
            {"Date": 100, "Name": 170, "CheckIn": 100, "CheckOut": 100, "WorkHours": 90, "SourceFile": 180},
        )

    def _build_activity_tab(self):
        container = tk.Frame(self.activity_tab, bg="#0f172a", padx=18, pady=18)
        container.pack(fill="both", expand=True)

        card = tk.Frame(container, bg="#111827", padx=12, pady=12)
        card.pack(fill="both", expand=True)

        tk.Label(
            card,
            text="System Activity",
            bg="#111827",
            fg="#f8fafc",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        self.log_text = tk.Text(
            card,
            wrap="word",
            bg="#020617",
            fg="#e2e8f0",
            insertbackground="#e2e8f0",
            relief="flat",
            font=("Consolas", 10),
        )
        self.log_text.pack(fill="both", expand=True)
        self._log("Ready. Use Register to enroll people, Dashboard to review data, and Activity to watch command output.")

    def _render_logo(self, parent):
        logo_path = Path(self.logo_var.get().strip() or DEFAULT_LOGO_PATH)
        if logo_path.exists():
            try:
                image = tk.PhotoImage(file=str(logo_path))
                max_w = 76
                max_h = 76
                x_factor = max(1, (image.width() + max_w - 1) // max_w)
                y_factor = max(1, (image.height() + max_h - 1) // max_h)
                image = image.subsample(max(x_factor, y_factor), max(x_factor, y_factor))
                self.logo_image = image
                tk.Label(parent, image=self.logo_image, bg="#111827").pack(anchor="e")
                return
            except Exception:
                pass

        tk.Label(
            parent,
            text="VA",
            fg="#93c5fd",
            bg="#111827",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="e")

    def _field(self, parent, label, variable, row):
        tk.Label(parent, text=label, bg="#111827", fg="#cbd5e1", font=("Segoe UI", 10)).grid(
            row=row, column=0, sticky="w", pady=6
        )
        tk.Entry(
            parent,
            textvariable=variable,
            width=30,
            bg="#0b1220",
            fg="#f8fafc",
            insertbackground="#f8fafc",
            relief="flat",
        ).grid(row=row, column=1, sticky="w", pady=6)

    def _build_tree(self, parent, columns, widths):
        wrapper = tk.Frame(parent, bg="#111827")
        wrapper.pack(fill="both", expand=True)

        tree = ttk.Treeview(wrapper, columns=columns, show="headings", height=9)
        tree.pack(side="left", fill="both", expand=True)

        y_scroll = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        x_scroll.pack(fill="x", pady=(6, 0))
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=widths.get(column, 120), anchor="w")
        return tree

    def _stat_card(self, parent, title, value_var, accent):
        card = tk.Frame(parent, bg=accent, padx=14, pady=12)
        card.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(card, text=title, bg=accent, fg="#eff6ff", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(card, textvariable=value_var, bg=accent, fg="white", font=("Segoe UI", 24, "bold")).pack(anchor="w", pady=(4, 0))

    def _set_busy(self, busy):
        self.is_busy = busy
        state = "disabled" if busy else "normal"
        self.capture_btn.config(state=state)
        self.train_btn.config(state=state)
        self.attendance_btn.config(state=state)
        self.refresh_btn.config(state=state)

    def _log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def _run_task(self, task, title, on_success=None):
        if self.is_busy:
            messagebox.showinfo("Please wait", "Another task is already running.")
            return

        class _LogWriter:
            def __init__(self, emit):
                self.emit = emit
                self.buffer = ""

            def write(self, text):
                if not text:
                    return
                self.buffer += text
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n", 1)
                    line = line.rstrip("\r")
                    if line:
                        self.emit(line)

            def flush(self):
                if self.buffer.strip():
                    self.emit(self.buffer.rstrip("\r"))
                self.buffer = ""

        def worker():
            succeeded = False
            self.root.after(0, lambda: self._set_busy(True))
            self.root.after(0, lambda: self._log(f"\n[{title}]"))
            try:
                writer = _LogWriter(lambda line: self.root.after(0, lambda l=line: self._log(l)))
                with redirect_stdout(writer), redirect_stderr(writer):
                    task()
                succeeded = True
                self.root.after(0, lambda: self._log(f"{title} completed successfully."))
            except Exception as exc:
                self.root.after(0, lambda: self._log(f"Error: {exc}"))
            finally:
                self.root.after(0, lambda: self._set_busy(False))
                if succeeded and on_success:
                    self.root.after(100, on_success)

        threading.Thread(target=worker, daemon=True).start()

    def _normalize(self, value):
        return " ".join((value or "").strip().lower().split())

    def _matches_query(self, row, query):
        if not query:
            return True
        query = self._normalize(query)
        haystack = self._normalize(" ".join(str(value or "") for value in row.values()))
        return query in haystack

    def _clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def _populate_tree(self, tree, rows, columns):
        self._clear_tree(tree)
        for row in rows:
            tree.insert("", "end", values=[row.get(column, "") for column in columns])

    def _current_view_scope(self):
        role = self.viewer_role_var.get().strip()
        if role in ADMIN_ROLES:
            return "Full access"
        if self.viewer_query_var.get().strip():
            return "Filtered personal view"
        return "Enter your name, mobile, or employee ID to see your record"

    def refresh_dashboard(self):
        employees = load_employees()
        attendance = load_attendance_records()
        role = self.viewer_role_var.get().strip()
        query = self.viewer_query_var.get().strip()

        visible_employees = employees
        visible_attendance = attendance
        if role not in ADMIN_ROLES:
            if query:
                visible_employees = [row for row in employees if self._matches_query(row, query)]
                visible_attendance = [row for row in attendance if self._matches_query(row, query)]
            else:
                visible_employees = []
                visible_attendance = []

        self.total_employees_var.set(str(len(employees)))
        self.visible_employees_var.set(str(len(visible_employees)))
        self.visible_attendance_var.set(str(len(visible_attendance)))
        self.access_scope_var.set("Full access" if role in ADMIN_ROLES else "Filtered access")
        self.hint_var.set(self._current_view_scope() + ". Manager and Co Founder can see every employee row and every attendance entry.")

        self._populate_tree(self.employee_tree, visible_employees, ["Name", "Mobile", "EmployeeID", "Role", "CompanyName"])
        self._populate_tree(self.attendance_tree, visible_attendance, ["Date", "Name", "CheckIn", "CheckOut", "WorkHours", "SourceFile"])

    def capture_employee(self):
        name = self.name_var.get().strip()
        mobile = self.mobile_var.get().strip()
        employee_id = self.employee_id_var.get().strip()
        role = self.registration_role_var.get().strip()
        company_name = self.company_var.get().strip() or DEFAULT_COMPANY_NAME
        logo_path = self.logo_var.get().strip()
        samples = self.samples_var.get().strip() or DEFAULT_SAMPLES

        if not name:
            messagebox.showerror("Validation", "Please enter employee name.")
            return
        if not mobile.isdigit() or len(mobile) < 10:
            messagebox.showerror("Validation", "Please enter a valid mobile number.")
            return
        if not employee_id:
            messagebox.showerror("Validation", "Please enter employee ID.")
            return
        if not role:
            messagebox.showerror("Validation", "Please select a role.")
            return
        if not samples.isdigit() or int(samples) < 1:
            messagebox.showerror("Validation", "Face samples must be a number greater than zero.")
            return
        if logo_path and not Path(logo_path).exists():
            logo_path = ""

        self._run_task(
            lambda: capture_employee(
                name,
                mobile,
                employee_id,
                role,
                company_name,
                logo_path,
                samples=int(samples),
            ),
            "Capture Faces",
            on_success=self.train_model,
        )

    def train_model(self):
        self._run_task(train_faces, "Train Model", on_success=self.refresh_dashboard)

    def start_attendance(self):
        self._run_task(run_attendance, "Start Attendance", on_success=self.refresh_dashboard)


def main():
    root = tk.Tk()
    AttendanceGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
