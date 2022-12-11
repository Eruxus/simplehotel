# Immports for curses
import curses
from curses import wrapper
from curses.textpad import Textbox
# Imports for flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
# General imports
from datetime import datetime
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

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(50), unique=False, nullable=False)
    size = db.Column(db.Integer, unique=False, nullable=False)
    is_double = db.Column(db.Boolean, unique=False, nullable=True)
    daily_price = db.Column(db.Integer, unique=False, nullable=False)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_in = db.Column(db.DateTime, unique=False, nullable=False)
    check_out = db.Column(db.DateTime, unique=False, nullable=False)
    extra_beds = db.Column(db.Integer, unique=False, nullable=False)
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
def SearchCustomers(query) -> list:
    listan = []
    result = Customer.query.filter(Customer.last_name.contains(query)).all()
    for x in result:
        if f"{x.last_name}".lower() == query.lower():
            listan.append(f"{x.first_name} {x.last_name} id{x.id}")
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
    search_box.edit()
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
                parts = active.split("id")
                update_id = parts[-1]
                customer = ""
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
                while True:
                    stdscr.attron(CYAN)
                    stdscr.addstr(height-(height), 1 , title)
                    stdscr.attron(BLACK_CYAN)
                    stdscr.addstr(height-1, 0, " " * (width-1))
                    stdscr.addstr(height-1, 1, footer)
                    stdscr.attroff(BLACK_CYAN)
                    try:
                        if not day:
                            pass
                    except UnboundLocalError:
                        stdscr.addstr(3,int(width/2+13), "dd")
                        day = ""
                    try:
                        if not month:
                            pass
                    except UnboundLocalError:
                        stdscr.addstr(3,int(width/2+10), "mm")
                        month = ""
                    try:
                        if not year:
                            pass
                    except UnboundLocalError:
                        stdscr.addstr(3,int(width/2+5), "yyyy")
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
                            first_name_box = Textbox(curses.newwin(1,30, 1, 13))
                            first_name_box.edit()
                            new_first_name = first_name_box.gather()
                            customer.first_name = new_first_name.strip()
                        if current_row == 2:
                            last_name_box = Textbox(curses.newwin(1,30, 2, 12))
                            last_name_box.edit()
                            new_last_name = last_name_box.gather()
                            customer.last_name = new_last_name.strip()
                        if current_row == 3:
                            day_box = Textbox(curses.newwin(1,3, 3,20))
                            month_box = Textbox(curses.newwin(1,3, 3,17))
                            year_box = Textbox(curses.newwin(1,5, 3,12))
                            while True:
                                year_box.edit()
                                year = year_box.gather()
                                year = year.replace(" ", "")
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
                                month_box.edit()
                                month = month_box.gather()
                                month = month.replace(" ", "")
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
                                day_box.edit()
                                day = day_box.gather()
                                day = day.replace(" ", "")
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
                            address_box = Textbox(curses.newwin(1,40, 4, 10))
                            address_box.edit()
                            new_address = address_box.gather()
                            customer.street_address = new_address.strip()
                        if current_row == 5:
                            postal_code_box = Textbox(curses.newwin(1,11, 5, 14))
                            postal_code_box.edit()
                            new_postal = postal_code_box.gather()
                            customer.postal_number = new_postal.strip()
                        if current_row == 6:
                            city_box = Textbox(curses.newwin(1,30, 6, 7))
                            city_box.edit()
                            new_city = city_box.gather()
                            customer.city = new_city.strip()
                        if current_row == 7:
                            country_box = Textbox(curses.newwin(1,20, 7, 10))
                            country_box.edit()
                            new_country = country_box.gather()
                            customer.country = new_country.strip()
                        if current_row == 8:
                            mail_box = Textbox(curses.newwin(1,40, 8, 9))
                            mail_box.edit()
                            new_mail = mail_box.gather()
                            customer.mail = new_mail.strip()
                        if current_row == 9:
                            number_box = Textbox(curses.newwin(1,15, 9, 17))
                            number_box.edit()
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

    while True:
        curses.curs_set(0)
        height, width = stdscr.getmaxyx()

        # Strings
        title = "Please fill the form to register a new customer "
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
                first_name_box = Textbox(curses.newwin(1,30, 1, 13))
                first_name_box.edit()
            if current_row == 2:
                last_name_box = Textbox(curses.newwin(1,30, 2, 12))
                last_name_box.edit()
            if current_row == 3:
                day_box = Textbox(curses.newwin(1,3, 3, 20))
                month_box = Textbox(curses.newwin(1,3, 3, 17))
                year_box = Textbox(curses.newwin(1,5, 3, 12))
                while True:
                    year_box.edit()
                    year = year_box.gather()
                    year = year.replace(" ", "")
                    if year.isdigit() == True and len(year) == 4:
                        break
                    else:
                        footer = "A year has to be 4 numbers ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, int((width/2)-(len(footer)/2)), footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
                while True:
                    month_box.edit()
                    month = month_box.gather()
                    month = month.replace(" ", "")
                    if month.isdigit() == True:
                        break
                    else:
                        footer = "A month has to be a number ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, int((width/2)-(len(footer)/2)), footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
                while True:
                    day_box.edit()
                    day = day_box.gather()
                    day = day.replace(" ", "")
                    if day.isdigit() == True:
                        footer = "(ﾉ◕ヮ◕)ﾉ*:・ﾟ✧ You should have some yummy coffee during break!"
                        break
                    else:
                        footer = "A day has to be a number ԅ(≖‿≖ԅ)"
                        stdscr.attron(BLACK_CYAN)
                        stdscr.addstr(height-1, 0, " " * (width-1))
                        stdscr.addstr(height-1, int((width/2)-(len(footer)/2)), footer)
                        stdscr.attroff(BLACK_CYAN)
                        stdscr.refresh()
                        continue
            if current_row == 4:
                address_box = Textbox(curses.newwin(1,40, 4, 10))
                address_box.edit()
            if current_row == 5:
                postal_code_box = Textbox(curses.newwin(1,11, 5, 14))
                postal_code_box.edit()
            if current_row == 6:
                city_box = Textbox(curses.newwin(1,30, 6, 7))
                city_box.edit()
            if current_row == 7:
                country_box = Textbox(curses.newwin(1,20, 7, 10))
                country_box.edit()
            if current_row == 8:
                mail_box = Textbox(curses.newwin(1,40, 8, 9))
                mail_box.edit()
            if current_row == 9:
                number_box = Textbox(curses.newwin(1,15, 9, 17))
                number_box.edit()
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
                except UnboundLocalError:
                    current_row = 1
                    footer = "Did you forget customers first name?! ԅ(≖‿≖ԅ)"
                    continue
                try:
                    last_name = last_name_box.gather()
                except UnboundLocalError:
                    current_row = 2
                    footer = "Oh gosh, does he even have a family? ԅ(≖‿≖ԅ)"
                    continue
                try:
                    address = address_box.gather()
                except UnboundLocalError:
                    current_row = 4
                    footer = "Where does this one live? ԅ(≖‿≖ԅ)"
                    continue
                try:
                    postal_code = postal_code_box.gather()
                except UnboundLocalError:
                    current_row = 5
                    footer = "Postal Code! ԅ(≖‿≖ԅ)"
                    continue
                try:
                    city = city_box.gather()
                except UnboundLocalError:
                    current_row = 6
                    footer = "Can't find'em if we don't know the city! ԅ(≖‿≖ԅ)"
                    continue
                try:
                    country = country_box.gather()
                    country = country.strip()
                except UnboundLocalError:
                    current_row = 7
                    footer = "Sad, has nowhere to belong to :c ԅ(≖‿≖ԅ)"
                    continue
                try:
                    mail = mail_box.gather()
                except UnboundLocalError:
                    current_row = 8
                    footer = "We need to spam that email with commercials. Mohaha! ԅ(≖‿≖ԅ)"
                    continue
                try:
                    number = number_box.gather()
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
        
        main_menu_items = ["Register a customer", "Update a customer", "Back"]
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
                pass
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
        wrapper(main)