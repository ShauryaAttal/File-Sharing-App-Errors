import socket
from threading import Thread
from tkinter import *
from tkinter import ttk
import time

import select
import ftplib
import os
import ntpath
from ftplib import FTP
from pathlib import Path
from tkinter import filedialog

# FTP SERVER
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

is_dirt_exists = os.path.isdir("shared_files")
if not is_dirt_exists:
    os.makedirs("shared_files")

IP_ADDRESS = "127.0.0.1"
PORT = 8000
SERVER = None
Buffer_size = 4096


# client = ip_ad + port
clients = {}


def removeClient(client_name):
    try:
        if client_name in clients:
            del clients[client_name]

    except KeyError:
        pass


def sendTextMessage(client_name, message):
    global clients

    other_client_name = clients["client_name"]["connected_with"]
    # other client ip_ad and port
    other_client_socket = clients[other_client_name]["client"]
    final_message = client_name + " > " + message
    other_client_socket.send(final_message.encode("utf-8"))


def handleErrorMessage(client):
    messgae = """
    You need to connect with one of the client first to chat or share files, Click on referesh to see all avaialble users
    """
    client.send(messgae.encode("utf-8"))


def handleShowLists(client):
    global clients
    counter = 0
    for c in clients:
        # print(c)
        counter += 1
        client_address = clients[c]["address"][0]
        connected_with = clients[c]["connected_with"]
        message = ""
        if connected_with:
            message = f"{counter},{c},{client_address}, connected with {connected_with},tiul,\n"
        else:
            message = f"{counter},{c},{client_address}, Available,tiul,\n"
        client.send(message.encode())
        time.sleep(1)


def handleClientConnection(message, client, client_name):
    global clients, Buffer_size
    print("message: ", message)
    entered_client_name = message[8:].strip()
    if entered_client_name in clients:
        if not clients[client_name]["connected_with"]:
            clients[entered_client_name]["connected_with"] = client_name
            clients[client_name]["connected_with"] = entered_client_name

            other_client_socket = clients[entered_client_name]["client"]
            greet_Msg = f"hello, {entered_client_name} {client_name} connected with you"
            other_client_socket.send(greet_Msg.encode("utf-8"))

            # still pending
            msg = f"You are successfully connected with {entered_client_name}"
            client.send(msg.encode())

        else:
            other_client_name = clients[client_name]["connected_with"]
            msg = f"You are already connected with {other_client_name}"
            client.send(msg.encode())


def handleClientDisConnect(message, client, client_name):
    # still pending
    print("message: ", message)
    global clients
    entered_client_name = message[11:].strip()
    if entered_client_name in clients:
        clients[entered_client_name]["connected_with"] = ""
        clients[client_name]["connected_with"] = ""

        other_client_socket = clients[entered_client_name]["client"]

        greet_message = f"Hello, {entered_client_name} you are successfully disconnected with {client_name} !!!"
        other_client_socket.send(greet_message.encode())

        msg = f"You are successfully disconnected with {entered_client_name}"
        client.send(msg.encode())


def handleSendFile(client_name, file_name, file_size):
    global clients
    clients[client_name]["file_name"] = file_name
    clients[client_name]["file_size"] = file_size
    other_client_name = clients[client_name]["connected_with"]
    other_client_socket = clients[other_client_name]["client"]
    msg = f"\n{client_name} wants to send {file_name} with a size of {file_size} bytes. Do you want to download ?"
    other_client_socket.send(msg.encode("utf-8"))
    time.sleep(2)

    msgToDownload = f"Download: {file_name}"
    other_client_socket.send(msg.encode("utf-8"))


def grantAccess(client_name):
    global clients
    other_client_name = clients[client_name]["connected_with"]
    other_client_socket = clients[other_client_name]["client"]
    msg = "access granted"
    other_client_socket.send(msg.encode("utf-8"))


def declineAccess(client_name):
    global clients
    other_client_name = clients[client_name]["connected_with"]
    other_client_socket = clients[other_client_name]["client"]
    msg =" denied access"
    other_client_socket.send(msg.encode("utf-8"))


def handleMessages(client, message, client_name):
    # print("message: ",message)
    if message == "show list":
        handleShowLists(client)
    elif message[:7] == "connect":
        handleClientConnection(message, client, client_name)
    elif message[:10] == "disconnect":
        handleClientDisConnect(message, client, client_name)
    elif message[:4] == "send":
        file_name = message.split(" ")[1]
        file_size = int(message.split(" ")[2])
        handleSendFile(client_name, file_name, file_size)
        print(client_name + " " + file_name + " " + file_size)
    elif message == "y" or message == "yes":
        grantAccess(client_name)
    elif message == "n" or message == "no":
        declineAccess(client_name)

    else:
        connected = clients[client_name]["connected_with"]
        # print("c:",connected)
        if connected:
            sendTextMessage(client_name, message)
        else:
            handleErrorMessage(client)


def handleClient(client, client_name):
    global clients, SERVER, Buffer_size
    welMsg = "Welcome, You are now connected to server\nClick on Refersh button to get all client list\n"
    client.send(welMsg.encode())
    while True:
        try:
            Buffer_size = clients[client_name]["file_size"]
            chunk = client.recv(Buffer_size)
            message = chunk.decode().strip().lower()
            print("Msg from client:  ", message)
            # print("messages:  ",message)
            if message:
                handleMessages(client, message, client_name)
            else:
                removeClient(client_name)

        except:
            pass


def acceptConnections():
    global SERVER
    global clients, Buffer_size

    while True:
        client, addr = SERVER.accept()
        client_name = client.recv(Buffer_size).decode().lower()
        clients[client_name] = {
            "client": client,
            "address": addr,
            "connected_with": "",
            "file_name": "",
            "file_size": 4096,
        }
        # print(f"Conncetion is built with {client_name}")
        print("Data of Clients:   ", clients)
        thread = Thread(target=handleClient, args=(client, client_name))
        thread.start()


def ftp():
    global IP_ADDRESS

    authorizer = DummyAuthorizer()
    authorizer.add_user("student", "student", ".", perm="elradfmw")

    handler = FTPHandler
    handler.authorizer = authorizer

    ftp_server = FTPServer((IP_ADDRESS,21), handler)
    ftp_server.serve_forever()


def setup():
    global SERVER, PORT, IP_ADDRESS
    print("Server started...")

    SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER.bind((IP_ADDRESS, PORT))

    SERVER.listen()

    acceptConnections()


setup_thread = Thread(target=setup)
setup_thread.start()

ftp_thread = Thread(target=ftp)
ftp_thread.start()
