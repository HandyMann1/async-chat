import asyncio

clients = {}
clients_lock = asyncio.Lock()


async def handle_client(reader, writer):  # основная работаа сервера
    addr = writer.get_extra_info('peername')
    print(f"New connection: {addr}")

    try:
        username = (await reader.readline()).decode().strip()
        room = (await reader.readline()).decode().strip()

        async with clients_lock:
            if room not in clients:
                clients[room] = []
            clients[room].append((username, writer))
            print(f"Client {username} {addr} joined the room {room}")

            await send_active_users_to_room(room)
            await send_message_to_room(room, f"{username} joined the room.")

        while True:
            data = await reader.readline()
            if not data:
                break

            message = data.decode().strip()

            if message.startswith("FILE:"):
                await handle_file_transfer(reader, message[5:], username, room)
            else:
                print(f"{username} ({addr}) in room {room}: {message}")
                await send_message_to_room(room, f"{message}")

    except Exception as e:
        print(f"Client error {username}: {e}")
    finally:
        async with clients_lock:
            if room in clients:
                clients[room] = [client for client in clients[room] if client[1] != writer]
                if not clients[room]:
                    del clients[room]
                await send_active_users_to_room(room)

        print(f"Client {username} {addr} left the room {room}")
        await send_message_to_room(room, f"{username} left the room.")
        writer.close()
        await writer.wait_closed()


async def handle_file_transfer(reader, filename, username, room):  # обработка отправки файла
    await send_message_to_room(room, f"{username} is sending a file: {filename}")

    size_data = await reader.readline()

    try:
        file_size = int(size_data.decode().strip())
    except ValueError:
        print(f"Invalid file size received from {username}.")
        return

    with open(filename, 'wb') as f:  # считываем файл и отправляем его чанками всем остальным
        bytes_received = 0
        while bytes_received < file_size:
            chunk = await reader.read(1024)
            if not chunk:
                break
            f.write(chunk)
            bytes_received += len(chunk)

    await send_message_to_room(room, f"File received: {filename}")


async def send_active_users_to_room(room):  # отправляет никнеймы всех участников комнаты на данный момент
    if room in clients:
        active_users = [client[0] for client in clients[room]]
        message = f"Active users in {room}: {', '.join(active_users)}\n"
        for _, writer in clients[room]:
            writer.write(message.encode())
            await writer.drain()


async def send_message_to_room(room, message):  # отправка сообщений в чат-комнату
    if room in clients:
        for username, writer in clients[room]:
            writer.write(f"{message}\n".encode())
            await writer.drain()


async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    addr = server.sockets[0].getsockname()
    print(f"Server works on {addr}")
    async with server:
        await server.serve_forever()


asyncio.run(main())
