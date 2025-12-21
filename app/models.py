import json
import hashlib
from app import db, app
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey,Enum,Date,Time
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as RoleEnum
from enum import Enum as PyEnum
from flask_login import UserMixin

class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)

    def __str__(self):
        return self.name

class UserRole(RoleEnum):
    GUEST = 1
    ADMIN = 2
    STAFF = 3

class CouponStatus(PyEnum):
    BOOKED = "BOOKED"
    USING = "USING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

class User(Base, UserMixin):
    __tablename__ = 'user'
    username = Column(String(150), nullable=False, unique=True)
    password = Column(String(150), nullable=False)
    phone = Column(String(150), nullable=False)
    point = Column(Integer, default=0) #chỉ dùng cho guest
    last_point_update = Column(DateTime, default=datetime.now)
    status = Column(Boolean,default=True)
    date_created = Column(DateTime, default=datetime.now)
    role = Column(Enum(UserRole), default=UserRole.GUEST)

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN
    @property
    def is_staff(self):
        return self.role == UserRole.STAFF
    @property
    def is_guest(self):
        return self.role == UserRole.GUEST

class Room(Base):
    __tablename__ = "room"
    capacity = Column(Integer)
    status = Column(Boolean, default=True)
    image = Column(String(150), nullable=False)
    typeid = Column(Integer, ForeignKey("typeroom.id"), nullable=False)

class TypeRoom(Base):
    __tablename__ = "typeroom"
    rooms = relationship("Room", backref="type", lazy=True)
    price = Column(Float)

class Coupon(db.Model):
    __tablename__ = "coupon"
    id  = Column(Integer, primary_key=True, autoincrement=True)
    #ngày tạo phiếu(tự động khi đặt phòng)
    created_time = Column(DateTime, default=datetime.now)

    #ngày đặt phòng hát
    booking_date = Column(Date, nullable=False)

    #giờ bắt đầu & giờ kết thúc
    check_in_time = Column(Time, nullable=False)
    check_out_time = Column(Time, nullable=False)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    user = relationship("User", backref="coupon", lazy=True)

    room_id = Column(Integer, ForeignKey('room.id'), nullable=False)
    room = relationship("Room", backref="coupon", lazy=True)

    status = Column(
        Enum(CouponStatus),
        default=CouponStatus.BOOKED,
        nullable=False,
    )
    receipt = relationship("Receipt", back_populates="coupon", uselist =False)

class Receipt(Base):
    __tablename__ = "receipt"

    staff_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    coupon_id = Column(Integer, ForeignKey('coupon.id'), nullable=False)

    created_time = Column(DateTime, default=datetime.now)
    total_room = Column(Float, default=0)
    total_service = Column(Float, default=0)
    total = Column(Float, default=0)
    discount = Column(Float, default=0)
    vat = Column(Float, default=0)
    payment_method =Column(String(10))


    details = relationship("DetailServices",
        back_populates="receipt",
        cascade="all, delete-orphan")
    coupon = relationship("Coupon",back_populates="receipt")


class Service(Base):
    __tablename__ = "service"

    unit = Column(String(20), nullable=False)
    price = Column(Float,default=0)
    status_service = Column(Boolean,default=True)
    inventory_quantity = Column(Integer,default=0)

    details = relationship("DetailServices", back_populates="service")

class DetailServices(Base):
    __tablename__ = "detail_services"

    service_id = Column(Integer, ForeignKey('service.id'), nullable=False)
    receipt_id = Column(Integer, ForeignKey('receipt.id'), nullable=False)

    quantity = Column(Integer,nullable=False)
    total =Column(Float)
    price =Column(Float,nullable=False)

    service = relationship("Service",back_populates="details")
    receipt = relationship("Receipt",back_populates="details")
if __name__ == "__main__":
    with app.app_context():
        # db.drop_all()
        db.create_all()

        if not TypeRoom.query.first():
            with open("data/typeroom.json", encoding="utf-8") as f:
                styles = json.load(f)
                for s in styles:
                    db.session.add(TypeRoom(
                        name=s["name"],
                        price=s["price"]
                    ))
            db.session.commit()

        if not Room.query.first():
            with open("data/room.json", encoding="utf-8") as f:
                rooms = json.load(f)
                for r in rooms:
                    db.session.add(Room(
                        name=r["name"],
                        capacity=r["capacity"],
                        status=r.get("status", True),
                        image=r["image"],
                        typeid=r["typeid"]
                    ))
            db.session.commit()
        if not User.query.first():
            with open("data/users.json", encoding="utf-8") as f:
                users = json.load(f)
                for u in users:
                    password = hashlib.sha1(u["password"].encode('utf-8')).hexdigest()
                    user = User(
                        name=u["name"],
                        username=u["username"],
                        password=password,
                        phone=u["phone"],
                        role=UserRole[u["role"]]
                    )
                    db.session.add(user)
            db.session.commit()
        if not Service.query.first():
            with open("data/services.json", encoding="utf-8") as f:
                services = json.load(f)
                for s in services:
                    db.session.add(Service(
                        name=s["name"],
                        unit=s["unit"],
                        price=s["price"],
                        inventory_quantity=s["inventory_quantity"],
                        status_service=s.get("status_service", True)
                    ))
            db.session.commit()

