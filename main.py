import sqlite3
import os
import hashlib
from functools import partial
from send2trash import send2trash
from wx import App, FD_SAVE, DD_DEFAULT_STYLE, DD_DIR_MUST_EXIST, ID_OK, DirDialog


def get_path():
    app = App(None)
    style = FD_SAVE
    dialog = DirDialog(None, "Save to...", "", DD_DEFAULT_STYLE | DD_DIR_MUST_EXIST)
    if dialog.ShowModal() == ID_OK:
        path = dialog.GetPath()
    else:
        path = ""
        print("No directory selected, saving to current directory.")
    dialog.Destroy()
    return path


def md5sum(filename):
    with open(filename, mode='rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()


def insert_value(i_filepath, i_filehash):
    c.execute("INSERT INTO files VALUES ('%s', '%s')" % (i_filepath, i_filehash))


f = open("files.db", "w+")
f.close()

conn = sqlite3.connect('files.db')

c = conn.cursor()
# Create table
c.execute('''CREATE TABLE IF NOT EXISTS files
            (name text, hash text)''')

directory_in_str = get_path()

directory = os.fsencode(directory_in_str)
hash_dict = {}
reference_dict = {}

filepathlist = []
filehashlist = []

for file in os.listdir(directory):
    name = os.fsdecode(file)
    filepath = directory_in_str + "/" + name
    filehash = (md5sum(filepath))

    filepathlist.append(filepath)
    filehashlist.append(filehash)

    reference_dict[filepath] = filehash

    if filehash not in hash_dict:
        hash_dict[filehash] = 1
    else:
        hash_dict[filehash] += 1

for path, hash in zip(filepathlist, filehashlist):
    insert_value(path, hash)

filehashlist = set(i for i in filehashlist if filehashlist.count(i) > 1)

for i in filehashlist:
    t = (i,)
    c.execute("SELECT * FROM files WHERE hash=?", t)
    duplicates = c.fetchall()

    for n in range(len(duplicates) - 1):
        send2trash(duplicates[n][0])

    print("Deleted %s duplicates..." % (len(duplicates)))
    for n in range(len(duplicates) - 2):
        print(duplicates[n][0])

c.execute("DROP TABLE files")

# Save (commit) the changes
conn.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()
os.remove("files.db")

