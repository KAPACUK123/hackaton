import sqlite3
import bcrypt
from datetime import datetime

DATABASE_NAME = 'special_equipment_management.db'


def connect_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_user(username, password, role, associated_brigade=None):
    conn = connect_db()
    cursor = conn.cursor()

    # Хешируем пароль
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute('''
            INSERT INTO Users (username, password_hash, role, associated_brigade)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, role, associated_brigade))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_by_username(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM Users WHERE username = ?
    ''', (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        user_dict = {
            'user_id': user[0],
            'username': user[1],
            'password_hash': user[2],
            'role': user[3],
            'associated_brigade': user[4]
        }
        return user_dict
    else:
        return None


def delete_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Ошибка при удалении пользователя: {e}")
        return False
    finally:
        conn.close()


def update_user(user_id, username, password, role, associated_brigade):
    conn = connect_db()
    cursor = conn.cursor()
    # Хешируем пароль
    if password:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    else:
        # Получаем текущий хеш пароля
        cursor.execute('SELECT password_hash FROM Users WHERE user_id = ?', (user_id,))
        password_hash = cursor.fetchone()[0]

    cursor.execute('''
        UPDATE Users
        SET username = ?, password_hash = ?, role = ?, associated_brigade = ?
        WHERE user_id = ?
    ''', (username, password_hash, role, associated_brigade, user_id))
    conn.commit()
    conn.close()


def create_request(master_id, equipment_type, quantity, desired_delivery_time, planned_work_duration, distance_to_site):
    conn = connect_db()
    cursor = conn.cursor()

    submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = 'Ожидание'
    external_order = False

    cursor.execute('''
        INSERT INTO Requests (master_id, equipment_type, quantity, submission_time, desired_delivery_time, planned_work_duration, distance_to_site, status, external_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (master_id, equipment_type, quantity, submission_time, desired_delivery_time, planned_work_duration,
          distance_to_site, status, external_order))

    conn.commit()
    conn.close()


def get_requests_by_master(master_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM Requests WHERE master_id = ?
    ''', (master_id,))
    requests = cursor.fetchall()
    conn.close()
    return requests


def get_request_by_id(request_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Requests WHERE request_id = ?', (request_id,))
    request = cursor.fetchone()
    conn.close()
    return request


def update_request_status(request_id, status):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Requests SET status = ? WHERE request_id = ?
    ''', (status, request_id))
    conn.commit()
    conn.close()


def create_review(request_id, master_id, content):
    conn = connect_db()
    cursor = conn.cursor()

    submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO Reviews (request_id, master_id, content, submission_time)
        VALUES (?, ?, ?, ?)
    ''', (request_id, master_id, content, submission_time))

    conn.commit()
    conn.close()


def get_review_by_request(request_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM Reviews WHERE request_id = ?
    ''', (request_id,))
    review = cursor.fetchone()
    conn.close()
    return review


def update_review(review_id, content):
    conn = connect_db()
    cursor = conn.cursor()

    submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        UPDATE Reviews SET content = ?, submission_time = ? WHERE review_id = ?
    ''', (content, submission_time, review_id))

    conn.commit()
    conn.close()


def create_initial_users():
    # Создаем учетные записи администратора и логиста
    conn = connect_db()
    cursor = conn.cursor()

    users = [
        ('admin', 'admin123', 'Администратор', None),
        ('logistician', 'logist123', 'Логист', None)
    ]

    for username, password, role, brigade in users:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            cursor.execute('''
                INSERT INTO Users (username, password_hash, role, associated_brigade)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, role, brigade))
        except sqlite3.IntegrityError:
            # Если пользователь уже существует, пропускаем
            pass

    conn.commit()
    conn.close()


def create_database():
    conn = connect_db()
    cursor = conn.cursor()

    # Создаем таблицу пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Мастер', 'Логист', 'Администратор')),
        associated_brigade TEXT
    )
    ''')

    # Создаем таблицу техники
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Equipment (
        equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        model TEXT NOT NULL,
        license_plate TEXT UNIQUE NOT NULL,
        tech_passport_data TEXT NOT NULL,
        assigned_to_subdivision TEXT
    )
    ''')

    # Создаем таблицу заявок
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        master_id INTEGER NOT NULL,
        equipment_type TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        submission_time TEXT NOT NULL,
        desired_delivery_time TEXT NOT NULL,
        planned_work_duration REAL NOT NULL,
        distance_to_site REAL NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Ожидание', 'Одобрено', 'Отменено', 'Выполнено')),
        logistician_id INTEGER,
        equipment_assigned INTEGER,
        external_order BOOLEAN NOT NULL DEFAULT 0,
        FOREIGN KEY (master_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (logistician_id) REFERENCES Users(user_id) ON DELETE SET NULL,
        FOREIGN KEY (equipment_assigned) REFERENCES Equipment(equipment_id) ON DELETE SET NULL
    )
    ''')

    # Создаем таблицу путевых листов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Waybills (
        waybill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        request_id INTEGER NOT NULL,
        planned_departure_time TEXT NOT NULL,
        planned_arrival_time TEXT NOT NULL,
        planned_work_duration REAL NOT NULL,
        actual_departure_time TEXT,
        actual_arrival_time TEXT,
        actual_work_duration REAL,
        waiting_time REAL,
        FOREIGN KEY (equipment_id) REFERENCES Equipment(equipment_id) ON DELETE CASCADE,
        FOREIGN KEY (request_id) REFERENCES Requests(request_id) ON DELETE CASCADE
    )
    ''')

    # Создаем таблицу внешних заказов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ExternalOrders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        contractor TEXT NOT NULL,
        equipment_details TEXT NOT NULL,
        cost REAL NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Заказано', 'Выполнено')),
        FOREIGN KEY (request_id) REFERENCES Requests(request_id) ON DELETE CASCADE
    )
    ''')

    # Создаем таблицу отзывов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        master_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        submission_time TEXT NOT NULL,
        FOREIGN KEY (request_id) REFERENCES Requests(request_id) ON DELETE CASCADE,
        FOREIGN KEY (master_id) REFERENCES Users(user_id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()

    # Создаем начальные учетные записи
    create_initial_users()

    # Создаем начальную технику
    create_initial_equipment()


def get_all_requests():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Requests')
    requests = cursor.fetchall()
    conn.close()
    return requests


def get_all_users():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users')
    users = cursor.fetchall()
    conn.close()
    return users


def get_user_by_id(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM Users WHERE user_id = ?
    ''', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_all_equipment():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Equipment')
    equipment = cursor.fetchall()
    conn.close()
    return equipment


def create_initial_equipment():
    conn = connect_db()
    cursor = conn.cursor()

    equipment_list = [
        ('Экскаватор', 'CAT 320', 'А123ВС', 'Паспорт1', 'Участок1'),
        ('Бульдозер', 'Komatsu D85', 'Б456ВГ', 'Паспорт2', 'Участок2'),
        ('Кран', 'Liebherr LTM 1030', 'В789ВВ', 'Паспорт3', 'Участок3'),
    ]

    for eq_type, model, license_plate, passport_data, subdivision in equipment_list:
        try:
            cursor.execute('''
                INSERT INTO Equipment (type, model, license_plate, tech_passport_data, assigned_to_subdivision)
                VALUES (?, ?, ?, ?, ?)
            ''', (eq_type, model, license_plate, passport_data, subdivision))
        except sqlite3.IntegrityError:
            pass  # Пропускаем, если уже существует

    conn.commit()
    conn.close()


def create_waybill(equipment_id, request_id, planned_departure_time, planned_arrival_time, planned_work_duration):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO Waybills (equipment_id, request_id, planned_departure_time, planned_arrival_time, planned_work_duration)
        VALUES (?, ?, ?, ?, ?)
    ''', (equipment_id, request_id, planned_departure_time, planned_arrival_time, planned_work_duration))

    conn.commit()
    conn.close()


def get_waybills_by_master(master_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT Waybills.* FROM Waybills
        INNER JOIN Requests ON Waybills.request_id = Requests.request_id
        WHERE Requests.master_id = ?
    ''', (master_id,))
    waybills = cursor.fetchall()
    conn.close()
    return waybills


def get_all_waybills():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Waybills')
    waybills = cursor.fetchall()
    conn.close()
    return waybills


def get_equipment_by_id(equipment_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Equipment WHERE equipment_id = ?', (equipment_id,))
    equipment = cursor.fetchone()
    conn.close()
    return equipment


def update_waybill_actual_times(waybill_id, actual_departure_time, actual_arrival_time, actual_work_duration,
                                waiting_time):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Waybills
        SET actual_departure_time = ?, actual_arrival_time = ?, actual_work_duration = ?, waiting_time = ?
        WHERE waybill_id = ?
    ''', (actual_departure_time, actual_arrival_time, actual_work_duration, waiting_time, waybill_id))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    create_database()
    print("База данных успешно создана.")
