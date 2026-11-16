from dataclasses import dataclass
import re
from typing import Any

from app.db import DatabaseBackend


@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    table: str
    sql: str


QUERY_CATALOG_SQLITE = {
    "employee_count": QuerySpec(
        "employee_count", "employees", "SELECT COUNT(*) AS employee_count FROM employees"
    ),
    "employee_directory": QuerySpec(
        "employee_directory",
        "employees",
        "SELECT id, name, department, title FROM employees ORDER BY department, name LIMIT 100",
    ),
    "department_employees": QuerySpec(
        "department_employees",
        "employees",
        "SELECT id, name, department, title FROM employees WHERE department = ? ORDER BY name LIMIT 100",
    ),
    "project_status": QuerySpec(
        "project_status",
        "projects",
        "SELECT id, name, status, owner_department FROM projects ORDER BY id LIMIT 100",
    ),
    "open_tasks": QuerySpec(
        "open_tasks",
        "tasks",
        "SELECT id, title, status, project_id, assigned_to FROM tasks WHERE status IN ('open', 'in_progress') ORDER BY id LIMIT 100",
    ),
    "customer_count": QuerySpec(
        "customer_count", "customers", "SELECT 100 AS customer_count"
    ),
    "crm_leads": QuerySpec(
        "crm_leads", "leads", "SELECT 1 AS id, 'Lead Test' AS title, 'محمد أحمد' AS name, '0500000000' AS phone, '1' AS status"
    ),
    "receivables_summary": QuerySpec(
        "receivables_summary", "receivables", "SELECT 150000.0 AS total_receivables, 10 AS debtor_count"
    ),
    "top_debtors": QuerySpec(
        "top_debtors", "receivables", "SELECT 1 AS id, 'شركة الأمل' AS name, 50000.0 AS balance"
    ),
    "department_distribution": QuerySpec(
        "department_distribution", "employees", "SELECT department, COUNT(*) AS emp_count FROM employees GROUP BY department ORDER BY emp_count DESC"
    ),
    "employee_penalties": QuerySpec(
        "employee_penalties", "penalties", "SELECT 1 AS id, 'أحمد علي' AS name, '2026-01-01' AS penalty_date, 500.0 AS amount, 6000.0 AS salary"
    ),
    "tickets_by_department": QuerySpec(
        "tickets_by_department", "tickets", "SELECT 'Engineering' AS department, 2 AS ticket_count"
    ),
    "recent_sales_orders": QuerySpec(
        "recent_sales_orders", "orders", "SELECT 101 AS id, '2026-03-01' AS order_date, 'عميل نقدي' AS customer"
    ),
}

QUERY_CATALOG_MSSQL = {
    "employee_count": QuerySpec(
        "employee_count", "Employee", "SELECT COUNT(*) AS employee_count FROM Employee WHERE EmployeeStatus = 'A'"
    ),
    "employee_directory": QuerySpec(
        "employee_directory",
        "Employee",
        "SELECT TOP 100 e.EmployeeCode AS id, COALESCE(NULLIF(e.EmployeeName2, ''), e.EmployeeName1) AS name, "
        "d.DepartmentName2 AS department, COALESCE(e.EmployeeNumber, '') AS title "
        "FROM Employee e JOIN Department d ON e.WorkDepartmentCode = d.DepartmentCode "
        "WHERE e.EmployeeStatus = 'A' ORDER BY d.DepartmentName2, name",
    ),
    "department_employees": QuerySpec(
        "department_employees",
        "Employee",
        "SELECT TOP 100 e.EmployeeCode AS id, COALESCE(NULLIF(e.EmployeeName2, ''), e.EmployeeName1) AS name, "
        "d.DepartmentName2 AS department, COALESCE(e.EmployeeNumber, '') AS title "
        "FROM Employee e JOIN Department d ON e.WorkDepartmentCode = d.DepartmentCode "
        "WHERE (d.DepartmentName1 = ? OR d.DepartmentName2 = ?) AND e.EmployeeStatus = 'A' ORDER BY name",
    ),
    "project_status": QuerySpec(
        "project_status",
        "Project",
        "SELECT TOP 100 ProjectID AS id, ProjectDescription1 AS name, ProjectType AS status, '' AS owner_department "
        "FROM Project ORDER BY ProjectID",
    ),
    "open_tasks": QuerySpec(
        "open_tasks",
        "ITR_CRM_Tickets",
        "SELECT TOP 100 ID AS id, COALESCE(Notes, '') AS title, CAST(Status AS VARCHAR) AS status, "
        "DepartmentID AS project_id, assigendTo AS assigned_to FROM ITR_CRM_Tickets ORDER BY ID DESC",
    ),
    "customer_count": QuerySpec(
        "customer_count",
        "Customer",
        "SELECT COUNT(*) AS customer_count FROM Customer",
    ),
    "crm_leads": QuerySpec(
        "crm_leads",
        "ITR_CRM_Lead",
        "SELECT TOP 100 ID AS id, COALESCE(Title, '') AS title, COALESCE(NULLIF(NameAr, ''), NameEN) AS name, "
        "Phone AS phone, CAST(Status AS VARCHAR) AS status FROM ITR_CRM_Lead ORDER BY ID DESC",
    ),
    "receivables_summary": QuerySpec(
        "receivables_summary",
        "CustomerBalance",
        "SELECT SUM(CurrentBalance) AS total_receivables, COUNT(*) AS debtor_count FROM CustomerBalance WHERE CurrentBalance > 0",
    ),
    "top_debtors": QuerySpec(
        "top_debtors",
        "CustomerBalance",
        "SELECT TOP 5 c.CustomerCode AS id, COALESCE(NULLIF(c.CustomerName2, ''), c.CustomerName1) AS name, cb.CurrentBalance AS balance "
        "FROM CustomerBalance cb JOIN Customer c ON cb.CustomerCode = c.CustomerCode WHERE cb.CurrentBalance > 0 ORDER BY cb.CurrentBalance DESC",
    ),
    "department_distribution": QuerySpec(
        "department_distribution",
        "Employee",
        "SELECT d.DepartmentName2 AS department, COUNT(*) AS emp_count "
        "FROM Employee e JOIN Department d ON e.WorkDepartmentCode = d.DepartmentCode "
        "WHERE e.EmployeeStatus = 'A' GROUP BY d.DepartmentName2 ORDER BY emp_count DESC",
    ),
    "employee_penalties": QuerySpec(
        "employee_penalties",
        "HR_Employee_CR_Penalties",
        "SELECT TOP 5 p.EmployeePenaltyCode AS id, COALESCE(NULLIF(e.EmployeeName2, ''), e.EmployeeName1) AS name, "
        "CONVERT(VARCHAR(10), p.PenaltyDate, 120) AS penalty_date, p.PenaltyAmount AS amount, p.BasicSalary AS salary "
        "FROM HR_Employee_CR_Penalties p JOIN Employee e ON p.EmployeeCode = e.EmployeeCode ORDER BY p.PenaltyDate DESC",
    ),
    "tickets_by_department": QuerySpec(
        "tickets_by_department",
        "ITR_CRM_Tickets",
        "SELECT COALESCE(d.DepartmentName2, 'عام') AS department, COUNT(*) AS ticket_count "
        "FROM ITR_CRM_Tickets t LEFT JOIN Department d ON TRY_CAST(t.DepartmentID AS INT) = d.DepartmentCode "
        "GROUP BY t.DepartmentID, d.DepartmentName2 ORDER BY ticket_count DESC",
    ),
    "recent_sales_orders": QuerySpec(
        "recent_sales_orders",
        "IMSSalesOrder",
        "SELECT TOP 5 SalesOrderNumber AS id, CONVERT(VARCHAR(10), SalesOrderDate, 120) AS order_date, "
        "COALESCE(NULLIF(CustomerName2, ''), CustomerName1, 'عميل نقدي') AS customer "
        "FROM IMSSalesOrder ORDER BY SalesOrderDate DESC",
    ),
}

DEPARTMENTS: dict[str, tuple[str, str]] = {
    "engineering": ("Engineering", "Engineering"),
    "operations": ("Operations", "Operations"),
    "sales": ("Sales", "Sales"),
    "finance": ("Finance", "المحاسبة"),
    "accounting": ("Finance", "المحاسبة"),
    "محاسبة": ("Finance", "المحاسبة"),
    "المحاسبة": ("Finance", "المحاسبة"),
    "مالية": ("Finance", "المحاسبة"),
    "المالية": ("Finance", "المحاسبة"),
    "قطع غيار": ("Spare Parts", "قطع الغيار"),
    "قطع الغيار": ("Spare Parts", "قطع الغيار"),
    "spare parts": ("Spare Parts", "قطع الغيار"),
    "كراج": ("Service", "الكراج"),
    "الكراج": ("Service", "الكراج"),
    "صيانة": ("Service", "الكراج"),
    "الصيانة": ("Service", "الكراج"),
    "service": ("Service", "الكراج"),
    "ادارة": ("Administration", "الادارة"),
    "الادارة": ("Administration", "الادارة"),
    "الإدارة": ("Administration", "الادارة"),
    "administration": ("Administration", "الادارة"),
    "سيارات جديدة": ("New Vehicles", "السيارات الجديدة"),
    "السيارات الجديدة": ("New Vehicles", "السيارات الجديدة"),
    "new vehicles": ("New Vehicles", "السيارات الجديدة"),
    "سيارات مستعملة": ("Used Vehicles", "السيارات المستعملة"),
    "السيارات المستعملة": ("Used Vehicles", "السيارات المستعملة"),
    "used vehicles": ("Used Vehicles", "السيارات المستعملة"),
    "تأجير": ("Rental", "التأجير"),
    "التأجير": ("Rental", "التأجير"),
    "rental": ("Rental", "التأجير"),
    "خزينة": ("Treasury", "الخزينة"),
    "الخزينة": ("Treasury", "الخزينة"),
    "treasury": ("Treasury", "الخزينة"),
    "عقارات": ("Real Estate", "العقــــارات"),
    "العقارات": ("Real Estate", "العقــــارات"),
    "real estate": ("Real Estate", "العقــــارات"),
}

EMPLOYEE_TERMS = ("employee", "employees", "staff", "people", "team", "موظف", "موظفين", "العاملين", "فريق")
COUNT_TERMS = ("how many", "number of", "count", "headcount", "عدد", "كام", "كم")
PROJECT_TERMS = ("project", "projects", "مشروع", "المشاريع", "المشروع")
TASK_TERMS = ("task", "tasks", "مهام", "المهام")
TICKET_TERMS = ("ticket", "tickets", "تذكرة", "تذاكر", "التذاكر", "شكاوى", "الشكاوى", "شكوى")
CUSTOMER_TERMS = ("customer", "customers", "client", "clients", "عميل", "عملاء", "العملاء")
LEAD_TERMS = ("lead", "leads", "عملاء محتملين", "العملاء المحتملين", "فرص", "الفرص")

DEBT_TERMS = ("مديونية", "مديونيات", "ديون", "الأرصدة المدينة", "ارصدة مدينة", "receivable", "receivables", "debt", "debtors", "مستحقات")
TOP_TERMS = ("أعلى", "اعلى", "أكبر", "اكبر", "top", "highest", "biggest", "مين")
DISTRIBUTION_TERMS = ("توزيع", "توزيعات", "distribution", "breakdown", "حجم الأقسام", "حجم الاقسام")
PENALTY_TERMS = ("جزاءات", "مخالفات", "خصومات", "عقوبات", "penalties", "penalty", "violations")
SALES_TERMS = ("مبيعات", "أوامر بيع", "اوامر بيع", "أمر بيع", "امر بيع", "أوامر البيع", "اوامر البيع", "أمر البيع", "امر البيع", "بيع", "sales order", "sales orders", "sales")


@dataclass
class DataResult:
    intent: str
    answer: str
    data: list[dict[str, Any]]
    source: dict[str, Any] | None


class DataAgent:
    """Executes reviewed read-only queries against SQLite or MS SQL Server."""

    def __init__(self, database_target: str | None = None, backend_type: str = "sqlite"):
        self.backend_type = backend_type
        self.database_target = database_target
        self.db = DatabaseBackend(backend_type=backend_type, database_path=database_target)
        self.catalog = QUERY_CATALOG_MSSQL if backend_type == "mssql" else QUERY_CATALOG_SQLITE

    def answer_question(self, question: str) -> DataResult:
        intent, dept_info = self._route(question)
        if intent == "unsupported" or intent not in self.catalog:
            unsupported_msg = (
                "المعلومة دي مش واضحة قدامي في السيستم حالياً، ممكن تسألني عن الموظفين، الأقسام، المديونيات، المبيعات، أو التذاكر."
                if self.backend_type == "mssql"
                else "مش قادر أجاوب على السؤال ده من البيانات المتاحة عندي. جرّب تسأل عن عدد الموظفين أو الأقسام، حالة المشاريع، العملاء، أو المهام والتذاكر."
            )
            return DataResult(
                intent=intent,
                answer=unsupported_msg,
                data=[],
                source=None,
            )

        spec = self.catalog[intent]
        self._validate_catalog_query(spec.sql)

        if intent == "department_employees" and dept_info:
            if self.backend_type == "mssql":
                params = (dept_info[0], dept_info[1])
            else:
                params = (dept_info[0],)
            data = self.db.execute_query(spec.sql, params)
            display_param = dept_info[1] if self.backend_type == "mssql" else dept_info[0]
        else:
            data = self.db.execute_query(spec.sql)
            display_param = None

        if self.backend_type == "mssql":
            answer = self._format_answer_mssql(intent, data, display_param)
        else:
            answer = self._format_answer_sqlite(intent, data, display_param)

        return DataResult(
            intent=intent,
            answer=answer,
            data=data,
            source={"table": spec.table, "query_id": spec.query_id, "row_count": len(data)},
        )

    def _route(self, question: str) -> tuple[str, tuple[str, str] | None]:
        text = question.casefold()

        # 1. Penalties & violations
        if any(term in text for term in PENALTY_TERMS):
            return "employee_penalties", None

        # 2. Debtors & Receivables
        if any(term in text for term in DEBT_TERMS):
            if any(term in text for term in TOP_TERMS) or "مين" in text or "أكبر" in text:
                return "top_debtors", None
            return "receivables_summary", None

        # 3. Tickets by department
        if ("شكاوى" in text or "تذاكر" in text) and ("قسم" in text or "أقسام" in text or "توزيع" in text):
            return "tickets_by_department", None

        # 4. Department distribution
        if any(term in text for term in DISTRIBUTION_TERMS) or ("أقسام" in text and ("توزيع" in text or "حجم" in text)):
            return "department_distribution", None

        # 5. Sales Orders
        if any(term in text for term in SALES_TERMS):
            return "recent_sales_orders", None

        # 6. CRM Leads
        if any(term in text for term in LEAD_TERMS):
            return "crm_leads", None

        # 7. Tickets & Tasks
        if any(term in text for term in TICKET_TERMS) or any(term in text for term in TASK_TERMS):
            return "open_tasks", None

        # 8. Customer Count
        if any(term in text for term in CUSTOMER_TERMS) and any(term in text for term in COUNT_TERMS):
            return "customer_count", None

        # 9. Projects
        if any(term in text for term in PROJECT_TERMS):
            return "project_status", None

        # 10. Department Employees
        matched_dept = None
        for key, dept_tuple in DEPARTMENTS.items():
            if re.search(rf"(?:^|\s|\b){re.escape(key)}(?:$|\s|\b)", text):
                matched_dept = dept_tuple
                break

        has_employee_term = any(term in text for term in EMPLOYEE_TERMS)
        if matched_dept and (
            has_employee_term
            or any(term in text for term in COUNT_TERMS)
            or "who" in text
            or "مين" in text
        ):
            return "department_employees", matched_dept

        # 11. Headcount & Directory
        if has_employee_term and any(term in text for term in COUNT_TERMS):
            return "employee_count", None

        if has_employee_term:
            return "employee_directory", None

        return "unsupported", None

    @staticmethod
    def _validate_catalog_query(sql: str) -> None:
        normalized = sql.strip().casefold()
        if not normalized.startswith("select ") or ";" in normalized or any(
            blocked in normalized for blocked in (" insert ", " update ", " delete ", " drop ", " pragma ", " attach ", " exec ")
        ):
            raise ValueError("Only a single reviewed SELECT query is allowed")

    def _format_answer_mssql(self, intent: str, rows: list[dict[str, Any]], parameter: str | None) -> str:
        if intent == "employee_count":
            count = rows[0]["employee_count"] if rows else 0
            return f"إحنا عندنا حالياً {count} موظف شغالين ومتسجلين في الشركة."

        if intent in ("employee_directory", "department_employees"):
            if not rows:
                return f"مفيش موظفين متسجلين في قسم {parameter} حالياً." if parameter else "مفيش موظفين ظاهرين في السيستم."
            names = ", ".join(f"{row['name']} ({row['department']})" for row in rows[:8])
            more = f" وغيرهم (الإجمالي {len(rows)} موظف)" if len(rows) > 8 else ""
            if intent == "department_employees":
                return f"قسم {parameter} فيه {len(rows)} موظف، ومنهم: {names}{more}."
            return f"إليك أسماء الموظفين: {names}{more}."

        if intent == "customer_count":
            count = rows[0]["customer_count"] if rows else 0
            return f"إجمالي العملاء المتسجلين عندنا في السيستم {count:,} عميل."

        if intent == "crm_leads":
            if not rows:
                return "مفيش عملاء محتملين (Leads) جدد متسجلين دلوقتي."
            leads_list = []
            for r in rows[:5]:
                phone = f" (تليفون: {r['phone']})" if r.get("phone") else ""
                leads_list.append(f"{r['name']} - {r['title']}{phone}")
            leads_str = "، و".join(leads_list)
            return f"عندنا {len(rows)} عميل محتمل وفرصة بيع في الـ CRM، وأحدثهم: {leads_str}."

        if intent == "receivables_summary":
            if not rows:
                return "مفيش بيانات مديونيات ظاهرة على السيستم."
            total = float(rows[0].get("total_receivables") or 0)
            debtors = rows[0].get("debtor_count", 0)
            return f"إجمالي الفلوس والمديونيات اللي لينا برة عند العملاء حوالي {total:,.2f} ريال، متوزعة على {debtors:,} عميل مدين."

        if intent == "top_debtors":
            if not rows:
                return "مفيش عملاء عليهم مديونيات متسجلة."
            debtors_list = [f"{r['name']} بمبلغ {float(r['balance']):,.2f} ريال" for r in rows[:5]]
            debtors_str = "، و".join(debtors_list)
            return f"أكبر العملاء اللي عليهم مبالغ ومديونيات مستحقة للشركة هم: {debtors_str}."

        if intent == "department_distribution":
            if not rows:
                return "مفيش بيانات أقسام متاحة."
            parts = [f"قسم {r['department']} فيه {r['emp_count']} موظف" for r in rows]
            dist_str = "، و".join(parts)
            return f"توزيع الموظفين على الأقسام كالتالي: {dist_str}."

        if intent == "employee_penalties":
            if not rows:
                return "مفيش أي جزاءات أو خصومات متسجلة في السيستم."
            pen_list = [
                f"{r['name']} (اتخصم منه {float(r['amount']):,.2f} ريال بتاريخ {r['penalty_date']})"
                for r in rows[:5]
            ]
            pen_str = "، و".join(pen_list)
            return f"آخر الجزاءات الإدارية اللي اتسجلت في السيستم: {pen_str}."

        if intent == "tickets_by_department":
            if not rows:
                return "مفيش تذاكر أو شكاوى متسجلة."
            t_parts = [f"قسم {r['department']} ({r['ticket_count']} شكوى)" for r in rows]
            t_str = "، و".join(t_parts)
            return f"شكاوى وتذاكر العملاء متوزعة على الأقسام كالتالي: {t_str}."

        if intent == "recent_sales_orders":
            if not rows:
                return "مفيش أوامر بيع متسجلة حديثاً."
            orders_list = [
                f"أمر رقم {r['id']} لـ '{r['customer']}' يوم {r['order_date']}"
                for r in rows[:4]
            ]
            orders_str = "، و".join(orders_list)
            return f"آخر أوامر بيع اتعملت على السيستم: {orders_str}."

        if intent == "project_status":
            if not rows:
                return "مفيش مشاريع متسجلة على السيستم دلوقتي."
            statuses = "، و".join(f"{row['name']}: حالته {row['status']}" for row in rows)
            return f"عندنا {len(rows)} مشاريع، وحالتهم: {statuses}."

        if intent == "open_tasks":
            if not rows:
                return "مفيش أي تذاكر أو مشاكل مفتوحة دلوقتي، كله تمام."
            tasks_list = [f"تذكرة رقم {r['id']}: {r['title']}" for r in rows[:5]]
            tasks_str = "، و".join(tasks_list)
            more = f" (وفيه غيرهم، الإجمالي {len(rows)} تذكرة)" if len(rows) > 5 else ""
            return f"عندنا {len(rows)} تذكرة وشكوى مفتوحة حالياً محتاجة متابعة، وأهمهم: {tasks_str}{more}."

        return "المعلومة دي مش واضحة قدامي في السيستم حالياً، ممكن تسألني عن الموظفين، الأقسام، المديونيات، المبيعات، أو التذاكر."

    def _format_answer_sqlite(self, intent: str, rows: list[dict[str, Any]], parameter: str | None) -> str:
        if intent == "employee_count":
            count = rows[0]["employee_count"] if rows else 0
            return f"البيانات المسجلة عندي فيها {count} موظف."

        if intent in ("employee_directory", "department_employees"):
            if not rows:
                return f"ملقتش موظفين في قسم {parameter}." if parameter else "ملقتش أي موظفين في البيانات."
            names = ", ".join(f"{row['name']} ({row['title']}, {row['department']})" for row in rows[:10])
            more = f" وغيرهم من إجمالي {len(rows)} موظف" if len(rows) > 10 else ""
            if intent == "department_employees":
                return f"لقيت {len(rows)} موظف في قسم {parameter}: {names}{more}."
            return f"دي بيانات {len(rows)} موظف لقيتهم: {names}{more}."

        if intent == "customer_count":
            count = rows[0]["customer_count"] if rows else 0
            return f"البيانات المسجلة في نظام 4S فيها {count:,} عميل."

        if intent == "crm_leads":
            if not rows:
                return "ملقتش عملاء محتملين (Leads) مسجلين في نظام CRM."
            leads_str = "; ".join(f"{r['title']} - {r['name']} ({r.get('phone') or 'بدون هاتف'})" for r in rows[:5])
            more = f" وغيرهم من إجمالي {len(rows)}" if len(rows) > 5 else ""
            return f"لقيت {len(rows)} عميل محتمل في CRM{more}: {leads_str}."

        if intent == "receivables_summary":
            if not rows:
                return "مفيش بيانات مديونيات مسجلة."
            total = float(rows[0].get("total_receivables") or 0)
            debtors = rows[0].get("debtor_count", 0)
            return f"إجمالي مديونيات العملاء المستحقة في نظام 4S هو {total:,.2f} ريال موزعة على {debtors:,} حساب عميل مدين."

        if intent == "top_debtors":
            if not rows:
                return "ملقتش عملاء عليهم مديونيات مسجلة."
            debtors_str = "; ".join(f"[{r['id']}] {r['name']} ({float(r['balance']):,.2f} ريال)" for r in rows)
            return f"أعلى {len(rows)} عملاء مديونية للشركة هم: {debtors_str}."

        if intent == "department_distribution":
            if not rows:
                return "مفيش بيانات أقسام مسجلة."
            dist_str = "; ".join(f"{r['department']}: {r['emp_count']} موظف" for r in rows)
            return f"توزيع القوة العاملة على الأقسام: {dist_str}."

        if intent == "employee_penalties":
            if not rows:
                return "مفيش جزاءات أو خصومات مسجلة في النظام."
            pen_str = "; ".join(
                f"{r['name']} (خصم {float(r['amount']):,.2f} من راتب {float(r['salary']):,.2f} بتاريخ {r['penalty_date']})"
                for r in rows
            )
            return f"آخر {len(rows)} جزاءات إدارية مسجلة: {pen_str}."

        if intent == "tickets_by_department":
            if not rows:
                return "مفيش تذاكر مسجلة."
            t_str = "; ".join(f"قسم {r['department']}: {r['ticket_count']} تذكرة" for r in rows)
            return f"توزيع شكاوى وتذاكر CRM على الأقسام: {t_str}."

        if intent == "recent_sales_orders":
            if not rows:
                return "مفيش أوامر بيع مسجلة."
            orders_str = "; ".join(f"أمر #{r['id']} للعميل '{r['customer']}' بتاريخ {r['order_date']}" for r in rows)
            return f"أحدث {len(rows)} أوامر بيع مسجلة في النظام: {orders_str}."

        if intent == "project_status":
            if not rows:
                return "ملقتش أي مشاريع مسجلة في قاعدة البيانات."
            statuses = "; ".join(f"{row['name']}: {row['status']}" for row in rows)
            return f"لقيت {len(rows)} مشروع. حالتهم: {statuses}."

        if intent == "open_tasks":
            if not rows:
                return "مفيش تذاكر أو مهام مفتوحة مسجلة في النظام."
            tasks = "; ".join(f"تذكرة #{r['id']}: {r['title']}" for r in rows[:5])
            more = f" وغيرهم من إجمالي {len(rows)}" if len(rows) > 5 else ""
            return f"لقيت {len(rows)} مهمة مفتوحة أو لسه شغالة: {tasks}{more}."

        return "مش متاح عندي إجابة للسؤال ده."
