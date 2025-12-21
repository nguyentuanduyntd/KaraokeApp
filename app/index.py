from datetime import datetime

from flask import flash, request, redirect, render_template,url_for,abort
from flask_login import login_user, current_user, logout_user, login_required

from app.dao import checkout_booking
from app.models import Room, TypeRoom, User, UserRole, Coupon, Receipt,Service,DetailServices,CouponStatus
import dao
from app import app, db, login


# hoàn tất không sửa thêm
@app.route("/")
def index():
    rooms = dao.load_room()
    typerooms = dao.load_typeroom()
    return render_template("index.html", rooms=rooms, typerooms=typerooms)


#hoàn tất không sửa thêm
@app.route("/login", methods=['get','post'])
def login_users():
    if current_user.is_authenticated:
        return redirect('/')

    err_msg = None
    if request.method.__eq__("POST"):
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username, password)
        if user:
            login_user(user)
            return redirect('/')
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"
    return render_template("login.html", err_msg=err_msg)


#hoàn tất không sửa thêm
@login.user_loader
def get_user(user_id):
    return dao.get_user_by_id(user_id)


#hoàn tất không sửa thêm
@app.route('/logout')
def logout_my_user():
    logout_user()
    return redirect('/login')

#hoàn tất không sửa thêm
@app.route("/register", methods=['get','post'])
def register():
    err_msg = None

    if request.method.__eq__("POST"):
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        phone = request.form.get('phone')

        if not name or not username or not password or not phone or not confirm:
            err_msg = "Vui lòng nhập đầy đủ thông tin"

        elif password != confirm:
            err_msg = "Mật khẩu xác nhận không khớp!"

        elif not phone.isdigit() or len(phone) not in [9,10]:
            err_msg = "Số điện thoại không hợp lệ!"

        else:
            try:
                dao.add_user(name, username,password, phone)
                return redirect('/login')
            except Exception as ex:
                err_msg = ex
                db.session.rollback()
                err_msg = "Tài khoản đã tồn tại hoặc hệ thống đang lỗi!"

    return render_template("register.html", err_msg=err_msg)

# hoàn tất không sửa thêm
@app.route("/booking", methods=['get', 'post'])
@app.route("/booking/<int:room_id>", methods=['get', 'post'])
@login_required
def booking_page(room_id=None, user_id=None):
    if current_user.is_staff:
        return redirect("/")
    rooms = dao.load_room()
    err_msg = None
    if request.method.__eq__("POST"):
        room_id_form = request.form.get('room_id')
        booking_date = request.form.get('booking_date')
        check_in_time = request.form.get('start_time')
        check_out_time = request.form.get('end_time')

        if not all([room_id_form, booking_date, check_in_time, check_out_time]):
            err_msg = "Vui lòng nhập đầy đủ thông tin đặt phòng!"
        else:
            try:
                dao.add_booking(
                    user_id=current_user.id,
                    room_id=int(room_id_form),
                    booking_date=datetime.strptime(booking_date, "%Y-%m-%d").date(),
                    check_in_time=datetime.strptime(check_in_time, "%H:%M").time(),
                    check_out_time=datetime.strptime(check_out_time, "%H:%M").time(),

                )
                flash("Đặt phòng thành công!", "success")
                return redirect('/')
            except Exception as ex:
                db.session.rollback()
                flash(str(ex),"danger")
                return redirect(request.url)
    return render_template("booking.html", rooms=rooms, room_id=room_id, err_msg=err_msg, user_id=user_id)


# hoàn tất không sửa thêm
@app.route("/history")
@login_required
def booking_history():
    bookings = dao.load_history(current_user.id)
    return render_template("history.html", bookings=bookings)

@app.route("/booking/<int:booking_id>/cancel",methods=["POST"])
@login_required
def cancel_booking(booking_id):
    booking = Coupon.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        return redirect("/")
    if booking.status != CouponStatus.BOOKED:
        flash("Không thể hủy phiếu này!", "danger")
        return redirect("/history")
    booking.status = CouponStatus.CANCELLED
    db.session.commit()
    flash("Hủy đặt phòng thành công!", "success")
    return redirect("/history")


# hoàn tất không sửa thêm
@app.route("/staff")
@login_required
def staff_home():
    if not current_user.is_staff:
        return "Không có quyền truy cập"

    return render_template("staff/staff.html")

@app.route("/staff/booking", methods=['get', 'post'])
@login_required
def staff_booking():
    if not current_user.is_staff:
        return redirect("/")

    rooms = dao.load_room()
    guests = dao.load_guests()

    if request.method == "POST":
         try:
             dao.staff_create_booking(
                 guest_name=request.form.get('guest_name'),
                 guest_phone=request.form.get('guest_phone'),
                 room_id=int(request.form.get('room_id')),
                 booking_date=datetime.strptime(request.form.get('booking_date'), "%Y-%m-%d").date(),
                 start_time = datetime.strptime(request.form.get('start_time'), "%H:%M").time(),
                 end_time = datetime.strptime(request.form.get('end_time'), "%H:%M").time(),
                 staff_id=current_user.id
             )
             flash("Đặt phòng thành công!", "success")
             return redirect("/")
         except Exception as ex:
             db.session.rollback()
             flash(str(ex), "danger")
             return redirect(request.url)
    return render_template("staff/staff_booking.html", rooms=rooms,guests=guests)

@app.route("/staff/services",methods=['GET'])
@login_required
def staff_services():
    if not current_user.is_staff:
        return redirect("/")

    receipts = dao.load_active_receipt()
    rooms = dao.load_active_rooms_with_customer()
    return render_template("staff/staff_services.html", rooms=rooms,receipts=receipts)

@app.route("/staff/services/<int:receipt_id>")
@login_required
def staff_services_detail(receipt_id):
    if not current_user.is_staff:
        return redirect("/")

    receipt = dao.get_receipt_by_id(receipt_id)
    services = dao.load_service()
    details = dao.load_service_details(receipt_id)
    total_service = dao.calc_total_service(receipt_id)

    return render_template(
        "staff/service_detail.html",
        receipt=receipt,
        services=services,
        details=details,
        total_service=total_service,
    )

@app.route("/staff/services/add/<int:receipt_id>", methods=["POST"])
@login_required
def staff_add_service(receipt_id):
    if not current_user.is_staff:
        return redirect("/")

    service_id = request.form.get('service_id')
    quantity = int(request.form.get('quantity', 1))

    if not service_id:
        flash("Vui lòng chọn dịch vụ", "danger")
        return redirect(url_for("staff_services_detail", receipt_id=receipt_id))

    service_id = int(service_id)

    service = Service.query.get_or_404(service_id)
    receipt = Receipt.query.get_or_404(receipt_id)
    total = service.price * quantity
    ds = DetailServices(
        service_id=service_id,
        receipt_id=receipt_id,
        quantity=quantity,
        price=service.price,
        total=total,
        name=service.name
    )

    db.session.add(ds)
    db.session.commit()

    recalc_receipt(receipt_id)

    flash("Thêm dịch vụ thành công", "success")
    return redirect(url_for("staff_services_detail", receipt_id=receipt_id))

@app.route("/staff/services/delete/<int:receipt_id>/<int:ds_id>")
@login_required
def staff_delete_service(receipt_id,ds_id):
    if not current_user.is_staff:
        return redirect("/")

    ds = DetailServices.query.get(ds_id)
    if not ds or ds.receipt_id != receipt_id:
        abort(404)
    db.session.delete(ds)
    db.session.commit()

    recalc_receipt(receipt_id)

    flash("Đã xóa dịch vụ", "success")
    return redirect(url_for("staff_services_detail", receipt_id=receipt_id))

def recalc_receipt(receipt_id):
    receipt = Receipt.query.get(receipt_id)
    if not receipt:
        return
    total_service = db.session.query(
        db.func.sum(DetailServices.quantity * DetailServices.price)
    ).filter(DetailServices.receipt_id == receipt_id).scalar() or 0

    receipt.total_service = total_service
    total_room = receipt.total_room or 0
    vat = (total_room + total_service) * (receipt.vat or 0) / 100
    receipt.total = total_room + total_service - (receipt.discount or 0) + vat
    db.session.commit()

@app.context_processor
def inject_guest_point():
    if current_user.is_authenticated:
        return dict(guest_point=current_user.point)
    return dict(guest_point=0)

@app.route("/staff/payment")
@login_required
def staff_payment():
    if not current_user.is_staff:
        return redirect("/")

    coupons = Coupon.query.filter(Coupon.status == CouponStatus.BOOKED) \
        .order_by(Coupon.created_time.desc()).all()

    for c in coupons:
        dao.update_booking_total(c.id)

    return render_template("staff/staff_payment.html", coupons=coupons)

@app.route("/staff/payment/confirm/<int:coupon_id>",methods=["POST"])
@login_required
def staff_confirm_payment(coupon_id):
    if not current_user.is_staff:
        abort(403)
    method = request.form.get("payment_method")
    receipt = Receipt.query.filter_by(coupon_id=coupon_id).first()

    if method == "CASH":
        return handle_cash_payment(coupon_id,method)

    elif method == "MOMO":
        return redirect(url_for("staff_momo_payment", coupon_id=coupon_id))
    abort(400)

def handle_cash_payment(coupon_id,payment_method):
    checkout_booking(coupon_id,payment_method)
    flash("Thanh toán tiền mặt thành công", "success")
    return redirect(url_for("staff_payment"))

@app.route("/staff/payment/momo/<int:coupon_id>")
@login_required
def staff_momo_payment(coupon_id):
    if not current_user.is_staff:
        abort(403)

    receipt = Receipt.query.filter_by(coupon_id=coupon_id).first()
    return render_template("/staff/momo_qr.html",receipt=receipt)

@app.route("/staff/payment/momo/callback/<int:coupon_id>",methods=["POST"])
@login_required
def staff_momo_callback(coupon_id):
    if not current_user.is_staff:
        abort(403)
    method = request.form.get("payment_method")
    checkout_booking(coupon_id,method)
    flash("Thanh toán MoMo thành công", "success")
    return redirect(url_for("staff_payment"))

@app.route("/rooms-schedule")
def room_list_check():
    rooms = dao.load_room()
    return render_template("room_list.html", rooms=rooms)

@app.route("/rooms-schedule/<int:room_id>")
def room_detail_schedule(room_id):
    room = dao.get_room_by_id(room_id)
    if not room:
        return redirect(url_for("room_list_check"))
    booked_coupons = dao.load_coupon_by_room(room_id)
    return render_template("room_detail_schedule.html",room=room, coupons=booked_coupons)

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
