import socket
from threading import Thread
from tkinter import *
from tkinter import ttk

import select
import ftplib
import os
import ntpath
from ftplib import FTP
from pathlib import Path
from tkinter import filedialog


IP_ADDRESS = "127.0.0.1"
PORT = 8000
SERVER = None

bufferSize = 4096
nameEntry = None
listBox = None
chatBox = None
labelChat = None
textMessage = None
playerName = None
fileEntry = None
sendingFile = None
downloadingFile = None
fileToDownload = None
filePath = None
chatwindow = None


def recieveMsg():
    global nameEntry, listBox, chatBox, labelChat, textMessage, SERVER, bufferSize, fileEntry, chatwindow, downloadingFile, fileToDownload
    while True:
        chunk = SERVER.recv(bufferSize)
        print("msg from server: ", chunk.decode("utf-8"))
        try:
            if "tiul" in chunk.decode() and "1.0," not in chunk.decode():
                letter_list = chunk.decode().split(",")
                listBox.insert(
                    letter_list[0],
                    letter_list[0]
                    + ":"
                    + letter_list[1]
                    + ":"
                    + letter_list[3]
                    + " "
                    + letter_list[5],
                )
                print(
                    letter_list[0],
                    letter_list[1],
                    letter_list[2],
                    letter_list[3],
                    letter_list[4],
                    letter_list[5],
                )
                print("l:: ", letter_list)
            elif chunk.decode() == "access granted":
                chatwindow.configure(text="")
                chatBox.insert(END, "\n" + chunk.decode("ascii"))
                chatBox.see(END)

            elif chunk.decode() == " denied access":
                chatwindow.configure(text="")
                chatBox.insert(END, "\n" + chunk.decode("ascii"))
                chatBox.see(END)
            elif "download ?" in chunk.decode():
                downloadingFile = chunk.decode("ascii").split(" ").strip()
                bufferSize = int(chunk.decode("ascii").split()[8])
                chatBox.insert(END, "\n" + chunk.decode("ascii"))
                chatBox.see(END)
            elif "Download:" in chunk.decode():
                getFileName = chunk.decode().split()
                fileToDownload = getFileName[1]

            else:
                chatBox.insert(END, "\n" + chunk.decode("utf-8"))
                chatBox.see("end")
                # print(chunk.decode("utf-8"))
        except:
            pass


def sendMsg():
    global nameEntry
    global SERVER
    global fileEntry
    global chatBox, fileToDownload

    msgToSend = fileEntry.get()
    SERVER.send(msgToSend.encode("utf-8"))
    chatBox.insert(END, "\n" + "You>" + msgToSend)
    chatBox.see("end")
    fileEntry.delete(0, "end")

    if (msgToSend == "y" or msgToSend == "Y"):
        print("\nplease wait, file is downloading...")
        chatBox.insert(END, "\n" + "\nplease wait, file is downloading...")
        chatBox.see("end")
        HOSTNAME = "127.0.0.1"
        USERNAME = "student"
        PASSWORD = "student"
        home = str(Path.home())
        download_path = home+"/Downloads"
        ftp_server = ftplib.FTP(HOSTNAME, USERNAME, PASSWORD)
        ftp_server.encoding = "utf-8"
        ftp_server.cwd("shared_files")
        fname=fileToDownload

        local_filename =os.path.join(download_path, fname)
        file = open(local_filename, "wb")
        ftp_server.retrbinary('RETR'+fname, file.write)
        ftp_server.dir()
        file.close()
        ftp_server.quit()
        print("file successfully downloaded to path: " + download_path)
        chatBox.insert(END, "\n" + "file successfully downloaded to path: " + download_path)
        chatBox.see("end")
    
    if (msgToSend == "n" or msgToSend == "N"):
        print("\nFile cannot be downloaded because the permission to download was denied")
        chatBox.insert(END, "\n" + "\nFile cannot be downloaded because the permission to download was denied")
        chatBox.see("end")
        ftp_server.quit()



def connectWithClient():
    global nameEntry, listBox, chatBox, labelChat, textMessage, SERVER, bufferSize, fileEntry

    text = listBox.get(ANCHOR)
    print("text: ", text)
    list_item = text.split(":")
    msg = "connect " + list_item[1]
    SERVER.send(msg.encode("ascii"))


def disConnectWithClient():
    global nameEntry, listBox, chatBox, labelChat, textMessage, SERVER, bufferSize, fileEntry

    text = listBox.get(ANCHOR)
    print("text: ", text)
    list_item = text.split(":")
    msg = "disconnect " + list_item[1]
    SERVER.send(msg.encode("ascii"))


def quitServer():
    global SERVER
    SERVER.close()


def getFileSize(file_name):
    with open(file_name, "rb") as file:
        chunk = file.read()
        print("Total size of file: ", len(chunk))
        return len(chunk)


def browseFile():
    global sendingFile, chatBox, filePath, SERVER

    try:
        fileName = filedialog.askopenfilename()
        filePath.configure(text=fileName)

        HOSTNAME = "127.0.0.1"
        USERNAME = "student"
        PASSWORD = "student"

        ftp_server = ftplib.FTP(HOSTNAME, USERNAME, PASSWORD)
        ftp_server.encoding = "utf-8"
        ftp_server.cwd("shared_files")
        fname = ntpath.basename(fileName)
        with open(fileName, "rb") as file:
            ftp_server.storbinary(f"STORE {fname}", file)

        ftp_server.dir()
        ftp_server.quit()

        message = "send: " + fname
        print("while browsing: ", message)
        if message[:4] == "send":
            print("Please wait.....")
            chatBox.insert(END, "\n", " \nPlease wait...\n")
            chatBox.see(END)
            sendingFile = message[5:]
            fileSize = getFileSize("shared files/" + sendingFile)
            final_msg = message + " " + str(fileSize)
            SERVER.send(final_msg.encode("utf-8"))
            chatBox.insert(END, "In process...")

    except FileNotFoundError:
        print("cancel button was prssed")


def showClientList():
    global listBox, SERVER
    listBox.delete(0, "end")
    SERVER.send("show list".encode("ascii"))
    print("show_list sent to serever")


def connectToServer():
    global SERVER, nameEntry
    clientName = nameEntry.get()
    SERVER.send(clientName.encode("utf-8"))
    print("{} is Connected to sever".format(clientName))


def openChatWindow():
    global nameEntry, listBox, chatBox, labelChat, textMessage, fileEntry
    window = Tk()
    window.title("Messenger")
    window.geometry("550x400")

    namelabel = Label(window, text="Enter your name", font=("Helvetica", 12))
    namelabel.place(x=10, y=10)

    nameEntry = Entry(window, width=20, font=("Helvetica", 12))
    nameEntry.place(x=140, y=10)
    nameEntry.focus()

    connect = Button(
        window,
        text="Connect to server",
        font=("Helvetica", 10),
        command=connectToServer,
    )
    connect.place(x=350, y=10)

    line = ttk.Separator(window, orient="horizontal")
    line.place(x=0, y=40, relwidth=1, height=0.25)

    activeuser = Label(window, text="Active Users", font=("Helvetica", 12))
    activeuser.place(x=10, y=50)

    listBox = Listbox(
        window, height=6, width=58, activestyle="dotbox", font=("Helvetica", 12)
    )
    listBox.place(x=10, y=70)

    sc1 = Scrollbar(listBox)
    sc1.place(relheight=1, relwidth=0.02, relx=0.98)
    sc1.config(command=listBox.yview)

    connectuser = Button(
        window,
        text="Connect to user",
        font=("Helvetica", 10),
        command=connectWithClient,
    )
    connectuser.place(x=230, y=190)

    disconnect = Button(
        window,
        text="Disconnect from User",
        font=("Helvetica", 10),
        command=disConnectWithClient,
    )
    disconnect.place(x=340, y=190)

    refresh = Button(
        window, text="Refresh", font=("Helvetica", 10), command=showClientList
    )
    refresh.place(x=480, y=190)

    chatwindow = Label(window, text="Chat Window", font=("Helvetica", 12))
    chatwindow.place(x=10, y=210)

    chatBox = Text(window, height=6, width=58, font=("Helvetica", 12))
    chatBox.place(x=10, y=230)

    sc2 = Scrollbar(chatBox)
    sc2.place(relheight=1, relwidth=0.02, relx=0.98)
    sc2.config(command=chatBox.yview)

    attach = Button(
        window, text="Attach File and Send", font=("Helvetica", 10), command=browseFile
    )
    attach.place(x=10, y=350)

    fileEntry = Entry(window, width=25, font=("Calibri", 12))
    fileEntry.pack()
    fileEntry.place(x=160, y=352)

    send = Button(window, text="Send", font=("Helvetica", 10), command=sendMsg)
    send.place(x=380, y=350)

    filePath = Label(window, text="", fg="blue", bg="yellow", font=("Helvetica", 12))
    filePath.place(x=10, y=380)

    window.mainloop()


def setup():
    global SERVER, PORT, IP_ADDRESS

    SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER.connect((IP_ADDRESS, PORT))

    receive_thread = Thread(target=recieveMsg)
    receive_thread.start()

    openChatWindow()


setup()
