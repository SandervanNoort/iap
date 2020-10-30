import os
import datetime
import time
import shutil
import io
import dropbox

from .utc_to_local import utc_to_local

# pylint: disable=E1103


def get_last_mtime(local_dir):
    """ last_mtime
      None: change timestamps of files
      0: Never synced before
      12341234: timestamp of last sync"""

    timestamp_fname = os.path.join(local_dir, "timestamp.txt")
    print("timestamp_fname", timestamp_fname)
    mtime_now = int(time.mktime(datetime.datetime.now().timetuple()))

    try:
        os.utime(local_dir, None)
        print("Success in setting utime to None")
        os.utime(local_dir, (mtime_now, mtime_now))
        print("Success in setting utime to now")
        last_mtime = None
    except OSError:
        print("Could not set utime")
        try:
            with open(timestamp_fname, "r") as fobj:
                last_mtime = int(fobj.read())
                print("Previous sync at",
                      datetime.datetime.fromtimestamp(last_mtime))
        except (IOError, ValueError):
            print("No previous sync date found")
            last_mtime = 0
        with open(timestamp_fname, "w") as fobj:
            fobj.write("{0}".format(mtime_now))

    print("last_mtime set to", last_mtime)
    return last_mtime


def dropbox_download(
        client, dropbox_dir, local_dir, delete=True, print_func=print):
    """Download from dropbox"""

    local_dir = os.path.normpath(local_dir)
    dropbox_dir = os.path.normpath(dropbox_dir)
    try:
        listing = client.files_list_folder(dropbox_dir, recursive=True)
    except dropbox.exceptions.ApiError:
        print("Empty dropbox folder", dropbox_dir)
        return
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    last_mtime = get_last_mtime(local_dir)
    has_more = True
    renames = {}
    local_names = [os.path.join(local_dir, "timestamp.txt")]
    while has_more:
        for entry in sorted(
                listing.entries, key=lambda entry: entry.path_lower):
            dirname = os.path.dirname(entry.path_lower)
            if not renames:
                local_name = local_dir
                renames[entry.path_lower] = local_dir
            else:
                local_name = os.path.join(renames[dirname], entry.name)
            local_names.append(local_name)
            if isinstance(entry, dropbox.files.FolderMetadata):
                renames[entry.path_lower] = local_name
            download(entry, local_name, last_mtime, client, print_func)
        if listing.has_more:
            listing = client.files_list_folder_continue(listing.cursor)
        else:
            has_more = False
    if delete:
        clear_local_dir(local_dir, local_names)
    print_func("Done syncing.")


def download(entry, local_name, last_mtime, client, print_func=print):
    """Download file, saved as local_name"""
    if isinstance(entry, dropbox.files.FolderMetadata):
        if not os.path.exists(local_name):
            print_func("Creating folder", local_name)
            os.makedirs(local_name)
    else:
        dbx_mtime = time.mktime(utc_to_local(
            entry.client_modified).timetuple())
        if os.path.exists(local_name):
            mtime = os.path.getmtime(local_name)
            size = os.path.getsize(local_name)
            if size == entry.size:
                if last_mtime is None and mtime == dbx_mtime:
                    print("Same timestamp", local_name)
                    return
                elif last_mtime > 0 and dbx_mtime <= last_mtime:
                    print("Synced after last file change", local_name)
                    return
                print("Same size but different timestamp", local_name)
                print("synced", last_mtime, "dropbox", dbx_mtime,
                      "local", mtime)
                print(entry.client_modified)
            else:
                print("Different size", local_name)
        try:
            result = client.files_download(entry.path_lower)[1]
        except dropbox.exceptions.HttpError as err:
            print("Error downloading", local_name, err)
            return
        print_func("Downloaded", local_name)
        with io.open(local_name, "wb") as fobj:
            fobj.write(result.content)
        try:
            os.utime(local_name, (dbx_mtime, dbx_mtime))
        except OSError:
            print("Cannot change time on Android")


# import unicodedata
# def to_path_lower(fname):
#     """Create the path_lower as used by dropbox"""
#     return unicodedata.normalize("NFC", to_unicode(fname))


def clear_local_dir(local_dir, local_names):
    """Remove all files from local_dir which are not in local_names"""
    for dirpath, dirnames, fnames in os.walk(local_dir):
        # subfolder = os.path.relpath(dirpath, local_dir)
        for fname in fnames:
            fullname = os.path.join(dirpath, fname)
            if fullname not in local_names and not fname.endswith("pyc"):
                print("Removing file", fullname)
                os.remove(fullname)
        for dirname in dirnames:
            fullname = os.path.join(dirpath, dirname)
            if fullname not in local_names:
                print("Removing folder", fullname)
                shutil.rmtree(fullname)
