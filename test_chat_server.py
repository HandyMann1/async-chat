import os
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import tkinter as tk
from client import send_text_message, receive_messages, send_file


class TestChatClient(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def test_send_message(self):
        mock_writer = AsyncMock()
        global username
        username = "TestUser"
        message = "Hello, World!"

        # Выполнение
        self.loop.run_until_complete(send_text_message(mock_writer, message))

        # Проверка
        expected_message = f"{username}({datetime.now().strftime('%H:%M:%S')}): {message}\n"
        mock_writer.write.assert_called_once_with(expected_message.encode())
        mock_writer.drain.assert_called_once()

    @patch('chat_client.active_users_widget')
    @patch('chat_client.text_widget')
    async def test_receive_messages(self, mock_text_widget, mock_active_users_widget):
        # Подготовка
        mock_reader = AsyncMock()
        mock_reader.read.side_effect = [b"Active users: User1, User2\n", b"User1 joined the room\n", b"User2: Hello!\n",
                                        b'']

        # Выполнение
        await receive_messages(mock_reader, mock_text_widget, mock_active_users_widget)

        # Проверка
        mock_active_users_widget.config.assert_called_with(state=tk.NORMAL)
        mock_active_users_widget.delete.assert_called_once()
        mock_active_users_widget.insert.assert_called_with(tk.END, "Active users: User1, User2\n")
        mock_active_users_widget.config.assert_called_with(state=tk.DISABLED)

        # Проверка текстовых сообщений
        mock_text_widget.insert.assert_any_call(tk.END, "User1 joined the room\n")
        mock_text_widget.insert.assert_any_call(tk.END, "User2: Hello!\n")

    def test_send_file(self):
        # Подготовка
        mock_writer = AsyncMock()
        file_path = "test_file.txt"

        with open(file_path, 'wb') as f:
            f.write(b'This is a test file.')

        # Выполнение
        self.loop.run_until_complete(send_file(mock_writer, file_path))

        # Проверка
        expected_file_size = os.path.getsize(file_path)

        mock_writer.write.assert_any_call(f"FILE:{os.path.basename(file_path)}\n".encode())
        mock_writer.write.assert_any_call(f"{expected_file_size}\n".encode())

    def tearDown(self):
        self.loop.close()


if __name__ == '__main__':
    unittest.main()
