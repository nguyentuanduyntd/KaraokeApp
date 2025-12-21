import hashlib

from sqlalchemy import extract, func
from sqlalchemy.orm import joinedload
from datetime import datetime
from app import app, db
from app.models import Room, TypeRoom, User, UserRole, Coupon, Service, DetailServices, Receipt, CouponStatus


def load_typeroom():
    return TypeRoom.query.all()

def load_room():
    return db.session.query(Room).options(joinedload(Room.type)).all()

def auth_user(username, password):
    password = hashlib.sha1(password.encode('utf-8')).hexdigest()
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()


def add_user(name, username, password, phone):
    password = hashlib.sha1(password.encode('utf-8')).hexdigest()

    user = User(
        name=name.strip(),
        username=username.strip(),
        password=password,
        phone=phone,
        role=UserRole.GUEST,
        status=True
    )
    db.session.add(user)
    db.session.commit()
    return user

def get_user_by_id(user_id):
    return User.query.get(user_id)


def add_booking(user_id, room_id, booking_date, check_in_time, check_out_time):
    try:
        conflict = Coupon.query.filter(
            Coupon.room_id == room_id,
            Coupon.booking_date == booking_date,
            Coupon.check_out_time > check_in_time,
            Coupon.check_in_time < check_out_time
        ).first()
        if conflict:
            raise Exception("Phòng đã có người đặt trong khoảng thời gian này!")

        booking = Coupon(
            user_id=user_id,
            room_id=room_id,
            booking_date=booking_date,
            check_in_time=check_in_time,
            check_out_time=check_out_time,
            status=CouponStatus.BOOKED
        )
        db.session.add(booking)
        db.session.flush()

        user = User.query.get(user_id)
        receipt = Receipt(
            staff_id = None,
            coupon_id = booking.id,
            name = user.name,
            total_room = 0,
            total_service = 0,
            total = 0,
            vat =0
        )
        db.session.add(receipt)
        db.session.commit()
        return booking
    except Exception as ex:
        db.session.rollback()
        raise ex

def staff_create_booking(guest_name, guest_phone, room_id, booking_date, start_time, end_time, staff_id):
    conflict = Coupon.query.filter(
        Coupon.room_id == room_id,
        Coupon.booking_date == booking_date,
        Coupon.check_out_time > start_time,
        Coupon.check_in_time < end_time
    ).first()

    if conflict:
        raise Exception("Phòng đã có người đặt trong thời gian này!!")

    guest = User.query.filter(
        User.phone == guest_phone,
        User.role == UserRole.GUEST
    ).first()

    if not guest:
        password = hashlib.sha1("123456789".encode('utf-8')).hexdigest()
        guest = User(
            name=guest_name,
            username=f"vl_{guest_phone}",
            password=password,
            phone=guest_phone,
            role=UserRole.GUEST,
            status=True
        )
        db.session.add(guest)
        db.session.flush()

    booking = Coupon(
        user_id=guest.id,
        room_id=room_id,
        booking_date=booking_date,
        check_in_time=start_time,
        check_out_time=end_time,
        status=CouponStatus.BOOKED
    )
    db.session.add(booking)
    db.session.flush()

    receipt = Receipt(
        staff_id=staff_id,
        coupon_id=booking.id,
        name =guest.name,
        total_room=0,
        total_service=0,
        total=0,
        vat=0
    )
    db.session.add(receipt)

    db.session.commit()
    return booking


def load_history(user_id):
    return Coupon.query.filter(Coupon.user_id == user_id).order_by(Coupon.created_time.desc()).all()


def load_guests():
    return User.query.filter(User.role == UserRole.GUEST).all()


def load_service(active_only=True):
    query = Service.query
    if active_only:
        query = query.filter(Service.status_service == True)
    return query.all()

def load_active_rooms_with_customer():
    return db.session.query(
        Room.name.label("room_name"),
        User.name.label("user_name"),
        Coupon.check_in_time,
        Coupon.check_out_time,
    ).join(
        Coupon, Coupon.room_id == Room.id,
    ).join(
        User, User.id == Coupon.user_id
    ).filter(
        Coupon.status == True,
    ).all()

def load_service_details(receipt_id):
    return DetailServices.query.filter(
        DetailServices.receipt_id == receipt_id,
    ).all()

def update_receipt_total(receipt_id):
    receipt = Receipt.query.get(receipt_id)
    if not receipt:
        return
    receipt.total_service = calc_total_service(receipt_id)
    receipt.total = (receipt.total_room or 0) + receipt.total_service + (receipt.vat or 0)
    db.session.commit()


def calc_total_service(receipt_id):
    total = db.session.query(
        db.func.sum(DetailServices.total)
    ).filter(DetailServices.receipt_id == receipt_id).scalar()
    return total or 0


def delete_service(detail_id):
    detail = DetailServices.query.get(detail_id)
    if detail:
        receipt_id = detail.receipt_id
        db.session.delete(detail)
        db.session.commit()

        update_receipt_total(receipt_id)


def get_receipt_by_id(receipt_id):
    return Receipt.query.get(receipt_id)


def load_active_receipt():
    return Receipt.query.join(Coupon) \
        .filter(Coupon.status == "BOOKED") \
        .order_by(Receipt.created_time.desc()) \
        .all()

def refresh_user_point(user, current_booking_date):
    if not user:
        return
    now = datetime.now()
    last_update = user.last_point_update

    if not last_update or (last_update.month != current_booking_date.month) or (last_update.year != current_booking_date.year):
        user.point = 0
        user.last_point_update = current_booking_date
        return True
    return False

def guest_point(user,booking_date):
    refresh_user_point(user,booking_date)
    user.point += 2
    user.last_point_update = booking_date

def apply_point_discount(user: User, subtotal,booking_date):
    refresh_user_point(user,booking_date)

    if user.role == UserRole.GUEST and user.point >= 10:
        discount = subtotal * 0.05
        return discount
    return 0

def update_booking_total(coupon_id):
    coupon = Coupon.query.get(coupon_id)
    receipt = Receipt.query.filter_by(coupon_id=coupon_id).first()

    if not coupon or not receipt:
        return None

    room_price = coupon.room.type.price if (coupon.room and coupon.room.type) else 0

    t_start = datetime.combine(coupon.booking_date, coupon.check_in_time)
    t_end = datetime.combine(coupon.booking_date, coupon.check_out_time)

    duration = t_end - t_start
    hours_used = duration.total_seconds() / 3600
    if hours_used < 0: hours_used = 0

    receipt.total_room = hours_used * room_price

    #ính tiền dịch vụ
    receipt.total_service = calc_total_service(receipt.id)

    #Tính tổng tạm tính
    subtotal = receipt.total_room + receipt.total_service


    user = User.query.get(coupon.user_id)
    discount = apply_point_discount(user, subtotal,coupon.booking_date) if user else 0

    after_discount = subtotal - discount

    #Tính VAT(10%)
    vat = after_discount * 0.10

    #Tổng cuối cùng
    total = after_discount + vat

    # Cập nhật vào Receipt
    receipt.discount = discount
    receipt.vat = vat
    receipt.total = total

    db.session.commit()
    return receipt

def checkout_booking(coupon_id, payment_method):
    update_booking_total(coupon_id)

    coupon = Coupon.query.get(coupon_id)
    receipt = Receipt.query.filter_by(coupon_id=coupon_id).first()
    user = User.query.get(coupon.user_id)

    if receipt.discount > 0:
        if user.point >= 10:
            user.point -= 10
        else:
            receipt.discount = 0
            receipt.total = (receipt.total_room + receipt.total_service) * 1.1  # Tính lại tổng gốc + VAT

    guest_point(user,coupon.booking_date)

    receipt.payment_method = payment_method
    coupon.status = CouponStatus.PAID

    db.session.commit()

def load_coupon_by_room(room_id):
    today = datetime.now().date()
    return Coupon.query.filter(
        Coupon.room_id == room_id,
        Coupon.status != CouponStatus.CANCELLED,
        Coupon.booking_date >= today
    ).order_by(Coupon.booking_date, Coupon.check_in_time).all()

def get_room_by_id(room_id):
    return Room.query.get(room_id)

def revenue_room_by_range(start_date, end_date):
    return db.session.query(
        func.date(Coupon.booking_date).label("date"),
        Room.name.label("room_name"),
        func.coalesce(func.sum(Receipt.total), 0).label("revenue")
    ).join(Coupon, Coupon.room_id == Room.id) \
     .join(Receipt, Receipt.coupon_id == Coupon.id) \
     .filter(Coupon.booking_date.between(start_date, end_date)) \
     .filter(Coupon.status == CouponStatus.PAID) \
     .group_by(func.date(Coupon.booking_date), Room.name) \
     .order_by(func.date(Coupon.booking_date)) \
     .all()

def revenue_room_by_week_range(start_date, end_date):
    return db.session.query(
        Room.name.label("room_name"),
        func.yearweek(Coupon.booking_date, 3).label("week"),
        func.sum(Receipt.total).label("revenue")
    ).join(Coupon, Coupon.room_id == Room.id) \
     .join(Receipt, Receipt.coupon_id == Coupon.id) \
     .filter(Coupon.booking_date.between(start_date, end_date)) \
     .filter(Coupon.status == CouponStatus.PAID) \
     .group_by(Room.name, func.yearweek(Coupon.booking_date, 3)) \
     .order_by(func.yearweek(Coupon.booking_date, 3)) \
     .all()


def room_usage_trend_range(start_date, end_date):
    return db.session.query(
        Room.name.label("room_name"),
        func.count(Coupon.id).label("total")
    ).join(Coupon, Coupon.room_id == Room.id) \
     .filter(Coupon.booking_date.between(start_date, end_date)) \
     .filter(Coupon.status == CouponStatus.PAID) \
     .group_by(Room.name) \
     .all()

if __name__ == '__main__':
    with app.app_context():
        print(auth_user('admin', 'admin'))