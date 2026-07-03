import os
import string
import platform


SCRAP_MECHANIC_APP_ID = 387990

def get_available_drives():
    return ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]

def quick_scan_user_mods():
    available_drives = get_available_drives()

    for drive in available_drives:
        users_path = os.path.join(drive, 'Users')

        if os.path.exists(users_path):
            for user in os.listdir(users_path):
                scrap_mechanic_path = os.path.join(users_path, user, "AppData", "Roaming", "Axolot Games", "Scrap Mechanic", "User")

                if os.path.exists(scrap_mechanic_path):
                    for steam_user in os.listdir(scrap_mechanic_path):
                        mod_path = os.path.join(scrap_mechanic_path, steam_user, "Mods", "ScrapComputers External Editor")

                        if os.path.exists(mod_path):
                            return mod_path

    return None




def windows_find_workshop_mod():
    import vdf
    import winreg

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Valve\Steam"
    )
    value, _ = winreg.QueryValueEx(key, "SteamPath")
    steam_path = value.replace("/", "\\")

    lib_file = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")

    with open(lib_file, "r", encoding="utf-8") as f:
        data = vdf.load(f)

    path: str | None = None

    for key, val in data["libraryfolders"].items():
        if key.isdigit():
            if str(SCRAP_MECHANIC_APP_ID) in val["apps"]:
                path = val["path"]
                break

    if path is None:
        raise FileNotFoundError("Could not find a Scrap Mechanic install via Steam")

    sm_mods_path = os.path.join(path, "steamapps", "workshop", "content", str(SCRAP_MECHANIC_APP_ID))

    for mod_id in os.listdir(sm_mods_path):
        x = os.path.join(sm_mods_path, mod_id, "description.json")

        if not os.path.exists(x):
            continue

        with open(x, "r", encoding='utf-8') as f:
            if "ScrapComputers External Editor" in f.read():
                return os.path.join(sm_mods_path, mod_id)

    return None



def find_where_tf_my_mod_is():
    os_type = platform.system()

    if os_type == "Windows":
        possible_path = quick_scan_user_mods()

        if possible_path:
            return possible_path

        path2 = windows_find_workshop_mod()

        if path2:
            return path2

        else:
            raise FileNotFoundError("Could not find 'ScrapComputers External Editor' installed in user mods or Steam workshop downloads")


    else:
        print("I aint added MacOS, Sorry linux users, add it yourself.")
        return input("Where is the Scrap Computers Mod (PATH):")




