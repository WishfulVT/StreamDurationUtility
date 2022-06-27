# Stream Duration Utility

The Stream Duration Utility, or **SDU**, is a GUI-based program that displays the current duration of a YouTube livestream.
Twitch livestreams already display their current live durations, but this feature may still be added at a future date.

---

## Installation
Clone the repository to a local directory.
```
git clone https://github.com/WishfulVT/OfflineTagger
```
Next, install the required Python modules from the requirements.txt file:
```
pip install -r requirements.txt
```
Finally, open sdu.pyw in an editor and **add your own YouTube API key** into the `api_key` string found at the start of the main method at the bottom of the file.
Failure to replace the API key will prevent requests from succeeding.
Create your own google API key: https://console.cloud.google.com/apis/dashboard

## Launch instructions
Double-clicking on sdu.pyw will now launch the program without opening a command-line. Creating a shortcut to this file should have the same effect.

If you prefer to call this from an existing command-line, use the following command from within your local directory:
```
pythonw sdu.pyw
```
Using "python" instead of "pythonw" will freeze the command-line even after the program finishes execution.

---

## Using the program

#### Entering a YouTube URL
Successfully running the SDU will open the main SDU window. From here, click on the open-folder icon to open a second window where you can enter a YouTube URL. 
Strictly speaking, you should enter the 11-digit identifier in the URL rather than the whole "youtube.com/watch?v=", but the program will strip this out for you. The same functionality is true for youtu.be links.
Once you've pasted in an id or URL, hit Go, or hit the Enter key. This will close the popup window and update the main window accordingly.
If you press the X or Escape key instead, the window will close, and the main window will resume displaying information for the last entered URL, which may be the empty string (in which case no useful information is displayed).

#### Entering a different URL
See above. Really. There's not too much extra functionality to describe.
