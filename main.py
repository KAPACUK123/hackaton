import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.lang import Builder
from datetime import datetime

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout

from database import (
    connect_db,
    create_user, get_user_by_username, get_all_users, get_all_requests, get_user_by_id,
    create_request, get_requests_by_master, get_request_by_id, update_request_status,
    create_review, get_review_by_request, update_review, delete_user, update_user,
    get_all_equipment, get_equipment_by_id, create_waybill, get_waybills_by_master, get_all_waybills
)

import bcrypt

kivy.require('2.0.0')

# Устанавливаем размер окна для удобства тестирования
Window.size = (400, 600)

# Загружаем разметку из файла KV
Builder.load_file('main.kv')

# Глобальная переменная для хранения информации о текущем пользователе
current_user = {}


# Экран менеджмента
class ScreenManagement(ScreenManager):
    pass


# Экран входа
class LoginScreen(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    role_spinner = ObjectProperty(None)
    message_label = ObjectProperty(None)

    def login(self):
        global current_user
        username = self.username.text.strip()
        password = self.password.text.strip()
        selected_role = self.role_spinner.text.strip()

        if not username or not password or selected_role == 'Выберите роль':
            self.message_label.text = 'Пожалуйста, заполните все поля.'
            return

        # Отладочный вывод
        #print(f"Попытка входа: {username}, выбранная роль: {selected_role}")

        user_info = get_user_by_username(username)
        if user_info:
            stored_password_hash = user_info['password_hash']
            actual_role = user_info['role']
            print(f"Роль пользователя в базе данных: {actual_role}")
            if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash):
                if actual_role == selected_role:
                    current_user = user_info
                    self.username.text = ''
                    self.password.text = ''
                    self.message_label.text = ''
                    if actual_role == 'Мастер':
                        self.manager.current = 'master'
                    elif actual_role == 'Логист':
                        self.manager.current = 'logistician'
                    elif actual_role == 'Администратор':
                        self.manager.current = 'admin'
                    else:
                        self.message_label.text = 'Неизвестная роль пользователя.'
                else:
                    self.message_label.text = 'Вы выбрали неверную роль для этого пользователя.'
            else:
                self.message_label.text = 'Неверный пароль.'
        else:
            self.message_label.text = 'Пользователь с таким именем не найден.'


# Экран регистрации
class RegisterScreen(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    brigade = ObjectProperty(None)
    message_label = ObjectProperty(None)

    def register(self):
        username = self.username.text.strip()
        password = self.password.text.strip()
        brigade = self.brigade.text.strip()

        if not username or not password or not brigade:
            self.message_label.text = 'Пожалуйста, заполните все поля.'
            return

        role = 'Мастер'  # Регистрация доступна только для мастеров

        if create_user(username, password, role, brigade):
            self.manager.current = 'login'
            self.username.text = ''
            self.password.text = ''
            self.brigade.text = ''
            self.message_label.text = ''
        else:
            self.message_label.text = 'Имя пользователя уже занято.'


# Экран мастера
class MasterScreen(Screen):
    def view_requests(self):
        self.manager.get_screen('requests_list').update_requests()
        self.manager.current = 'requests_list'

    def view_waybills(self):
        waybills_screen = self.manager.get_screen('waybills_list')
        waybills_screen.set_previous_screen('master')
        waybills_screen.update_waybills(master_id=current_user['user_id'])
        self.manager.current = 'waybills_list'


# Экран создания заявки
class CreateRequestScreen(Screen):
    equipment_type = ObjectProperty(None)
    quantity = ObjectProperty(None)
    desired_delivery_time = ObjectProperty(None)
    planned_work_duration = ObjectProperty(None)
    distance_to_site = ObjectProperty(None)
    message_label = ObjectProperty(None)

    def submit_request(self):
        equipment_type = self.equipment_type.text.strip()
        quantity = self.quantity.text.strip()
        desired_delivery_time = self.desired_delivery_time.text.strip()
        planned_work_duration = self.planned_work_duration.text.strip()
        distance_to_site = self.distance_to_site.text.strip()

        if not equipment_type or not quantity or not desired_delivery_time or not planned_work_duration or not distance_to_site:
            self.message_label.text = 'Пожалуйста, заполните все поля.'
            return

        try:
            quantity = int(quantity)
            planned_work_duration = float(planned_work_duration)
            distance_to_site = float(distance_to_site)
        except ValueError:
            self.message_label.text = 'Проверьте корректность введенных данных.'
            return

        # Проверка формата времени
        try:
            datetime.strptime(desired_delivery_time, "%Y-%m-%d %H:%M")
        except ValueError:
            self.message_label.text = 'Неверный формат времени. Используйте YYYY-MM-DD HH:MM.'
            return

        # Создание заявки в базе данных
        create_request(current_user['user_id'], equipment_type, quantity, desired_delivery_time, planned_work_duration,
                       distance_to_site)

        # Очистка полей
        self.equipment_type.text = ''
        self.quantity.text = ''
        self.desired_delivery_time.text = ''
        self.planned_work_duration.text = ''
        self.distance_to_site.text = ''
        self.message_label.text = 'Заявка успешно создана.'


# Экран списка заявок
class RequestsListScreen(Screen):
    requests_list = ObjectProperty(None)

    def update_requests(self):
        self.requests_list.clear_widgets()
        try:
            requests = get_requests_by_master(current_user['user_id'])
            if requests:
                for req in requests:
                    req_id = req[0]
                    equipment_type = req[2]
                    status = req[8]
                    btn = Button(text=f'Заявка #{req_id} - {equipment_type} - Статус: {status}', size_hint_y=None,
                                 height=dp(40))
                    btn.bind(on_press=lambda x, req_id=req_id: self.open_request_details(req_id))
                    self.requests_list.add_widget(btn)
            else:
                self.requests_list.add_widget(Label(text='У вас нет заявок.', size_hint_y=None, height=dp(40)))
        except Exception as e:
            print("Ошибка при обновлении списка заявок:", e)
            self.requests_list.add_widget(
                Label(text='Произошла ошибка при загрузке заявок.', size_hint_y=None, height=dp(40)))

    def open_request_details(self, request_id):
        self.manager.get_screen('review').request_id = request_id
        self.manager.get_screen('review').load_review()
        self.manager.current = 'review'


# Экран отзывов
class ReviewScreen(Screen):
    review_input = ObjectProperty(None)
    message_label = ObjectProperty(None)
    request_id = None

    def load_review(self):
        review = get_review_by_request(self.request_id)
        if review:
            self.review_input.text = review[3]
        else:
            self.review_input.text = ''

    def submit_review(self):
        content = self.review_input.text.strip()
        if not content:
            self.message_label.text = 'Отзыв не может быть пустым.'
            return

        review = get_review_by_request(self.request_id)
        if review:
            update_review(review[0], content)
            self.message_label.text = 'Отзыв обновлен.'
        else:
            create_review(self.request_id, current_user['user_id'], content)
            self.message_label.text = 'Отзыв добавлен.'

    def go_back(self):
        self.review_input.text = ''
        self.message_label.text = ''
        self.manager.current = 'requests_list'


# Экран логиста
class LogisticianScreen(Screen):
    def view_requests(self):
        self.manager.current = 'logistician_requests'

    def view_equipment(self):
        equipment_screen = self.manager.get_screen('logistician_equipment')
        equipment_screen.update_equipment()
        self.manager.current = 'logistician_equipment'

    def view_waybills(self):
        waybills_screen = self.manager.get_screen('waybills_list')
        waybills_screen.set_previous_screen('logistician')
        waybills_screen.update_waybills()
        self.manager.current = 'waybills_list'


class LogisticianEquipmentScreen(Screen):
    equipment_list = ObjectProperty(None)

    def update_equipment(self):
        self.equipment_list.clear_widgets()
        equipment = get_all_equipment()
        if equipment:
            for eq in equipment:
                equipment_id = eq[0]
                eq_type = eq[1]
                model = eq[2]
                license_plate = eq[3]
                subdivision = eq[5]
                btn = Button(text=f'{eq_type} {model} - {license_plate} - {subdivision}', size_hint_y=None,
                             height=dp(40))
                self.equipment_list.add_widget(btn)
        else:
            self.equipment_list.add_widget(Label(text='Нет доступной техники.', size_hint_y=None, height=dp(40)))


class LogisticianRequestsScreen(Screen):
    requests_list = ObjectProperty(None)

    def on_enter(self):
        self.update_requests()

    def update_requests(self):
        self.requests_list.clear_widgets()
        try:
            requests = get_all_requests()
            if requests:
                for req in requests:
                    req_id = req[0]
                    master_id = req[1]
                    equipment_type = req[2]
                    status = req[8]
                    btn = Button(text=f'Заявка #{req_id} от мастера #{master_id} - {equipment_type} - Статус: {status}',
                                 size_hint_y=None, height=dp(40))
                    btn.bind(on_press=lambda x, req_id=req_id: self.open_request_details(req_id))
                    self.requests_list.add_widget(btn)
            else:
                self.requests_list.add_widget(Label(text='Нет заявок.', size_hint_y=None, height=dp(40)))
        except Exception as e:
            print("Ошибка при обновлении списка заявок:", e)
            self.requests_list.add_widget(
                Label(text='Произошла ошибка при загрузке заявок.', size_hint_y=None, height=dp(40)))

    def open_request_details(self, request_id):
        detail_screen = self.manager.get_screen('logistician_request_detail')
        detail_screen.request_id = request_id
        detail_screen.load_request()
        self.manager.current = 'logistician_request_detail'


class LogisticianRequestDetailScreen(Screen):
    request_id = NumericProperty(None)
    status_spinner = ObjectProperty(None)
    message_label = ObjectProperty(None)

    def load_request(self):
        request = get_request_by_id(self.request_id)
        if request:
            master_id = request[1]
            equipment_type = request[2]
            quantity = request[3]
            submission_time = request[4]
            desired_delivery_time = request[5]
            planned_work_duration = request[6]
            distance_to_site = request[7]
            status = request[8]

            details = f"""
[b]Заявка #[/b]{self.request_id}
[b]Мастер:[/b] {master_id}
[b]Тип техники:[/b] {equipment_type}
[b]Количество:[/b] {quantity}
[b]Время подачи заявки:[/b] {submission_time}
[b]Желаемое время доставки:[/b] {desired_delivery_time}
[b]Планируемая длительность работы:[/b] {planned_work_duration}
[b]Расстояние до объекта:[/b] {distance_to_site}
[b]Статус:[/b] {status}
"""
            self.ids.request_details.text = details
            self.status_spinner.text = status
        else:
            self.message_label.text = 'Заявка не найдена.'

    def update_status(self):
        new_status = self.status_spinner.text
        if new_status not in ['Ожидание', 'Одобрено', 'Отменено', 'Выполнено']:
            self.message_label.text = 'Пожалуйста, выберите корректный статус.'
            return
        update_request_status(self.request_id, new_status)
        self.message_label.text = 'Статус заявки обновлен.'
        self.load_request()

    def go_back(self):
        self.manager.current = 'logistician_requests'


# Экран путевых листов
class WaybillsListScreen(Screen):
    waybills_list = ObjectProperty(None)
    previous_screen = StringProperty('')

    def set_previous_screen(self, screen_name):
        self.previous_screen = screen_name

    def update_waybills(self, master_id=None):
        self.waybills_list.clear_widgets()
        if master_id:
            waybills = get_waybills_by_master(master_id)
        else:
            waybills = get_all_waybills()

        if waybills:
            for wb in waybills:
                waybill_id = wb[0]
                equipment_id = wb[1]
                request_id = wb[2]
                planned_departure_time = wb[3]
                planned_arrival_time = wb[4]
                planned_work_duration = wb[5]
                actual_departure_time = wb[6] or 'N/A'
                actual_arrival_time = wb[7] or 'N/A'
                equipment = get_equipment_by_id(equipment_id)
                equipment_info = f'{equipment[1]} {equipment[2]} - {equipment[3]}'

                lbl = Label(
                    text=f'Путевой лист #{waybill_id}\nТехника: {equipment_info}\nПлан. выезд: {planned_departure_time}\nПлан. прибытие: {planned_arrival_time}',
                    size_hint_y=None, height=dp(80)
                )
                self.waybills_list.add_widget(lbl)
        else:
            self.waybills_list.add_widget(Label(text='Нет путевых листов.', size_hint_y=None, height=dp(40)))


# Экран администратора
class AdminScreen(Screen):
    def manage_users(self):
        self.manager.current = 'admin_users'

    def view_waybills(self):
        waybills_screen = self.manager.get_screen('waybills_list')
        waybills_screen.set_previous_screen('admin')
        waybills_screen.update_waybills()
        self.manager.current = 'waybills_list'


class AdminUsersScreen(Screen):
    users_list = ObjectProperty(None)

    def on_enter(self):
        self.update_users()

    def update_users(self):
        self.users_list.clear_widgets()
        try:
            users = get_all_users()
            if users:
                for user in users:
                    user_id = user[0]
                    username = user[1]
                    role = user[3]
                    btn = Button(text=f'Пользователь #{user_id} - {username} - Роль: {role}', size_hint_y=None,
                                 height=dp(40))
                    btn.bind(on_press=lambda x, user_id=user_id: self.open_user_details(user_id))
                    self.users_list.add_widget(btn)
            else:
                self.users_list.add_widget(Label(text='Нет пользователей.', size_hint_y=None, height=dp(40)))
        except Exception as e:
            print("Ошибка при обновлении списка пользователей:", e)
            self.users_list.add_widget(
                Label(text='Произошла ошибка при загрузке пользователей.', size_hint_y=None, height=dp(40)))

    def open_user_details(self, user_id):
        detail_screen = self.manager.get_screen('admin_user_detail')
        detail_screen.user_id = user_id
        detail_screen.load_user()
        self.manager.current = 'admin_user_detail'


class AdminUserDetailScreen(Screen):
    user_id = NumericProperty(None)
    username_input = ObjectProperty(None)
    password_input = ObjectProperty(None)
    role_spinner = ObjectProperty(None)
    brigade_input = ObjectProperty(None)
    message_label = ObjectProperty(None)

    def load_user(self):
        user = get_user_by_id(self.user_id)
        if user:
            self.username_input.text = user[1]
            self.password_input.text = ''  # Оставляем пароль пустым
            self.role_spinner.text = user[3]
            self.brigade_input.text = user[4] if user[4] else ''
        else:
            self.message_label.text = 'Пользователь не найден.'

    def save_changes(self):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        role = self.role_spinner.text.strip()
        brigade = self.brigade_input.text.strip() if self.brigade_input.text.strip() else None

        if not username or role == 'Выберите роль':
            self.message_label.text = 'Имя пользователя и роль не могут быть пустыми.'
            return

        # Обновление пользователя
        update_user(self.user_id, username, password, role, brigade)
        self.message_label.text = 'Изменения сохранены.'

    def delete_user(self):
        # Подтверждение удаления
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text='Вы уверены, что хотите удалить пользователя?'))

        buttons = BoxLayout(spacing=10, size_hint_y=None, height=dp(40))
        btn_yes = Button(text='Да')
        btn_no = Button(text='Нет')
        buttons.add_widget(btn_yes)
        buttons.add_widget(btn_no)
        content.add_widget(buttons)

        popup = Popup(title='Подтверждение', content=content, size_hint=(0.8, 0.4))
        btn_yes.bind(on_press=lambda x: self.confirm_delete_user(popup))
        btn_no.bind(on_press=popup.dismiss)
        popup.open()

    def confirm_delete_user(self, popup):
        result = delete_user(self.user_id)
        if result:
            self.message_label.text = 'Пользователь удален.'
            self.manager.get_screen('admin_users').update_users()
            self.manager.current = 'admin_users'
        else:
            self.message_label.text = 'Ошибка при удалении пользователя.'
        popup.dismiss()

    def go_back(self):
        self.manager.current = 'admin_users'


# Основное приложение
class SpecialEquipmentApp(App):
    def build(self):
        sm = ScreenManagement()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(MasterScreen(name='master'))
        sm.add_widget(CreateRequestScreen(name='create_request'))
        sm.add_widget(RequestsListScreen(name='requests_list'))
        sm.add_widget(ReviewScreen(name='review'))
        sm.add_widget(LogisticianScreen(name='logistician'))
        sm.add_widget(LogisticianEquipmentScreen(name='logistician_equipment'))
        sm.add_widget(LogisticianRequestsScreen(name='logistician_requests'))
        sm.add_widget(LogisticianRequestDetailScreen(name='logistician_request_detail'))
        sm.add_widget(WaybillsListScreen(name='waybills_list'))
        sm.add_widget(AdminScreen(name='admin'))
        sm.add_widget(AdminUsersScreen(name='admin_users'))
        sm.add_widget(AdminUserDetailScreen(name='admin_user_detail'))
        return sm

    def logout(self):
        global current_user
        current_user = {}
        self.root.current = 'login'


if __name__ == '__main__':
    SpecialEquipmentApp().run()
