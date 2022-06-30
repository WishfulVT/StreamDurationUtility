# Python 3.10
# Given a stream URL, returns the current stream time

# Imports necessary for livestream details
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime
import time
# Imports necessary for the GUI
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
import threading


# Methods necessary for livestream details

def mod_url(URL):
    # If someone enters an actual URL, get just the identifier
    if "youtu.be" in str(URL):
        return str(URL.split("youtu.be/")[1][:11])
    elif "youtube.com/watch?v=" in str(URL):
        return str(URL.split("youtube.com/watch?v=")[1][:11])
    return URL

def livestream_details_request(URL):
    try:
        request = youtube.videos().list(
            part='liveStreamingDetails',
            id=URL
        )

        response = request.execute()
        return response
    except HttpError:
        return None

# Given an API response, process it in terms of start and/or end times
def fetch_livestream_times(URL):
    stream_details = livestream_details_request(URL)
    #print(stream_details)

    # Code -1: if your request wasn't processed, assume a bad API key
    if stream_details == None:
        return -1, {"bad_api": True}, None

    # Code -1: if you submitted a malformed URL, no items will be available
    if len(stream_details['items']) == 0:
        return -1, {}, None

    # Code -2: if the stream has ended, return start and end times
    stream_items = stream_details['items'][0]["liveStreamingDetails"]
    if "actualEndTime" in stream_items.keys():
        return -2, stream_items["actualEndTime"], stream_items["actualStartTime"]

    # Code -3: if stream has yet to start, return scheduled start time
    if "actualStartTime" not in stream_items.keys():
        return -3, stream_items["scheduledStartTime"], None

    # Code 0: stream is live, return the actual start time
    return 0, stream_items["actualStartTime"], None

# For live or upcoming streams, process start and end times into a sensible
# string to display to the window
def get_delta_label(time_start, time_end, text_line1, text_line2):
    # We subtract two datetimes to get a timedelta, chop off the fractions
    # (decimals) of a second at the end, and remove the trailing "0:" if
    # 0 hours remain. Then just put the labels together.
    delta = time_end - time_start
    delta = str(delta).split(".")[0] if delta.total_seconds() > 0 else "00:00"
    delta = delta[2:] if delta[:2] == "0:" else delta
    return f'{text_line1}{text_line2}{delta}'

# Converts a time string to a UTC datetime object
# Calling datetime.datetime.now(datetime.timezone.utc) gives us one time in UTC
# YouTube times are already in UTC but we have to make sure datetime knows this
def as_datetime(string):
    s2 = string + "+0000"
    return datetime.datetime.strptime(s2, "%Y-%m-%dT%H:%M:%SZ%z")

# The bulk of the livestream code. Given a string URL, which can be an 11-digit
# identifier or a whole youtube.com or youtu.be URL, construct an appropriate
# string to display to the window
# This code CAN be repurposed for other programs!
def get_livestream_runtime(URL, live_check = False):
    STARTING_SOON = 15
    LIVE = 60
    LIVE_REFRESH = 1
    PREMIERE_REFRESH = 1

    if len(URL) < 1: # don't bother pinging the API if the string is ""
        return "Enter URL", {}
    
    ret, stream_time, acStart = fetch_livestream_times(URL)
    
    if ret == -1:
        if "bad_api" in stream_time.keys():
            return "HTTP request failed\nCheck your API key", {}
        else:
            return "Stream ID unknown", {}

    start = as_datetime(stream_time)
    if ret == -3:
        now = datetime.datetime.now(datetime.timezone.utc)
        ret_str = get_delta_label(now, start,
                                  "Stream has not yet started",
                                  "\nExpected wait: ")
        
        return ret_str, {"fetch": STARTING_SOON, "refresh_type": "premiere",
                         "refresh": PREMIERE_REFRESH, "start": start}
        # Basically, if the stream hasn't started yet, use get_delta_label()
        # to figure out when it *does* start, and return that string

    if ret == 0:
        updated = '*' if live_check else ''
        now = datetime.datetime.now(datetime.timezone.utc)
        ret_str = get_delta_label(start, now,
                                  f'Stream is live{updated}',
                                  "\nDuration: ")
        
        return ret_str, {"fetch": LIVE, "refresh_type": "live",
                         "refresh": LIVE_REFRESH, "start": start}
        # If the stream is currently live, figure out for how long it has
        # been live, and return that string as formatted by get_delta_label()
        # To show if the constructed time was a "live" time (pinged the API),
        # we add an asterisk to "Stream is live"

    if ret == -2:
        ret_str = "Stream has concluded"
        sEnd = as_datetime(stream_time)
        sStart = as_datetime(acStart)
        ret_str += f'\nDuration: {str(sEnd - sStart)}'
        # If a stream is over, simply use actual start and end to determine
        # the runtime, and return the string with no extra timer values
        
        return ret_str, {}


# Methods necessary for the GUI

# Refresh() is a scary class, since it handles refreshing the label every
# second (only for upcoming or live streams)
class Refresh(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self.event = threading.Event()
        # we create an event so we can interrupt our timer

    def run(self):
        global root_alive, lbl, url
        check = True

        if root_alive:
            # if we don't CONSTANTLY ask if root is alive, then we'll
            # occasionally run some of this tkinter label code when the
            # root window has been destroyed. So get used to it.
            refresh = 0
            last_time = None
            
            label_str = ""
            waits = {}
            # hold onto the label and wait times as pulled by the API

            while not self.event.is_set():
                # if we haven't been interrupted yet,
                if check and root_alive:
                    if last_time == None:
                        # and we're not holding onto our start time, then
                        # ping the API for our label
                        label_str, waits = get_livestream_runtime(mod_url(url), True)
                        
                    elif "refresh_type" in waits.keys():
                        # Alternatively, if we only ping our API every couple
                        # of seconds, we still want to update the second count
                        # every second. So we hold onto the last time pulled by
                        # the API, and we just do math every second
                        now = datetime.datetime.now(datetime.timezone.utc)
                        if waits["refresh_type"] == "live":
                            updated = "*" if refresh == 0 else ""
                            label_str = get_delta_label(last_time, now,
                                                f'Stream is live{updated}',
                                                "\nDuration: ")
                        elif waits["refresh_type"] == "premiere":
                            label_str = get_delta_label(now, last_time,
                                                "Stream has not yet started",
                                                "\nExpected wait: ")
                            # and of course we have different labels for live or
                            # upcoming streams, which I misleadingly refer to as
                            # 'premieres'
                        else:
                            label_str = "Something went wrong"

                    if root_alive:
                        # Now that we've determined what the label should say,
                        # update it (so long as root exists)
                        lbl.configure(text=label_str)

                    if "fetch" and "refresh" in waits.keys():
                        # If we are upcoming or live, we want to wait one
                        # second for 15 or 60 seconds respectively
                        if refresh == 0:
                            last_time = waits["start"]
                        
                        if refresh >= 0 and refresh < int(waits["fetch"]):
                            refresh += int(waits["refresh"])
                            self.event.wait(int(waits["refresh"]))
                        else:
                            # Every 15/60 seconds, kill the time we stored so
                            # we have to ping the API again
                            refresh = 0
                            last_time = None
                        
                    # If we're not bothering to refresh at all, set check to False
                    else:
                        check = False

            # The only time we hit this code down here is when (1) root still
            # exists and (2) the popup enter-URL window is open
            lbl.configure(text="Awaiting URL")
            check = True
    # after the popup window is closed, run() ends. So we then recreate this
    # thread with the new URL information, as seen in close_frame() below

# A popup window (or the main window) has been closed
def close_frame(frame, kill_root = False):
    global thread

    if kill_root: # If somebody closes the main window, kill the child
        global root_alive
        root_alive = False
        for child in frame.winfo_children():
            child.destroy()

    # Then kill the frame and *restart* the thread, since it has ended
    # (Unless you're killing the program)
    frame.destroy()
    if not kill_root:    
        thread = Refresh()
        thread.start()

def sendoff_url(textfield, frame):
    # Our url string is stored in a global. Store it, then kill the frame
    global url
    url = str(textfield.get())
    close_frame(frame)

def construct_open_url(base):
    # Open a popup window only if no popup window already exists
    # https://stackoverflow.com/questions/69751236/how-get-name-of-
    # toplevel-window-of-another-toplevel
    num_toplevels = 0
    for child in base.winfo_children():
        num_toplevels += 1 if child.winfo_class() == "Toplevel" else 0

    if num_toplevels == 0:
        global thread
        thread.event.set()
        
        # Create a new popup window
        popup = Toplevel()
        popup.title("SDU: enter URL")
        popup.iconbitmap("img/folder.ico") # https://findicons.com/icon/68711/opened
        popup.minsize(100, 10)
        pfrm = ttk.Frame(popup, padding=8)
        pfrm.grid()

        # Create a textfield to enter text, and a "Go" button
        urlfield = Entry(pfrm, width=30)
        urlfield.focus_force() # focus on the new window
        urlfield.grid(row=0, column=0)
        ttk.Button(pfrm, text="Go", width=6,
                   command=lambda: sendoff_url(urlfield, popup)
                   ).grid(row=0, column=1)


        # Hitting the Esc key or the X button closes the window and does NOT
        # save the entered text. The SDU will fall back on the last entered
        # URL, even if it is blank.
        # Hitting "Go" or the Enter key, meanwhile, will use the newly entered
        # text information as the URL.
        urlfield.bind("<Escape>", lambda event: close_frame(popup))
        urlfield.bind("<Return>", lambda event: sendoff_url(urlfield, popup))
        popup.protocol("WM_DELETE_WINDOW", lambda: close_frame(popup))
        popup.mainloop()

# This is main.
def construct_window():
    global root_alive, url, thread, lbl
    root_alive = True
    url = ""

    # Construct a tkinter window and add it to the visual grid
    root = Tk()
    root.title("SDU")
    root.iconbitmap("img/timer.ico") # https://findicons.com/icon/567889/timer
    root.minsize(200, 60)
    frm = ttk.Frame(root, padding=10)
    frm.grid()

    # Create a button to open an "enter-URL" popup
    icon = Image.open("img/open_folder.png").resize((32, 32), Image.Resampling.LANCZOS)
    iconimg = ImageTk.PhotoImage(icon) # https://www.flaticon.com/free-icon/open-folder-outline_25402

    thread = Refresh()
    ttk.Button(frm, image=iconimg, command=lambda: construct_open_url(root)
               ).grid(row=0, column=0)

    # Create a label to display the stream details
    labelString = "Enter URL"
    lbl = ttk.Label(frm, text=labelString)
    lbl.grid(row=0, column=1)

    # Set exit conditions, start the stream label refresher, and open
    # the main window
    root.bind("<Escape>", lambda event: close_frame(root, True))
    root.protocol("WM_DELETE_WINDOW", lambda: close_frame(root, True))
    thread.start()
    root.mainloop()


if __name__ == "__main__": # Call our main method
    API_KEY = "your_api_key_here"

    try:
        youtube = build('youtube', 'v3', developerKey = API_KEY)
        construct_window()
    except:
        root = Tk()
        root.title("SDU")
        root.iconbitmap("img/timer.ico") # https://findicons.com/icon/567889/timer
        root.minsize(200, 60)
        frm = ttk.Frame(root, padding=10)
        frm.grid()
        ttk.Label(frm, text="No API key given").grid(row=0, column=0)
        root.mainloop()
