import Editor
from backend import wheretfissm

path = wheretfissm.find_where_tf_my_mod_is()

from envs.generator import create_definition_file
create_definition_file("definitions/ScrapComputersV3.lua", "envs/lua_sc.json")



# todo List
# - Topbar
#  > Manual File Saving
#  > Run the code? (Like, start the computer, if that is even possible)
#
# - Debug Console
#  > Make it copy-able
#  > Auto-display errors [Done]
#
# - Project Viewer
#  > Create / Delete Files / Folders  [Kinda Done]
#
# - Code Viewer
#  > Selecting Code [Kinda Done]
#  > Copy/Paste
#  > Context Analyser (Scan other Lua files for syntax stuff) [Kinda Done]


if __name__ == "__main__":
    app = Editor.App(path)
    app.run()