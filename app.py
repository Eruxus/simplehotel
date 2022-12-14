# Immports for curses
import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle
# Imports for flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
# General imports
from datetime import datetime, timedelta
import sys
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:666@localhost/simplehotel'
db = SQLAlchemy(app)
db.init_app(app)
migrate = Migrate(app,db)
migrate.init_app(app, db)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), unique=False, nullable=False)
    last_name = db.Column(db.String(50), unique=False, nullable=False)
    birth_date = db.Column(db.Date, unique=False, nullable=False)
    street_address = db.Column(db.String(95), unique=False, nullable=False)
    postal_number = db.Column(db.String(11), unique=False, nullable=False)
    city = db.Column(db.String(35), unique=False, nullable=False)
    country = db.Column(db.String(20), unique=False, nullable=False)
    mail = db.Column(db.String(100), unique=False, nullable=True)
    contact_number = db.Column(db.String(15), unique=False, nullable=True)
    deleted = db.Column(db.Boolean, unique=False, nullable=False)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(50), unique=False, nullable=False)
    size = db.Column(db.Integer, unique=False, nullable=False)
    is_double = db.Column(db.Boolean, unique=False, nullable=True)
    daily_price = db.Column(db.Integer, unique=False, nullable=False)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_in = db.Column(db.Date, unique=False, nullable=False)
    check_out = db.Column(db.Date, unique=False, nullable=False)
    extra_beds = db.Column(db.Integer, unique=False, nullable=False)
    canceled = db.Column(db.Boolean, unique=False, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    to_pay = db.Column(db.Integer, unique=False, nullable=True)
    date = db.Column(db.DateTime, unique=False, nullable=False)
    deadline = db.Column(db.Date, unique=False, nullable=False)
    is_paid = db.Column(db.Boolean, unique=False, nullable=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)

def CreateRooms():
    exists = Room.query.filter(Room.room_name.contains("Basic Single Room")).all()
    if not exists:
        room_single = Room()
        room_single.room_name = "Basic Single Room"
        room_single.size = 12
        room_single.daily_price = 500
        room_single.is_double = False
        db.session.add(room_single)
        db.session.commit()

    exists = Room.query.filter(Room.room_name.contains("Basic Double Room")).all()
    if not exists:
        room_double = Room()
        room_double.room_name = "Basic Double Room"
        room_double.size = 15
        room_double.daily_price = 600
        room_double.is_double = True
        db.session.add(room_double)
        db.session.commit()
    
    exists = Room.query.filter(Room.room_name.contains("Deluxe Double Room")).all()
    if not exists:
        room_double2 = Room()
        room_double2.room_name = "Deluxe Double Room"
        room_double2.size = 18
        room_double2.daily_price = 700
        room_double2.is_double = True
        db.session.add(room_double2)
        db.session.commit()

# Functions for handling logic
def ListUnpaid() -> list:
    unpaid_list = []
    unpaid_invoices = Invoice.query.filter_by(is_paid = 0).order_by(Invoice.date).all()
    for x in unpaid_invoices:
        unpaid_list.append(f"{x.to_pay}kr to pay by {x.deadline} ID;{x.id}")
    return unpaid_list

def ListUpcoming() -> list:
    active_reservations_list = []
    today = datetime.now().date()
    active_reservations = Reservation.query.filter_by(canceled = 0).order_by(Reservation.check_in).all()
    for x in active_reservations:
        if x.check_out >= today:
            customer = Customer.query.filter_by(id = x.customer_id).first()
            active_reservations_list.append(f"{customer.first_name} {customer.last_name} - From {x.check_in} to {x.check_out} ID;{x.id}")
    return active_reservations_list

def KillPastDeadline():
    unpaid_invoices = Invoice.query.filter_by(is_paid = 0)
    today = datetime.now().date()
    for x in unpaid_invoices:
        if today > x.deadline:
            reservation = Reservation.query.filter_by(id = x.reservation_id).first()
            reservation.canceled = True
        db.session.commit()
    print("\nSuccesfully canceled resevations past deadline. Initiating...")
    time.sleep(2)

def FindReservation(checkin, checkout) -> int:
    reservation_id = 0
    result = Reservation.query.all()
    for x in result:
        if x.check_in == checkin and x.check_out == checkout:
            reservation_id = x.id
    return reservation_id

def SearchRoom(checkin, checkout) -> list:
    room_query = Room.query.all()
    reservation_query = Reservation.query.all()
    free = True
    room_list = []
    for x in room_query:
        free = True
        for y in reservation_query:
            if y.room_id == x.id:
                if y.check_in <= checkin <= y.check_out or y.check_in <= checkout <= y.check_out:
                    free = False
        if free == True:
            room_list.append(f"{x.room_name} ID;{x.id}")
    return room_list

def GenerateInvoice(checkin, checkout, room_price, reservation_id):
    today = datetime.now()
    deadline =  today + timedelta(days=10)
    days = (checkout - checkin).days
    to_pay = days * room_price
    paid = False
    invoice = Invoice()
    invoice.to_pay = to_pay
    invoice.date = today
    invoice.deadline = deadline
    invoice.is_paid = paid
    invoice.reservation_id = reservation_id
    db.session.add(invoice)
    db.session.commit()

def InsertReservation(checkin, checkout, extra, room_id, customer_id):
    reservation = Reservation()
    reservation.check_in = checkin
    reservation.check_out = checkout
    reservation.extra_beds = extra
    reservation.canceled = False
    reservation.room_id = room_id
    reservation.customer_id = customer_id
    db.session.add(reservation)
    db.session.commit()

def SearchCustomers(query) -> list:
    listan = []
    result = Customer.query.filter(Customer.last_name.contains(query)).all()
    for x in result:
        if f"{x.last_name}".lower() == query.lower() and x.deleted == False:
            listan.append(f"{x.first_name} {x.last_name} ID;{x.id}")
    return listan

def InsertCustomer(fname, lname, birthdate, address, postalcode, city, country, email, number):
    customer = Customer()
    customer.first_name = fname.strip()
    customer.last_name = lname.strip()
    customer.birth_date = birthdate
    customer.street_address = address.strip()
    customer.postal_number = postalcode.strip()
    customer.city = city.strip()
    customer.country = country.strip()
    customer.mail = email.strip()
    customer.contact_number = number.strip()
    db.session.add(customer)
    db.session.commit()

# Menu system
def delete_customer(stdscr):
    height, width = stdscr.getmaxyx()
    key = 0
    current_row = 1
    stdscr.clear()
    stdscr.refresh()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    CYAN = curses.color_pair(1)
    BLACK_CYAN = curses.color_pair(2)
    search_tooltip = "You can only delete customers that don't have upcoming reservation, search by last name"
    footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"
    stdscr.attron(CYAN)
    stdscr.addstr(height-(height), 1, search_tooltip)
    stdscr.attroff(CYAN)
    stdscr.attron(BLACK_CYAN)
    stdscr.addstr(height-1, 0, " " * (width-1))
    stdscr.addstr(height-1, 1, footer)
    stdscr.attroff(BLACK_CYAN)
    stdscr.refresh()
    search_box = Textbox(curses.newwin(1, 30, 1, 1))
    curses.curs_set(1)
    search_box.edit()
    curses.curs_set(0)
    search_query = search_box.gather()
    search_query = search_query.strip()
    main_menu_items = SearchCustomers(search_query)
    main_menu_items.append("Back")
    footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"
    stdscr.clear()
    while True:
        curses.curs_set(0)
        
        # Strings
        title = "Your search results "

        stdscr.attron(CYAN)
        stdscr.addstr(height-(height), 1 , title)
        stdscr.attroff(CYAN)

        stdscr.attron(BLACK_CYAN)
        stdscr.addstr(height-1, 0, " " * (width-1))
        stdscr.addstr(height-1, 1, footer)
        stdscr.attroff(BLACK_CYAN)
        for idx, element in enumerate(main_menu_items):
            y = 1 + idx
            if y == current_row:
                stdscr.attron(BLACK_CYAN)
                stdscr.addstr(y, 1, element)
                stdscr.attroff(BLACK_CYAN)
            else:
                stdscr.addstr(y, 1, element)

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 1:
            current_row = current_row - 1
        elif key == curses.KEY_DOWN and current_row < len(main_menu_items):
            current_row = current_row + 1
        elif key == 10:
            if current_row != len(main_menu_items):
                active = main_menu_items[current_row-1]
                parts = active.split(";")
                update_id = parts[-1]
                reservation_check = Reservation.query.filter_by(customer_id = update_id).all()
                today = datetime.now().date()
                invalid = False
                for x in reservation_check:
                    if x.check_out > today:
                        invalid = True
                if invalid == True:
                    current_row = 1
                    footer = "Oops, this customer has a active reservation"
                    stdscr.refresh()
                    continue
                customer_del = Customer.query.filter_by(id = update_id).first()
                customer_del.deleted = True
                db.session.commit()
                stdscr.attron(BLACK_CYAN)
                footer = "Deletion confirmation SUCCESSFUL! (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧"
                stdscr.addstr(height-1, 0, " " * (width-1))
                stdscr.addstr(height-1, 1, footer)
                stdscr.attroff(BLACK_CYAN)
                stdscr.refresh()
                time.sleep(3)
                wrapper(customers)
            if current_row == len(main_menu_items):
                wrapper(customers)

def confirm_payment(stdscr):
    height, width = stdscr.getmaxyx()
    key = 0
    current_row = 1
    stdscr.clear()
    stdscr.refresh()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    CYAN = curses.color_pair(1)
    BLACK_CYAN = curses.color_pair(2)
    search_tooltip = "Here is a list of unpaid reservation invoices"
    footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"
    stdscr.attron(CYAN)
    stdscr.addstr(height-(height), 1, search_tooltip)
    stdscr.attroff(CYAN)
    stdscr.attron(BLACK_CYAN)
    stdscr.addstr(height-1, 0, " " * (width-1))
    stdscr.addstr(height-1, 1, footer)
    stdscr.attroff(BLACK_CYAN)
    stdscr.refresh()
    main_menu_items = ListUnpaid()
    main_menu_items.append("Back")
    stdscr.clear()
    while True:
        curses.curs_set(0)
        
        # Strings
        title = "Your search results "
        footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"

        stdscr.attron(CYAN)
        stdscr.addstr(height-(height), 1 , title)
        stdscr.attroff(CYAN)

        stdscr.attron(BLACK_CYAN)
        stdscr.addstr(height-1, 0, " " * (width-1))
        stdscr.addstr(height-1, 1, footer)
        stdscr.attroff(BLACK_CYAN)
        for idx, element in enumerate(main_menu_items):
            y = 1 + idx
            if y == current_row:
                stdscr.attron(BLACK_CYAN)
                stdscr.addstr(y, 1, element)
                stdscr.attroff(BLACK_CYAN)
            else:
                stdscr.addstr(y, 1, element)

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 1:
            current_row = current_row - 1
        elif key == curses.KEY_DOWN and current_row < len(main_menu_items):
            current_row = current_row + 1
        elif key == 10:
            if current_row != len(main_menu_items):
                active = main_menu_items[current_row-1]
                parts = active.split(";")
                update_id = parts[-1]
                invoice_paid = Invoice.query.filter_by(id = update_id).first()
                invoice_paid.is_paid = True
                db.session.commit()
                stdscr.attron(BLACK_CYAN)
                footer = "Payment confirmation SUCCESSFUL! (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧"
                stdscr.addstr(height-1, 0, " " * (width-1))
                stdscr.addstr(height-1, 1, footer)
                stdscr.attroff(BLACK_CYAN)
                stdscr.refresh()
                time.sleep(3)
                wrapper(reservations)
            if current_row == len(main_menu_items):
                wrapper(reservations)

def cancel_reservation(stdscr):
    height, width = stdscr.getmaxyx()
    key = 0
    current_row = 1
    stdscr.clear()
    stdscr.refresh()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    CYAN = curses.color_pair(1)
    BLACK_CYAN = curses.color_pair(2)
    search_tooltip = "Here is a list of upcoming reservations, choose one to cancel it"
    footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"
    stdscr.attron(CYAN)
    stdscr.addstr(height-(height), 1, search_tooltip)
    stdscr.attroff(CYAN)
    stdscr.attron(BLACK_CYAN)
    stdscr.addstr(height-1, 0, " " * (width-1))
    stdscr.addstr(height-1, 1, footer)
    stdscr.attroff(BLACK_CYAN)
    stdscr.refresh()
    main_menu_items = ListUpcoming()
    main_menu_items.append("Back")
    stdscr.clear()
    while True:
        curses.curs_set(0)
        
        # Strings
        title = "Your search results "
        footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"

        stdscr.attron(CYAN)
        stdscr.addstr(height-(height), 1 , title)
        stdscr.attroff(CYAN)

        stdscr.attron(BLACK_CYAN)
        stdscr.addstr(height-1, 0, " " * (width-1))
        stdscr.addstr(height-1, 1, footer)
        stdscr.attroff(BLACK_CYAN)
        for idx, element in enumerate(main_menu_items):
            y = 1 + idx
            if y == current_row:
                stdscr.attron(BLACK_CYAN)
                stdscr.addstr(y, 1, element)
                stdscr.attroff(BLACK_CYAN)
            else:
                stdscr.addstr(y, 1, element)

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 1:
            current_row = current_row - 1
        elif key == curses.KEY_DOWN and current_row < len(main_menu_items):
            current_row = current_row + 1
        elif key == 10:
            if current_row != len(main_menu_items):
                active = main_menu_items[current_row-1]
                parts = active.split(";")
                update_id = parts[-1]
                reservation_to_cancel = Reservation.query.filter_by(id = update_id).first()
                reservation_to_cancel.canceled = True
                db.session.commit()
                stdscr.attron(BLACK_CYAN)
                footer = "Cancel SUCCESSFUL! (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧"
                stdscr.addstr(height-1, 0, " " * (width-1))
                stdscr.addstr(height-1, 1, footer)
                stdscr.attroff(BLACK_CYAN)
                stdscr.refresh()
                time.sleep(3)
                wrapper(reservations)
            if current_row == len(main_menu_items):
                wrapper(reservations)

def make_reservation(stdscr):
    key = 0
    current_row = 1
    stdscr.clear()
    stdscr.refresh()

    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    CYAN = curses.color_pair(1)
    BLACK_CYAN = curses.color_pair(2)

    checkin_day_box = Textbox(curses.newwin(1,3, 1, 32))
    checkin_month_box = Textbox(curses.newwin(1,3, 1, 29))
    checkin_year_box = Textbox(curses.newwin(1,5, 1, 24))
    checkout_day_box = Textbox(curses.newwin(1,3, 2, 33))
    checkout_month_box = Textbox(curses.newwin(1,3, 2, 30))
    checkout_year_box = Textbox(curses.newwin(1,5, 2, 25))

    footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"

    while True:
        curses.curs_set(0)
        height, width = stdscr.getmaxyx()

        stdscr.attron(CYAN)
        try:
            if not checkin_day:
                pass
        except UnboundLocalError:
            stdscr.addstr(1,32, "dd")
            checkin_day = ""
        try:
            if not checkin_month:
                pass
        except UnboundLocalError:
            stdscr.addstr(1,29, "mm")
            checkin_month = ""
        try:
            if not checkin_year:
                pass
        except UnboundLocalError:
            stdscr.addstr(1,24, "yyyy")
            checkin_year = ""
        try:
            if not checkout_day:
                pass
        except UnboundLocalError:
            stdscr.addstr(2,33, "dd")
            checkout_day = ""
        try:
            if not checkout_month:
                pass
        except UnboundLocalError:
            stdscr.addstr(2,30, "mm")
            checkout_month = ""
        try:
            if not checkout_year:
                pass
        except UnboundLocalError:
            stdscr.addstr(2,25, "yyyy")
            checkout_year = ""
        stdscr.attroff(CYAN)

        # Strings
        title = "Please choose what customer's desired check in and out dates"

        stdscr.attron(CYAN)
        stdscr.addstr(height-(height), 1 , title)
        stdscr.attroff(CYAN)

        stdscr.attron(BLACK_CYAN)
        stdscr.addstr(height-1, 0, " " * (width-1))
        stdscr.addstr(height-1, 1, footer)
        stdscr.attroff(BLACK_CYAN)
        
        main_menu_items = ["Desired check-in date: ", "Desired check-out date: ", "Search rooms", "Back"]
        for idx, element in enumerate(main_menu_items):
            y = 1 + idx
            if y == current_row:
                stdscr.attron(BLACK_CYAN)
                stdscr.addstr(y, 1, element)
                stdscr.attroff(BLACK_CYAN)
            else:
                stdscr.addstr(y, 1, element)

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 1:
            current_row = current_row - 1
        elif key == curses.KEY_DOWN and current_row < len(main_menu_items):
            current_row = current_row + 1
        elif key == 10:
            if current_row == 1:
                while True:
                    curses.curs_set(1)
                    checkin_year_box.edit()
                    curses.curs_set(0)
                    checkin_year = checkin_year_box.gather()
                    checkin_year = checkin_year.strip()
                    if checkin_year.isdigit() == True and len(checkin_year) == 4:
                        break
                    else:
                        footer = "A year has to be 4 numbers ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, 1, footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
                while True:
                    curses.curs_set(1)
                    checkin_month_box.edit()
                    curses.curs_set(0)
                    checkin_month = checkin_month_box.gather()
                    checkin_month = checkin_month.strip()
                    if checkin_month.isdigit() == True:
                        break
                    else:
                        footer = "A month has to be a number ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, 1, footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
                while True:
                    curses.curs_set(1)
                    checkin_day_box.edit()
                    curses.curs_set(0)
                    checkin_day = checkin_day_box.gather()
                    checkin_day = checkin_day.strip()
                    if checkin_day.isdigit() == True:
                        footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ You should have some yummy coffee during break!"
                        break
                    else:
                        footer = "A day has to be a number ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, 1, footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
            if current_row == 2:
                while True:
                    curses.curs_set(1)
                    checkout_year_box.edit()
                    curses.curs_set(0)
                    checkout_year = checkout_year_box.gather()
                    checkout_year = checkout_year.strip()
                    if checkout_year.isdigit() == True and len(checkout_year) == 4:
                        break
                    else:
                        footer = "A year has to be 4 numbers ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, 1, footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
                while True:
                    curses.curs_set(1)
                    checkout_month_box.edit()
                    curses.curs_set(0)
                    checkout_month = checkout_month_box.gather()
                    checkout_month = checkout_month.strip()
                    if checkout_month.isdigit() == True:
                        break
                    else:
                        footer = "A month has to be a number ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, 1, footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
                while True:
                    curses.curs_set(1)
                    checkout_day_box.edit()
                    curses.curs_set(0)
                    checkout_day = checkout_day_box.gather()
                    checkout_day = checkout_day.strip()
                    if checkout_day.isdigit() == True:
                        footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ You should have some yummy coffee during break!"
                        break
                    else:
                        footer = "A day has to be a number ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, 1, footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
            if current_row == 3:
                try:
                    checkin_date = datetime.strptime(f"{checkin_day}-{checkin_month}-{checkin_year}", "%d-%m-%Y").date()
                except ValueError:
                    footer = "Are you sure about this date? ԅ(≖‿≖ԅ)"
                    current_row = 1
                    continue
                checkin_date_str = f"{checkin_year}-{checkin_month}-{checkin_day}"
                try:
                    checkout_date = datetime.strptime(f"{checkout_day}-{checkout_month}-{checkout_year}", "%d-%m-%Y").date()
                except ValueError:
                    footer = "Are you sure about this date? ԅ(≖‿≖ԅ)"
                    current_row = 2
                    continue
                checkout_date_str = f"{checkout_year}-{checkout_month}-{checkout_day}"
                if checkin_date >= checkout_date:
                    footer = "Check for date paradox...(~_~;)"
                    continue
                available_rooms = SearchRoom(checkin_date, checkout_date)
                available_rooms.append("Back")
                key = 0
                current_row = 1
                stdscr.clear()
                stdscr.refresh()

                curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
                curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
                CYAN = curses.color_pair(1)
                BLACK_CYAN = curses.color_pair(2)

                while True:
                    curses.curs_set(0)
                    height, width = stdscr.getmaxyx()

                    # Strings
                    title = "Those rooms are available! "
                    footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"

                    stdscr.attron(CYAN)
                    stdscr.addstr(height-(height), 1 , title)
                    stdscr.attroff(CYAN)

                    stdscr.attron(BLACK_CYAN)
                    stdscr.addstr(height-1, 0, " " * (width-1))
                    stdscr.addstr(height-1, 1, footer)
                    stdscr.attroff(BLACK_CYAN)
                    
                    for idx, element in enumerate(available_rooms):
                        y = 1 + idx
                        if y == current_row:
                            stdscr.attron(BLACK_CYAN)
                            stdscr.addstr(y, 1, element)
                            stdscr.attroff(BLACK_CYAN)
                        else:
                            stdscr.addstr(y, 1, element)

                    key = stdscr.getch()
                    if key == curses.KEY_UP and current_row > 1:
                        current_row = current_row - 1
                    elif key == curses.KEY_DOWN and current_row < len(available_rooms):
                        current_row = current_row + 1
                    elif key == 10:
                        if current_row != len(available_rooms):
                            ############################################################
                            active_room = available_rooms[current_row-1]
                            parts = active_room.split(";")
                            room_id = parts[-1]
                            stdscr.clear()
                            current_row = 1
                            extra = 0
                            stdscr.addstr(1,1, f"{room_id}")
                            stdscr.refresh()
                            reservation_last_name = Textbox(curses.newwin(1,30, 1, 13))
                            footer = "You are almost there! (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧"
                            while True:
                                title = "Choose customer and extra beds"

                                stdscr.attron(CYAN)
                                stdscr.addstr(height-(height), 1 , title)
                                stdscr.attroff(CYAN)

                                stdscr.attron(BLACK_CYAN)
                                stdscr.addstr(height-1, 0, " " * (width-1))
                                stdscr.addstr(height-1, 1, footer)
                                stdscr.attroff(BLACK_CYAN)
                                if room_id == "1":
                                    final_menu_items = ["Choose Customer: ", "No extra beds available for this room", "Reserve!", "Back"]
                                else:
                                    final_menu_items = ["Choose Customer: ", "Extra beds: ", "Reserve!", "Back"]
                                for idx, element in enumerate(final_menu_items):
                                    y = 1 + idx
                                    if y == current_row:
                                        stdscr.attron(BLACK_CYAN)
                                        stdscr.addstr(y, 1, element)
                                        stdscr.attroff(BLACK_CYAN)
                                    else:
                                        stdscr.addstr(y, 1, element)

                                key = stdscr.getch()
                                if key == curses.KEY_UP and current_row > 1:
                                    current_row = current_row - 1
                                elif key == curses.KEY_DOWN and current_row < len(final_menu_items):
                                    current_row = current_row + 1
                                elif key == curses.KEY_RIGHT and current_row == 2:
                                    if room_id == "2":
                                        if extra == 0:
                                            extra = extra + 1
                                            stdscr.addstr(2, 13, f"{extra}")
                                    if room_id == "3":
                                        if extra < 2:
                                            extra = extra + 1
                                            stdscr.addstr(2, 13, f"{extra}")                                        
                                elif key == curses.KEY_LEFT and current_row == 2:
                                    if room_id == "2":
                                        if extra == 1:
                                            extra = extra - 1
                                            stdscr.addstr(2, 13, f"{extra}")
                                    if room_id == "3":
                                        if extra > 0:
                                            extra = extra - 1
                                            stdscr.addstr(2, 13, f"{extra}")
                                elif key == 10:
                                    if current_row == 1:
                                        key = 0
                                        search_win = curses.newwin(10, 30, 1, abs(int(width/2)-15))
                                        customer_search_box = Textbox(curses.newwin(1, 30, 1, abs(int(width/2))))
                                        curses.curs_set(1)
                                        customer_search_box.edit()
                                        curses.curs_set(0)
                                        search_current_row = 1
                                        search_query = customer_search_box.gather()
                                        search_query = search_query.strip()
                                        search_results = SearchCustomers(search_query)
                                        search_results.append("Back")
                                        search_win.addstr(0,1, "Search results")
                                        while True:
                                            for idx, element in enumerate(search_results):
                                                y = 1 + idx
                                                if y == search_current_row:
                                                    search_win.attron(BLACK_CYAN)
                                                    search_win.addstr(y, 1, element)
                                                    search_win.attroff(BLACK_CYAN)
                                                else:
                                                    search_win.addstr(y, 1, element)
                                            search_win.refresh()
                                            key = stdscr.getch()
                                            if key == curses.KEY_UP and search_current_row > 1:
                                                search_current_row = search_current_row - 1
                                            elif key == curses.KEY_DOWN and search_current_row < len(search_results):
                                                search_current_row = search_current_row + 1
                                            elif key == 10:
                                                if search_current_row != len(search_results):
                                                    active_customer = search_results[search_current_row-1]
                                                    parts = active_customer.split(";")
                                                    update_id = parts[-1]
                                                    customer = Customer.query.filter_by(id = update_id).first()
                                                    active_customer_id = customer.id
                                                    active_customer_name = f"{customer.first_name} {customer.last_name}"
                                                    stdscr.addstr(1, 18, active_customer_name)
                                                    search_win.clear()
                                                    search_win.refresh()
                                                    footer = "Nice choice $.$"
                                                    break
                                                if search_current_row == len(search_results):
                                                    search_win.clear()
                                                    search_win.refresh()
                                                    break
                                    if current_row == 3:
                                        try:
                                            stdscr.addstr(1, 30, f"{active_customer_id}")
                                        except UnboundLocalError:
                                            footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Make sure to choose customer ԅ(≖‿≖ԅ)"
                                            current_row = 1
                                            continue
                                        InsertReservation(checkin_date_str, checkout_date_str, extra, room_id, active_customer_id)
                                        reservation_id = FindReservation(checkin_date, checkout_date)
                                        room_price = 400
                                        if room_id == "1":
                                            room_price = 500
                                        if room_id == "2":
                                            room_price = 600
                                        if room_id == "3":
                                            room_price = 700
                                        GenerateInvoice(checkin_date, checkout_date, room_price, reservation_id)
                                        stdscr.attron(BLACK_CYAN)
                                        footer = "Reserved SUCCESSFULLY! (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧"
                                        stdscr.addstr(height-1, 0, " " * (width-1))
                                        stdscr.addstr(height-1, 1, footer)
                                        stdscr.attroff(BLACK_CYAN)
                                        stdscr.refresh()
                                        time.sleep(3)
                                        wrapper(reservations)
                                    if current_row == 4:
                                        wrapper(main)
                        if current_row == len(available_rooms):
                            wrapper(reservations)
            if current_row == 4:
                wrapper(reservations)
        stdscr.refresh()

def reservations(stdscr):
    key = 0
    current_row = 1
    stdscr.clear()
    stdscr.refresh()

    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    CYAN = curses.color_pair(1)
    BLACK_CYAN = curses.color_pair(2)

    while True:
        curses.curs_set(0)
        height, width = stdscr.getmaxyx()

        # Strings
        title = "Welcome to Manage Reservations window, here you can manage reservations and confirm payments! "
        footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"

        stdscr.attron(CYAN)
        stdscr.addstr(height-(height), 1 , title)
        stdscr.attroff(CYAN)

        stdscr.attron(BLACK_CYAN)
        stdscr.addstr(height-1, 0, " " * (width-1))
        stdscr.addstr(height-1, 1, footer)
        stdscr.attroff(BLACK_CYAN)

        rectangle(stdscr, 1, 25, 2, 75)
        rectangle(stdscr, 2, 25, 7, 41)
        rectangle(stdscr, 2, 42, 7, 58)
        rectangle(stdscr, 2, 59, 7, 75)
        stdscr.attron(CYAN)
        stdscr.addstr(1,46, " Our Rooms ")
        stdscr.attroff(CYAN)
        stdscr.addstr(3,26, "Basic Single")
        stdscr.addstr(4,26, "Size: 12")
        stdscr.addstr(5,26, "Price: 500kr")
        stdscr.addstr(6,26, "No extra beds")
        stdscr.addstr(3,43, "Basic Double")
        stdscr.addstr(4,43, "Size: 15")
        stdscr.addstr(5,43, "Price: 600kr")
        stdscr.addstr(6,43, "Up to 1 exbeds")
        stdscr.addstr(3,60, "Deluxe Double")
        stdscr.addstr(4,60, "Size: 18")
        stdscr.addstr(5,60, "Price: 700kr")
        stdscr.addstr(6,60, "Up to 2 exbeds")
        
        main_menu_items = ["Make reservation", "Cancel reservation", "Confirm payment", "Back"]
        for idx, element in enumerate(main_menu_items):
            y = 1 + idx
            if y == current_row:
                stdscr.attron(BLACK_CYAN)
                stdscr.addstr(y, 1, element)
                stdscr.attroff(BLACK_CYAN)
            else:
                stdscr.addstr(y, 1, element)

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 1:
            current_row = current_row - 1
        elif key == curses.KEY_DOWN and current_row < len(main_menu_items):
            current_row = current_row + 1
        elif key == 10:
            if current_row == 1:
                wrapper(make_reservation)
            if current_row == 2:
                wrapper(cancel_reservation)
            if current_row == 3:
                wrapper(confirm_payment)
            if current_row == 4:
                wrapper(main)
        stdscr.refresh()

def customers_manage(stdscr):
    height, width = stdscr.getmaxyx()
    key = 0
    current_row = 1
    stdscr.clear()
    stdscr.refresh()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    CYAN = curses.color_pair(1)
    BLACK_CYAN = curses.color_pair(2)
    search_tooltip = "Here you can search for customers by their last name"
    footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"
    stdscr.attron(CYAN)
    stdscr.addstr(height-(height), 1, search_tooltip)
    stdscr.attroff(CYAN)
    stdscr.attron(BLACK_CYAN)
    stdscr.addstr(height-1, 0, " " * (width-1))
    stdscr.addstr(height-1, 1, footer)
    stdscr.attroff(BLACK_CYAN)
    stdscr.refresh()
    search_box = Textbox(curses.newwin(1, 30, 1, 1))
    curses.curs_set(1)
    search_box.edit()
    curses.curs_set(0)
    search_query = search_box.gather()
    search_query = search_query.strip()
    main_menu_items = SearchCustomers(search_query)
    main_menu_items.append("Back")
    stdscr.clear()
    while True:
        curses.curs_set(0)
        
        # Strings
        title = "Your search results "
        footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"

        stdscr.attron(CYAN)
        stdscr.addstr(height-(height), 1 , title)
        stdscr.attroff(CYAN)

        stdscr.attron(BLACK_CYAN)
        stdscr.addstr(height-1, 0, " " * (width-1))
        stdscr.addstr(height-1, 1, footer)
        stdscr.attroff(BLACK_CYAN)
        for idx, element in enumerate(main_menu_items):
            y = 1 + idx
            if y == current_row:
                stdscr.attron(BLACK_CYAN)
                stdscr.addstr(y, 1, element)
                stdscr.attroff(BLACK_CYAN)
            else:
                stdscr.addstr(y, 1, element)

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 1:
            current_row = current_row - 1
        elif key == curses.KEY_DOWN and current_row < len(main_menu_items):
            current_row = current_row + 1
        elif key == 10:
            if current_row != len(main_menu_items):
                active = main_menu_items[current_row-1]
                parts = active.split(";")
                update_id = parts[-1]
                customer = Customer.query.filter_by(id = update_id).first()
                birthday = customer.birth_date
                stdscr.clear()
                stdscr.addstr(1,abs(int(width/2)), f"First Name: {customer.first_name}")
                stdscr.addstr(2,abs(int(width/2)), f"Last Name: {customer.last_name}")
                stdscr.addstr(3,abs(int(width/2)), f"Birthdate: {customer.birth_date}")
                stdscr.addstr(4,abs(int(width/2)), f"Street Address: {customer.street_address}")
                stdscr.addstr(5,abs(int(width/2)), f"Postal Code: {customer.postal_number}")
                stdscr.addstr(6,abs(int(width/2)), f"City: {customer.city}")
                stdscr.addstr(7,abs(int(width/2)), f"Country: {customer.country}")
                stdscr.addstr(8,abs(int(width/2)), f"E-Mail: {customer.mail}")
                stdscr.addstr(9,abs(int(width/2)), f"Phone Number: {customer.contact_number}")
                current_row = 1
                title = "Update chosen customer to"
                
                first_name_box = Textbox(curses.newwin(1,30, 1, 13))
                last_name_box = Textbox(curses.newwin(1,30, 2, 12))
                day_box = Textbox(curses.newwin(1,3, 3,20))
                month_box = Textbox(curses.newwin(1,3, 3,17))
                year_box = Textbox(curses.newwin(1,5, 3,12))
                address_box = Textbox(curses.newwin(1,40, 4, 10))
                postal_code_box = Textbox(curses.newwin(1,11, 5, 14))
                city_box = Textbox(curses.newwin(1,30, 6, 7))
                country_box = Textbox(curses.newwin(1,20, 7, 10))
                mail_box = Textbox(curses.newwin(1,40, 8, 9))
                number_box = Textbox(curses.newwin(1,15, 9, 17))

                while True:
                    stdscr.attron(CYAN)
                    stdscr.addstr(height-(height), 1 , title)
                    stdscr.attroff(CYAN)
                    stdscr.attron(BLACK_CYAN)
                    stdscr.addstr(height-1, 0, " " * (width-1))
                    stdscr.addstr(height-1, 1, footer)
                    stdscr.attroff(BLACK_CYAN)
                    stdscr.attron(CYAN)
                    try:
                        if not day:
                            pass
                    except UnboundLocalError:
                        stdscr.addstr(3,20, "dd")
                        day = ""
                    try:
                        if not month:
                            pass
                    except UnboundLocalError:
                        stdscr.addstr(3,17, "mm")
                        month = ""
                    try:
                        if not year:
                            pass
                    except UnboundLocalError:
                        stdscr.addstr(3,12, "yyyy")
                        year = ""
                    stdscr.attroff(CYAN)
                    old_values_str = "Old Values"
                    stdscr.attron(CYAN)
                    stdscr.addstr(0,abs(int(width/2)), old_values_str)
                    stdscr.attroff(CYAN)
                    sub_menu_items = ["First Name: ", "Last Name: ", "Birthdate: ", "Address: ", "Postal Code: ", "City: ","Country: ", "E-Mail: ", "Contact Number: ", "Update", "Back"]
                    for idx, element in enumerate(sub_menu_items):
                        y = 1 + idx
                        if y == current_row:
                            stdscr.attron(BLACK_CYAN)
                            stdscr.addstr(y, 1, element)
                            stdscr.attroff(BLACK_CYAN)
                        else:
                            stdscr.addstr(y, 1, element)
                    key = stdscr.getch()
                    if key == curses.KEY_UP and current_row > 1:
                        current_row = current_row - 1
                    elif key == curses.KEY_DOWN and current_row < len(sub_menu_items):
                        current_row = current_row + 1
                    elif key == 10:
                        if current_row == 1:
                            curses.curs_set(1)
                            first_name_box.edit()
                            curses.curs_set(0)
                            new_first_name = first_name_box.gather()
                            customer.first_name = new_first_name.strip()
                        if current_row == 2:
                            curses.curs_set(1)
                            last_name_box.edit()
                            curses.curs_set(0)
                            new_last_name = last_name_box.gather()
                            customer.last_name = new_last_name.strip()
                        if current_row == 3:
                            while True:
                                curses.curs_set(1)
                                year_box.edit()
                                curses.curs_set(0)
                                year = year_box.gather()
                                year = year.strip()
                                if year.isdigit() == True and len(year) == 4:
                                    break
                                else:
                                    footer = "A year has to be 4 numbers ԅ(≖‿≖ԅ)"
                                    stdscr.attron(BLACK_CYAN)
                                    stdscr.addstr(height-1, 0, " " * (width-1))
                                    stdscr.addstr(height-1, 1, footer)
                                    stdscr.attroff(BLACK_CYAN)
                                    stdscr.refresh()
                                    continue
                            while True:
                                curses.curs_set(1)
                                month_box.edit()
                                curses.curs_set(0)
                                month = month_box.gather()
                                month = month.strip()
                                if month.isdigit() == True:
                                    break
                                else:
                                    footer = "A month has to be a number ԅ(≖‿≖ԅ)"
                                    stdscr.attron(BLACK_CYAN)
                                    stdscr.addstr(height-1, 0, " " * (width-1))
                                    stdscr.addstr(height-1, 1, footer)
                                    stdscr.attroff(BLACK_CYAN)
                                    stdscr.refresh()
                                    continue
                            while True:
                                curses.curs_set(1)
                                day_box.edit()
                                curses.curs_set(0)
                                day = day_box.gather()
                                day = day.strip()
                                if day.isdigit() == True:
                                    bdate_str = f"{year}-{month}-{day}"
                                    customer.birth_date = bdate_str
                                    break
                                else:
                                    footer = "A day has to be a number ԅ(≖‿≖ԅ)"
                                    stdscr.attron(BLACK_CYAN)
                                    stdscr.addstr(height-1, 0, " " * (width-1))
                                    stdscr.addstr(height-1, 1, footer)
                                    stdscr.attroff(BLACK_CYAN)
                                    stdscr.refresh()
                                    continue
                        if current_row == 4:
                            curses.curs_set(1)
                            address_box.edit()
                            curses.curs_set(0)
                            new_address = address_box.gather()
                            customer.street_address = new_address.strip()
                        if current_row == 5:
                            curses.curs_set(1)
                            postal_code_box.edit()
                            curses.curs_set(0)
                            new_postal = postal_code_box.gather()
                            customer.postal_number = new_postal.strip()
                        if current_row == 6:
                            curses.curs_set(1)
                            city_box.edit()
                            curses.curs_set(0)
                            new_city = city_box.gather()
                            customer.city = new_city.strip()
                        if current_row == 7:
                            curses.curs_set(1)
                            country_box.edit()
                            curses.curs_set(0)
                            new_country = country_box.gather()
                            customer.country = new_country.strip()
                        if current_row == 8:
                            curses.curs_set(1)
                            mail_box.edit()
                            curses.curs_set(0)
                            new_mail = mail_box.gather()
                            customer.mail = new_mail.strip()
                        if current_row == 9:
                            curses.curs_set(1)
                            number_box.edit()
                            curses.curs_set(0)
                            new_number = number_box.gather()
                            customer.contact_number = new_number.strip()
                        if current_row == 10:
                            bdate_str = f"{birthday}"
                            if year.isdigit() == True:
                                try:
                                    new_birthday = datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y").date
                                except ValueError:
                                    footer = "Are you sure about this date? ԅ(≖‿≖ԅ)"
                                    stdscr.attron(BLACK_CYAN)
                                    stdscr.addstr(height-1, 0, " " * (width-1))
                                    stdscr.addstr(height-1, 1, footer)
                                    stdscr.attroff(BLACK_CYAN)
                                    current_row = 3
                                    continue
                            db.session.commit()
                            stdscr.attron(BLACK_CYAN)
                            footer = "Update SUCCESSFUL! (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧"
                            stdscr.addstr(height-1, 0, " " * (width-1))
                            stdscr.addstr(height-1, 1, footer)
                            stdscr.attroff(BLACK_CYAN)
                            stdscr.refresh()
                            time.sleep(3)
                            wrapper(customers)
                        if current_row == len(sub_menu_items):
                            db.session.rollback()
                            wrapper(customers)
            if current_row == len(main_menu_items):
                wrapper(customers)
        stdscr.refresh()

def customers_register(stdscr):
    key = 0
    current_row = 1
    stdscr.clear()
    stdscr.refresh()

    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    CYAN = curses.color_pair(1)
    BLACK_CYAN = curses.color_pair(2)

    first_name_box = Textbox(curses.newwin(1,30, 1, 13))
    last_name_box = Textbox(curses.newwin(1,30, 2, 12))
    day_box = Textbox(curses.newwin(1,3, 3, 20))
    month_box = Textbox(curses.newwin(1,3, 3, 17))
    year_box = Textbox(curses.newwin(1,5, 3, 12))
    address_box = Textbox(curses.newwin(1,40, 4, 10))
    postal_code_box = Textbox(curses.newwin(1,11, 5, 14))
    city_box = Textbox(curses.newwin(1,30, 6, 7))
    country_box = Textbox(curses.newwin(1,20, 7, 10))
    mail_box = Textbox(curses.newwin(1,40, 8, 9))
    number_box = Textbox(curses.newwin(1,15, 9, 17))

    while True:
        curses.curs_set(0)
        height, width = stdscr.getmaxyx()

        # Strings
        title = "Please fill the form to register a new customer"
        try:
            if not footer:
                pass
        except UnboundLocalError:
            footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"

        stdscr.attron(CYAN)
        stdscr.addstr(height-(height), 1 , title)
        try:
            if not day:
                pass
        except UnboundLocalError:
            stdscr.addstr(3,20, "dd")
            day = ""
        try:
            if not month:
                pass
        except UnboundLocalError:
            stdscr.addstr(3,17, "mm")
            month = ""
        try:
            if not year:
                pass
        except UnboundLocalError:
            stdscr.addstr(3,12, "yyyy")
            year = ""
        stdscr.attroff(CYAN)

        stdscr.attron(BLACK_CYAN)
        stdscr.addstr(height-1, 0, " " * (width-1))
        stdscr.addstr(height-1, 1, footer)
        stdscr.attroff(BLACK_CYAN)
        
        main_menu_items = ["First Name: ", "Last Name: ", "Birthdate: ", "Address: ", "Postal Code: ", "City: ","Country: ", "E-Mail: ", "Contact Number: ", "Register", "Back"]
        for idx, element in enumerate(main_menu_items):
            y = 1 + idx
            if y == current_row:
                stdscr.attron(BLACK_CYAN)
                stdscr.addstr(y, 1, element)
                stdscr.attroff(BLACK_CYAN)
            else:
                stdscr.addstr(y, 1, element)

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 1:
            current_row = current_row - 1
        elif key == curses.KEY_DOWN and current_row < len(main_menu_items):
            current_row = current_row + 1
        elif key == 10:
            if current_row == 1:
                curses.curs_set(1)
                first_name_box.edit()
                curses.curs_set(0)
            if current_row == 2:
                curses.curs_set(1)
                last_name_box.edit()
                curses.curs_set(0)
            if current_row == 3:
                while True:
                    curses.curs_set(1)
                    year_box.edit()
                    curses.curs_set(0)
                    year = year_box.gather()
                    year = year.strip()
                    if year.isdigit() == True and len(year) == 4:
                        break
                    else:
                        footer = "A year has to be 4 numbers ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, 1, footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
                while True:
                    curses.curs_set(1)
                    month_box.edit()
                    curses.curs_set(0)
                    month = month_box.gather()
                    month = month.strip()
                    if month.isdigit() == True:
                        break
                    else:
                        footer = "A month has to be a number ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, 1, footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
                while True:
                    curses.curs_set(1)
                    day_box.edit()
                    curses.curs_set(0)
                    day = day_box.gather()
                    day = day.strip()
                    if day.isdigit() == True:
                        footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ You should have some yummy coffee during break!"
                        break
                    else:
                        footer = "A day has to be a number ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, 1, footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
            if current_row == 4:
                curses.curs_set(1)
                address_box.edit()
                curses.curs_set(0)
            if current_row == 5:
                curses.curs_set(1)
                postal_code_box.edit()
                curses.curs_set(0)
            if current_row == 6:
                curses.curs_set(1)
                city_box.edit()
                curses.curs_set(0)
            if current_row == 7:
                curses.curs_set(1)
                country_box.edit()
                curses.curs_set(0)
            if current_row == 8:
                curses.curs_set(1)
                mail_box.edit()
                curses.curs_set(0)
            if current_row == 9:
                curses.curs_set(1)
                number_box.edit()
                curses.curs_set(0)
            if current_row == 10:
                try:
                    birthday = datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y").date
                except ValueError:
                    footer = "Are you sure about this date? ԅ(≖‿≖ԅ)"
                    current_row = 3
                    continue
                bdate_str = f"{year}-{month}-{day}"
                try:
                    first_name = first_name_box.gather()
                    if first_name.strip() == "":
                        current_row = 1
                        footer = "Did you forget customers first name?! ԅ(≖‿≖ԅ)"
                        continue
                except UnboundLocalError:
                    current_row = 1
                    footer = "Did you forget customers first name?! ԅ(≖‿≖ԅ)"
                    continue
                try:
                    last_name = last_name_box.gather()
                    if last_name.strip() == "":
                        current_row = 2
                        footer = "Oh gosh, does he even have a family? ԅ(≖‿≖ԅ)"
                        continue
                except UnboundLocalError:
                    current_row = 2
                    footer = "Oh gosh, does he even have a family? ԅ(≖‿≖ԅ)"
                    continue
                try:
                    address = address_box.gather()
                    if address.strip() == "":
                        current_row = 4
                        footer = "Where does this one live? ԅ(≖‿≖ԅ)"
                        continue
                except UnboundLocalError:
                    current_row = 4
                    footer = "Where does this one live? ԅ(≖‿≖ԅ)"
                    continue
                try:
                    postal_code = postal_code_box.gather()
                    if postal_code.strip() == "":
                        current_row = 5
                        footer = "Postal Code! ԅ(≖‿≖ԅ)"
                        continue
                except UnboundLocalError:
                    current_row = 5
                    footer = "Postal Code! ԅ(≖‿≖ԅ)"
                    continue
                try:
                    city = city_box.gather()
                    if city.strip() == "":
                        current_row = 6
                        footer = "Can't find'em if we don't know the city! ԅ(≖‿≖ԅ)"
                        continue
                except UnboundLocalError:
                    current_row = 6
                    footer = "Can't find'em if we don't know the city! ԅ(≖‿≖ԅ)"
                    continue
                try:
                    country = country_box.gather()
                    if country.strip() == "":
                        current_row = 7
                        footer = "Sad, has nowhere to belong to :c ԅ(≖‿≖ԅ)"
                        continue
                except UnboundLocalError:
                    current_row = 7
                    footer = "Sad, has nowhere to belong to :c ԅ(≖‿≖ԅ)"
                    continue
                try:
                    mail = mail_box.gather()
                    if mail.strip() == "":
                        current_row = 8
                        footer = "We need to spam that email with commercials. Mohaha! ԅ(≖‿≖ԅ)"
                        continue
                except UnboundLocalError:
                    current_row = 8
                    footer = "We need to spam that email with commercials. Mohaha! ԅ(≖‿≖ԅ)"
                    continue
                try:
                    number = number_box.gather()
                    if number.strip() == "":
                        current_row = 9
                        footer = "Don't forget phone number, those are sellworthy ԅ(≖‿≖ԅ)"
                        continue
                except UnboundLocalError:
                    current_row = 9
                    footer = "Don't forget phone number, those are sellworthy ԅ(≖‿≖ԅ)"
                    continue
                # Insert to database
                InsertCustomer(first_name, last_name, bdate_str, address, postal_code, city, country, mail, number)
                stdscr.attron(BLACK_CYAN)
                footer = "Registration SUCCESSFUL! (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧"
                stdscr.addstr(height-1, 0, " " * (width-1))
                stdscr.addstr(height-1, 1, footer)
                stdscr.attroff(BLACK_CYAN)
                stdscr.refresh()
                time.sleep(3)
                wrapper(customers)
            if current_row == 11:
                wrapper(customers)
        stdscr.refresh()

def customers(stdscr):
    key = 0
    current_row = 1
    stdscr.clear()
    stdscr.refresh()

    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    CYAN = curses.color_pair(1)
    BLACK_CYAN = curses.color_pair(2)

    while True:
        curses.curs_set(0)
        height, width = stdscr.getmaxyx()

        # Strings
        title = "Welcome to Manage Customers window, here you can register new customers or update details about existing ones "
        footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"

        stdscr.attron(CYAN)
        stdscr.addstr(height-(height), 1 , title)
        stdscr.attroff(CYAN)

        stdscr.attron(BLACK_CYAN)
        stdscr.addstr(height-1, 0, " " * (width-1))
        stdscr.addstr(height-1, 1, footer)
        stdscr.attroff(BLACK_CYAN)
        
        main_menu_items = ["Register a customer", "Update a customer", "Delete a customer", "Back"]
        for idx, element in enumerate(main_menu_items):
            y = 1 + idx
            if y == current_row:
                stdscr.attron(BLACK_CYAN)
                stdscr.addstr(y, 1, element)
                stdscr.attroff(BLACK_CYAN)
            else:
                stdscr.addstr(y, 1, element)

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 1:
            current_row = current_row - 1
        elif key == curses.KEY_DOWN and current_row < len(main_menu_items):
            current_row = current_row + 1
        elif key == 10:
            if current_row == 1:
                wrapper(customers_register)
            if current_row == 2:
                wrapper(customers_manage)
            if current_row == 3:
                wrapper(delete_customer)
            if current_row == len(main_menu_items):
                wrapper(main)
        stdscr.refresh()

def main(stdscr):
    key = 0
    current_row = 1
    stdscr.clear()
    stdscr.refresh()

    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    CYAN = curses.color_pair(1)
    BLACK_CYAN = curses.color_pair(2)

    while True:
        curses.curs_set(0)
        height, width = stdscr.getmaxyx()

        # Strings
        title = "Welcome to Pythonic Hotel Management software! Have a great day at work"
        footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ Never give up! ԅ(≖‿≖ԅ)"

        stdscr.attron(CYAN)
        stdscr.addstr(height-(height), 1 , title)
        stdscr.attroff(CYAN)

        stdscr.attron(BLACK_CYAN)
        stdscr.addstr(height-1, 0, " " * (width-1))
        stdscr.addstr(height-1, 1, footer)
        stdscr.attroff(BLACK_CYAN)
        
        main_menu_items = ["Manage Customers", "Manage Reservations", "Exit"]
        for idx, element in enumerate(main_menu_items):
            y = 1 + idx
            if y == current_row:
                stdscr.attron(BLACK_CYAN)
                stdscr.addstr(y, 1, element)
                stdscr.attroff(BLACK_CYAN)
            else:
                stdscr.addstr(y, 1, element)
                

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 1:
            current_row = current_row - 1
        elif key == curses.KEY_DOWN and current_row < len(main_menu_items):
            current_row = current_row + 1
        elif key == 10:
            if current_row == 1:
                wrapper(customers)
            if current_row == 2:
                wrapper(reservations)
            if current_row == 3:
                sys.exit()
        stdscr.refresh()

if __name__  == "__main__":
    with app.app_context():
        # Database init/update
        db.create_all()
        upgrade()
        CreateRooms()

        # Program starts
        KillPastDeadline()
        wrapper(main)