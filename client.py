import asyncio
import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, filedialog

asyncio_loop = None
reader = None
writer = None
username = None


async def receive_messages(reader, message_widget, user_widget):  # Постоянная прослушка сообщений
    while True:
        data = await reader.read(100)
        if not data:
            break

        message = data.decode()
        if message.startswith("Active users"):
            user_widget.config(state=tk.NORMAL)
            user_widget.delete(1.0, tk.END)
            user_widget.insert(tk.END, message + '\n')
            user_widget.config(state=tk.DISABLED)
        elif "joined the room" in message or "left the room" in message:
            message_widget.insert(tk.END, f"{message}\n")
            message_widget.see(tk.END)
        else:
            message_widget.insert(tk.END, f"{message}\n")
            message_widget.see(tk.END)


async def send_text_message(writer, message):  # отправить текстовое сообщение
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_message = f"{username}({timestamp}): {message}"
    writer.write((full_message + '\n').encode())
    await writer.drain()


async def send_file(writer, file_path):  # отправить файл
    writer.write(f"FILE:{os.path.basename(file_path)}\n".encode())
    await writer.drain()

    file_size = os.path.getsize(file_path)
    writer.write(f"{file_size}\n".encode())
    await writer.drain()

    with open(file_path, 'rb') as file:
        while chunk := file.read(1024):
            writer.write(chunk)
            await writer.drain()

    writer.write(f"Finished sending file: {os.path.basename(file_path)}\n".encode())
    await writer.drain()


def on_send_button_click():  # при нажатии на send
    message = entry_widget.get()
    entry_widget.delete(0, tk.END)
    asyncio.run_coroutine_threadsafe(send_text_message(writer, message), asyncio_loop)


def on_send_file_button_click():  # при нажатии на send file
    file_path = filedialog.askopenfilename()
    if file_path:
        asyncio.run_coroutine_threadsafe(send_file(writer, file_path), asyncio_loop)


async def register_client(ip, username, room):  # подключение клиента к комнате
    global reader, writer
    reader, writer = await asyncio.open_connection(ip, 8888)
    writer.write(f"{username}\n".encode())
    await writer.drain()
    writer.write(f"{room}\n".encode())
    await writer.drain()

    print(f"Client {username} registered in room {room}")
    asyncio.create_task(receive_messages(reader, text_widget, active_users_widget))


def start_chat(ip, username, room):  # начать чат(подключение клиента к серверу)
    asyncio.run_coroutine_threadsafe(register_client(ip, username, room), asyncio_loop)
    root.deiconify()


async def main():
    global reader, writer
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    asyncio.create_task(receive_messages(reader, text_widget, active_users_widget))


def start_client():
    global asyncio_loop
    asyncio_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio_loop)
    asyncio_loop.run_forever()


def initial_data_registration():  # создание окна для подключения к комнате
    dialog = tk.Toplevel(root)
    dialog.title("Connect to Chat Server")

    form_frame = tk.Frame(dialog, padx=10, pady=10)
    form_frame.pack(padx=10, pady=10)

    tk.Label(form_frame, text="Server IP:").grid(row=0, column=0, sticky="w", pady=5)
    ip_entry = tk.Entry(form_frame)
    ip_entry.insert(0, "127.0.0.1")
    ip_entry.grid(row=0, column=1)

    tk.Label(form_frame, text="Username:").grid(row=1, column=0, sticky="w", pady=5)
    username_entry = tk.Entry(form_frame)
    username_entry.grid(row=1, column=1)

    tk.Label(form_frame, text="Room Name:").grid(row=2, column=0, sticky="w", pady=5)
    room_entry = tk.Entry(form_frame)
    room_entry.grid(row=2, column=1)

    def on_confirm():  # cценарий при нажатии на "connect" в меню регистрации
        global username
        ip = ip_entry.get()
        username = username_entry.get()
        room = room_entry.get()

        if ip and username and room:
            start_chat(ip, username, room)
            dialog.destroy()

    connect_button = tk.Button(form_frame, text="Connect", command=on_confirm,
                               bg="#4CAF50", fg="white")
    connect_button.grid(row=4, columnspan=2, pady=(10, 0))


def center_window(window, width, height):  # центрирование окна
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    position_top = int(screen_height / 2 - height / 2)
    position_left = int(screen_width / 2 - width / 2)

    window.geometry(f'{width}x{height}+{position_left}+{position_top}')


async def disconnect_client():  # отключение клиента
    global writer
    if writer:
        writer.close()
        await writer.wait_closed()
        root.destroy()


def on_disconnect_button_click():  # сценарии при нажатии на "disconnect" в чате
    asyncio.run_coroutine_threadsafe(disconnect_client(), asyncio_loop)


# Tkinter GUI Setup
root = tk.Tk()
root.geometry("800x450")
root.title("Chat Client")
center_window(root, 800, 450)
root.withdraw()

main_frame = tk.Frame(root)
main_frame.pack(padx=10, pady=10)

# Active Users Frame
active_users_frame = tk.LabelFrame(main_frame, text="Active Users", padx=10, pady=10)
active_users_frame.pack(fill="x", padx=5)

active_users_widget = tk.Text(active_users_frame,
                              height=1,
                              wrap=tk.WORD,
                              bg="#f0f0f0",
                              fg="black",
                              state=tk.DISABLED)
active_users_widget.pack(fill="x")

# Chat Messages Frame
chat_frame = tk.LabelFrame(main_frame,
                           text="Chat Messages",
                           padx=10,
                           pady=10)
chat_frame.pack(fill="both", expand=True)

text_widget = scrolledtext.ScrolledText(chat_frame,
                                        wrap=tk.WORD,
                                        height=15,
                                        bg="#ffffff",
                                        fg="black")
text_widget.pack(fill="both", expand=True)

input_frame = tk.Frame(main_frame)
input_frame.pack(padx=5)

entry_widget = tk.Entry(input_frame)
entry_widget.pack(side="left", fill="x", expand=True)
entry_widget.insert(0, "Enter your message...")
entry_widget.config(fg="grey")


def clear_placeholder(event):
    if entry_widget.get() == "Enter your message...":
        entry_widget.delete(0, "end")
        entry_widget.config(fg="black")


def restore_placeholder(event):
    if entry_widget.get() == "":
        entry_widget.insert(0, "Enter your message...")
        entry_widget.config(fg="grey")


entry_widget.bind("<FocusIn>", clear_placeholder)
entry_widget.bind("<FocusOut>", restore_placeholder)
entry_widget.bind("<Return>", lambda event: on_send_button_click())

send_button = tk.Button(input_frame,
                        text="Send",
                        command=on_send_button_click,
                        bg="#4CAF50",
                        fg="white")
send_button.pack(side="right", padx=(5, 0))

send_file_button = tk.Button(input_frame,
                             text="Send File",
                             command=lambda: on_send_file_button_click(),
                             bg="#2196F3",
                             fg="white")
send_file_button.pack(side="right", padx=(5, 0))

# Disconnect Button Frame
disconnect_frame = tk.Frame(main_frame)
disconnect_frame.pack(pady=(5, 0))

disconnect_button = tk.Button(disconnect_frame,
                              text="Disconnect",
                              command=on_disconnect_button_click,
                              bg="#ff6666",
                              fg="#ffffff")
disconnect_button.pack(side="right")

client_thread = threading.Thread(target=start_client,
                                 daemon=True)
client_thread.start()

initial_data_registration()

root.protocol("WM_DELETE_WINDOW", lambda: asyncio.run_coroutine_threadsafe(disconnect_client(), asyncio_loop))
root.mainloop()
