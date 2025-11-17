# Chris Valdivia

import tkinter as tk
from tkinter import messagebox
import sqlite3 #For database access
import bcrypt #For password hashing and salting
import os #For file access
import sys #For sys things
import subprocess #To switch programs
import cv2 #Used to check if the rtsp stream is valid

# Load database for users
conn = sqlite3.connect("AIPIA.db")
cursor = conn.cursor()



def on_closing():
    conn.commit();
    conn.close();
    root.destroy()


def login():
    usernameEntered = username_entry.get()
    passwordEntered = password_entry.get()


    #Do a database query to compare usernames and passwords
    cursor.execute("SELECT ID, Username, Password FROM users WHERE Username = ?", (usernameEntered,));
    rows = cursor.fetchall() #Store results
    #print(rows)

    #Check to see if the results are empty (Which means user does not exist)
    if not rows:
        messagebox.showerror("Login Failed", "Invalid camera name or password.")

    else:

        #Loop through all results from rows
        for id, username, password in rows:
	    #If the username entered matches from the database and the password matches the hash, show success window
            #if bcrypt.checkpw(str.encode(passwordEntered), str.encode(password)):

            if not passwordEntered:
                passwordEntered = " "

            if bcrypt.checkpw(passwordEntered.encode('utf-8'), password):
                #Now to check if the rtsp stream is alive and working
            	
            	#Do a database query to compare usernames and passwords
                cursor.execute("SELECT RTSPStream from users_settings WHERE ID = ?", (id,));
                rows = cursor.fetchall() #Store results
            	
            	#Set the url for capture
                cap = cv2.VideoCapture(rows[0][0])
                #Set a timeout interval (Give it x miliseconds to open)
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)

                #tk.Tk.after(root, 10000)
                #Check if the stream failed to opened
                if not cap.isOpened():
                    #Print out an error message
                    messagebox.showerror("RTSP Stream Unreachable", "RTSP stream failed to respond. Make sure your RTSP stream is running.")
                    break
            
            
            
                messagebox.showinfo("Login Success", f"Welcome, now opening {username}")
                #print("ID: "+str(id))
                #subprocess.Popen(['python', 'Main5-3.py', str(id)])
                #subprocess.call("python Main5-2.py " + str(id))

                subprocess.Popen(['python', 'homepage.py', str(id)])
                sys.exit(0) #Close program

            else:
                messagebox.showerror("Login Failed", "Invalid camera name or password.")

def open_register_window():
    def register_user():
        #Get the new camera name, password, and rtsp url
        new_username = reg_username_entry.get()
        new_password = reg_password_entry.get()
        new_rtspurl = reg_rtspurl_entry.get()

        #Check the database to see if this camera already exists
        cursor.execute("SELECT ID, Username, Password FROM users WHERE Username = ?", (new_username,));
        rows = cursor.fetchall()

        #If so, say so. Also if the user fails to enter all of the required information, do so.
        if rows:
            messagebox.showerror("Error", "Camera name already exists.")
        elif not new_username or not new_rtspurl:
            messagebox.showerror("Error", "Camera name and URL are required.")
        else:
            #If we entered a unique camera name and there is a password and URL, we need to check
            #if the url entered is valid. We can use OpenCV to open the stream to check if it is valid

            if not new_password:
                new_password =" "

            #Set the url for capture
            cap = cv2.VideoCapture(new_rtspurl)
            #print(cap)
            #Set a timeout interval (Give it x miliseconds to open)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)

            #tk.Tk.after(root, 10000)
            #Check if the stream failed to opened
            if not cap.isOpened():
                #Print out an error message
                messagebox.showerror("RTSP URL Invalid or Unreachable", "RTSP stream failed to respond. Make sure your RTSP stream is running and the URL entered is correct.")
            else:
                #If it opened, we now want to close the opencv capture, then enter the data into the database

                #close opencv2 capture
                cap.release()

                #Now we need to check which next ID number is available (in order) in the db
                cursor.execute("SELECT ID FROM users order by ID asc");
                rows = cursor.fetchall()

                #Variable to store the ID to use
                currentID = 0;
                #print(rows)
                #Iterate through all of the ids until we find a gap. If there is no gap, use the last number
                for i, ids in enumerate(rows):
                    i = i + 1
                    if i != ids[0]:
                        currentID = i;
                        break
                if currentID == 0:
                    currentID = len(rows)+1

                #print("Next ID: "+ str(currentID))

                #Now that we have the ID, we need to hash and salt the password before saving it

                #First, we encode the password into an array of bites
                passwordByteArray = new_password.encode('utf-8')
                #Now we generate the salt
                salt = bcrypt.gensalt()
                #Finally we can hash and salt the password
                hashedPassword = bcrypt.hashpw(passwordByteArray, salt)

                #First to save the camera name and password
                cursor.execute("INSERT INTO users (ID, username, password) VALUES (?, ?, ?)", (currentID, new_username, hashedPassword))


                #Now to save the RTSP Stream
                cursor.execute("INSERT INTO users_settings (ID, RTSPStream) VALUES (?, ?)", (currentID, new_rtspurl))
                #Commit the changes
                conn.commit()
                #Show a message saying we have successfully added the camera
                messagebox.showinfo("Registration Success", f"Successfully added {new_username}")
                register_window.destroy()

            

            #user_database[new_username] = new_password
            #messagebox.showinfo("Success", "Camera registered successfully!")
            #register_window.destroy()

    register_window = tk.Toplevel(root)
    register_window.title("Register")
    register_window.geometry("300x250")

    tk.Label(register_window, text="Register New Camera", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(register_window, text="Camera Name:").pack()
    reg_username_entry = tk.Entry(register_window)
    reg_username_entry.pack()

    tk.Label(register_window, text="Password:").pack()
    reg_password_entry = tk.Entry(register_window, show="*")
    reg_password_entry.pack()

    tk.Label(register_window, text="RTSP URL with Account:").pack()
    reg_rtspurl_entry = tk.Entry(register_window)
    reg_rtspurl_entry.pack()



    tk.Button(register_window, text="Register", command=register_user).pack(pady=15)

# Main window
root = tk.Tk()
root.title("Login Page")
root.geometry("300x250+860+440")

# Title
tk.Label(root, text="AI-PIA Login", font=("Arial", 16, "bold")).pack(pady=10)

# Username
tk.Label(root, text="Camera Name:").pack()
username_entry = tk.Entry(root)
username_entry.pack()

# Password
tk.Label(root, text="Password:").pack()
password_entry = tk.Entry(root, show="*")
password_entry.pack()

# RTSPUrl
#tk.Label(root, text="RTSP URL:").pack()
#rtspurl_entry = tk.Entry(root, show="*")
#rtspurl_entry.pack()


# Buttons
tk.Button(root, text="View Camera", command=login).pack(pady=10)
tk.Button(root, text="Register New Camera", command=open_register_window).pack()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
