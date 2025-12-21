import math
from datetime import datetime, timedelta
import hashlib
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from app.models import Room, Service, TypeRoom, UserRole, User
from app import app, db, dao
from flask_login import current_user, logout_user
from flask import redirect, request


class LogoutView(BaseView):
    @expose("/")
    def index(self):
        logout_user()
        return redirect("/admin")

    def is_accessible(self) -> bool:
        return current_user.is_authenticated


class AdminView(ModelView):
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.role in [UserRole.ADMIN, UserRole.STAFF]


class RoomView(AdminView):
    column_list = ["name", 'image', 'typeid', 'capacity', 'status']
    column_searchable_list = ["name"]
    column_filters = ["name", 'capacity']
    edit_modal = True
    can_export = True
    column_editable_list = ["capacity"]
    page_size = 6


class ServiceView(AdminView):
    column_list = ["name", 'price', 'unit', 'inventory_quantity', 'status_service']
    column_searchable_list = ["name"]
    edit_modal = True
    can_export = True
    page_size = 6


class TypeRoomView(AdminView):
    column_list = ["name", 'price']
    edit_modal = True
    column_editable_list = ['price']


class MyAdminIndexView(AdminIndexView):

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        # Lấy dữ liệu từ form (Dạng chuỗi)
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        report_type = request.form.get("report_type")

        day_report = []
        week_report = []
        trend_data = []

        # Biến để hiển thị lại trên form (tránh bị reset form)
        start_date = start_date_str
        end_date = end_date_str

        if request.method == "POST" and start_date_str and end_date_str:
            try:
                # [QUAN TRỌNG] Chuyển chuỗi sang ngày tháng để DB hiểu
                # HTML input date trả về định dạng: YYYY-MM-DD
                d_start = datetime.strptime(start_date_str, "%Y-%m-%d")
                d_end = datetime.strptime(end_date_str, "%Y-%m-%d")

                if report_type == "day":
                    day_report = dao.revenue_room_by_range(d_start, d_end)

                elif report_type == "week":
                    day_report = []  # Reset để tránh hiển thị nhầm
                    week_report = dao.revenue_room_by_week_range(d_start, d_end)

                elif report_type == "trend":
                    day_report = []
                    week_report = []
                    trend_data = dao.room_usage_trend_range(d_start, d_end)
            except Exception as ex:
                # Xử lý lỗi nếu ngày tháng không hợp lệ
                print(f"Error parsing date: {ex}")

        return self.render(
            'admin/index.html',
            report_type=report_type,
            day_report=day_report,
            week_report=week_report,
            trend_data=trend_data,
            start_date=start_date,
            end_date=end_date,
        )


class UserView(AdminView):
    column_list = ["name", 'username', 'phone', 'role', 'status']
    column_searchable_list = ["name", "phone", "username"]
    column_filters = ['role', 'name']
    column_editable_list = ['role', 'status']
    form_columns = ['name', 'username', 'password', 'phone', 'role', 'status']
    column_exclude_list = ['password']
    edit_modal = True
    can_export = True
    page_size = 10

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password = hashlib.sha1(form.password.data.encode('utf-8')).hexdigest()

admin = Admin(app=app, name="E-COMMERCE", theme=Bootstrap4Theme(), index_view=MyAdminIndexView())
admin.add_view(RoomView(Room, db.session))
admin.add_view(ServiceView(Service, db.session))
admin.add_view(TypeRoomView(TypeRoom, db.session))
admin.add_view(UserView(User, db.session,name='Quản lý người dùng'))
admin.add_view(LogoutView(name='Đăng xuất'))