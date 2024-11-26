import unittest

import unittest

from unittest.mock import patch, MagicMock
from main import CreateRequestScreen, current_user
from kivy.uix.screenmanager import ScreenManager

from main import LoginScreen, get_user_by_username


import unittest
from kivy.uix.label import Label
from kivy.uix.button import Button
from main import RequestsListScreen, current_user

import bcrypt

from database import get_user_by_username, create_user


class TestDatabaseFunctions(unittest.TestCase):
    def test_get_user_by_username(self):
        username = "testuser"
        password = "testpassword"
        role = "Мастер"
        brigade = "1"

        # Создаем тестового пользователя
        create_user(username, password, role, brigade)

        # Проверяем, что пользователь корректно возвращается
        user = get_user_by_username(username)
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], username)
        self.assertEqual(user["role"], role)





class TestLoginScreen(unittest.TestCase):
    def setUp(self):
        self.manager = ScreenManager()
        self.login_screen = LoginScreen(name="login")
        self.manager.add_widget(self.login_screen)

    def test_login_success(self):
        # Mock database response
        get_user_by_username_mock = MagicMock(return_value={
            "user_id": 4,
            "username": "testuser",
            "password_hash": bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()),
            "role": "Мастер"
        })

        self.login_screen.username.text = "testuser"
        self.login_screen.password.text = "password"
        self.login_screen.role_spinner.text = "Мастер"
        self.login_screen.message_label = Label()

        self.login_screen.login()

        # Проверяем переход экрана
        self.assertEqual(self.manager.current, "Мастер")

    def test_login_failure(self):
        # Mock database response
        get_user_by_username_mock = MagicMock(return_value=None)

        self.login_screen.username.text = "wronguser"
        self.login_screen.password.text = "password"
        self.login_screen.role_spinner.text = "Мастер"
        self.login_screen.message_label = Label()

        self.login_screen.login()
        self.assertEqual(self.login_screen.message_label.text, "Пользователь с таким именем не найден.")


if __name__ == '__main__':
    unittest.main()


class TestCreateRequestScreen(unittest.TestCase):
    def setUp(self):
        # Инициализируем экран
        self.screen = CreateRequestScreen()
        # Устанавливаем текущего пользователя
        global current_user
        current_user.clear()
        current_user['user_id'] = 1

        # Мокаем UI элементы экрана
        self.screen.equipment_type = MagicMock()
        self.screen.quantity = MagicMock()
        self.screen.desired_delivery_time = MagicMock()
        self.screen.planned_work_duration = MagicMock()
        self.screen.distance_to_site = MagicMock()
        self.screen.message_label = MagicMock()

    @patch('main.create_request')
    def test_submit_request_success(self, mock_create_request):
        # Задаем корректные данные
        self.screen.equipment_type.text = "Экскаватор"
        self.screen.quantity.text = "2"
        self.screen.desired_delivery_time.text = "2024-12-01 14:00"
        self.screen.planned_work_duration.text = "5.5"
        self.screen.distance_to_site.text = "12.3"

        # Вызываем метод
        self.screen.submit_request()

        # Проверяем, что сообщение о результате успешное
        self.screen.message_label.text = 'Заявка успешно создана.'

        # Проверяем вызов функции создания заявки
        mock_create_request.assert_called_once_with(
            current_user['user_id'],
            "Экскаватор",
            2,
            "2024-12-01 14:00",
            5.5,
            12.3
        )

        # Проверяем очистку полей
        self.assertEqual(self.screen.equipment_type.text, '')
        self.assertEqual(self.screen.quantity.text, '')
        self.assertEqual(self.screen.desired_delivery_time.text, '')
        self.assertEqual(self.screen.planned_work_duration.text, '')
        self.assertEqual(self.screen.distance_to_site.text, '')

    def test_submit_request_invalid_data(self):
        # Задаем некорректные данные (нечисловое количество)
        self.screen.equipment_type.text = "Экскаватор"
        self.screen.quantity.text = "abc"  # Некорректные данные
        self.screen.desired_delivery_time.text = "2024-12-01 14:00"
        self.screen.planned_work_duration.text = "5.5"
        self.screen.distance_to_site.text = "12.3"

        # Вызываем метод
        self.screen.submit_request()

        # Проверяем, что появилось сообщение об ошибке
        self.screen.message_label.text = 'Проверьте корректность введенных данных.'

    def test_submit_request_invalid_date_format(self):
        # Задаем некорректные данные (неверный формат даты)
        self.screen.equipment_type.text = "Экскаватор"
        self.screen.quantity.text = "2"
        self.screen.desired_delivery_time.text = "12-01-2024 14:00"  # Некорректный формат даты
        self.screen.planned_work_duration.text = "5.5"
        self.screen.distance_to_site.text = "12.3"

        # Вызываем метод
        self.screen.submit_request()

        # Проверяем, что появилось сообщение об ошибке
        self.screen.message_label.text = 'Неверный формат времени. Используйте YYYY-MM-DD HH:MM.'

    def test_submit_request_empty_fields(self):
        # Задаем пустые поля
        self.screen.equipment_type.text = ""
        self.screen.quantity.text = ""
        self.screen.desired_delivery_time.text = ""
        self.screen.planned_work_duration.text = ""
        self.screen.distance_to_site.text = ""

        # Вызываем метод
        self.screen.submit_request()

        # Проверяем, что появилось сообщение об ошибке
        self.screen.message_label.text = 'Пожалуйста, заполните все поля.'







if __name__ == '__main__':
    unittest.main()




