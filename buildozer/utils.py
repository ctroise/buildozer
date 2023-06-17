# "2023-06-11"
#
import os
import logging

# Working with multiple kivy screens:
# https://noudedata.com/2023/04/kivy-screen-navigation/

# -------------------------------------------------------------------------------------------------------------------
# COLORS
# the fonts can also access system fonts?
# a collection of 3 or 4 float values between 0-1 (kivy default)
# https://www.w3.org/TR/SVG11/types.html#ColorKeywords

FONT_DIR = "Pycharm/buildozer/venv/Lib/site-packages/kivy/data/fonts"

MY_RED = [1, 0, 0, 1]
MY_WHITE = [1, 1, 1, 1]

NORMAL_COLOR = "white"                 # ? [0.8784313725490196, 1.0, 1.0, 1.0]
NO_FOCUS_COLOR = "blanchedalmond"      #
HIGHLIGHT_COLOR = "lightpink"          # [1.0, 0.7137254901960784, 0.7568627450980392, 1.0]
REMAINING_OPTIONS_COLOR = "lightcyan"  # "lightgoldenrodyellow"
MY_SOLUTION_HIGHLIGHT_COLOR = "lightskyblue"
MY_SOLUTION_COLOR = "lightsteelblue"

def static_vars(**kwargs):  # do not delete me
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

@static_vars(ct_dict={})
def myjoe(what="", stop:bool=True):
    if what != "":
        if what in myjoe.ct_dict:
            return
        else:
            myjoe.ct_dict[what] = 1
    if stop:
        _joe = 12  #  this line Needs a breakpoint


def did_I_come_here_from(function_p):
    if isinstance(function_p, str):
        function_p = [function_p]
    import inspect
    a_INSPECT_STACK = inspect.stack()
    for ct, values in enumerate(a_INSPECT_STACK):
        frame, filename, linenum, function, line_of_code, index = values
        for fn in function_p:
            if function.lower() == fn.lower():
                return True
    return False

def flatten_list(alist):
    # only works for one level deep
    res = [item for xx in alist for item in xx]
    return res

def scrub_text(value):
    MARGIN = 50
    if not value:  #  value == []:
        return "", ""
    #
    assert value  # if it passed the above test then it should be fine
    if isinstance(value, int):
        return 1, str(value)
    #
    ll = len(value)
    if isinstance(value, list):
        tmp = ""
        text = ""
        for ct in range(len(value)):
            if tmp:
                tmp += ", "
            tmp += ", ".join(map(str, value[ct:ct + 1]))
            if len(tmp) >= MARGIN:
                text += f"{tmp}\n"
                tmp = ""
        text += tmp
    elif isinstance(value, str):
        text = value
    #
    if text[-1] == "\n":
        text = text[:-1]
    if text[-1] == ",":
        text = text[:-1]  # does this ever get hit?  2023-05-27
    #
    return ll, text

def get_sql_today(withDay=False):
    import datetime
    currentdt = datetime.datetime.now()
    today = currentdt.strftime("%Y-%m-%d")
    hour = int(currentdt.strftime("%H"))
    return today, hour


TODAY, HOUR = get_sql_today()

def backup_to_one_drive():
    from shutil import copy
    to_dir = "/mnt/c/Users/ctroi/OneDrive/Pycharm"
    for file in ["main.py", "util.py", "saved_puzzle.txt"]:
        from_file = f"./{file}"
        to_file = f"{to_dir}/{file}"
        copy(from_file, to_file)
    return

def delete_undo_files():
    DIR = "UndoFiles"
    for root, dirs, files in os.walk(DIR):
        for ct, filename in enumerate(files):
            file = f"{root}/{filename}"
            try:
                os.remove(file)
            except FileNotFoundError:
                pass
    return

def create_loggers():
    with open("Logs/this_session_only.txt", "w") as fp:
        pass  # just blanks it out
    #today = get_sql_today()
    fmtlong = logging.Formatter(f"{TODAY} %(asctime)s.%(msecs)03d  %(levelname)s  %(message)s", datefmt="%H:%M:%S")
    fmtkivy = logging.Formatter(f"{TODAY}  %(asctime)s.%(msecs)06d  [%(levelname)s]  %(message)s", datefmt="%H:%M:%S")
    # ---------------------------
    # Snag what IB/TWS is logging
    # ---------------------------
    KIVY_logger = logging.getLogger()  # <--- the 'root' logger
    KIVY_logger.propagate = False
    KIVY_logger.setLevel(logging.INFO)
    KIVY_handler = logging.FileHandler(f"Logs/kivy_log_{TODAY}.txt")
    KIVY_handler.setFormatter(fmtkivy)
    KIVY_logger.addHandler(KIVY_handler)
    # THIS SESSION ONLY
    thisonlylogger = logging.getLogger()
    thisonlylogger.setLevel(logging.DEBUG)
    thisonlyhandler = logging.FileHandler("Logs/this_session_only.txt")
    thisonlyhandler.setFormatter(fmtlong)
    thisonlylogger.addHandler(thisonlyhandler)
    # # MAIN
    # mainlogger = logging.getLogger("myapp")
    # mainlogger.setLevel(logging.DEBUG)
    # mainhandler = logging.FileHandler("Logs/my_log.txt")
    # mainlogger.propagate = False
    # mainhandler.setFormatter(fmtlong)
    # mainlogger.addHandler(mainhandler)
    #
    return #mainlogger, thisonlylogger

def file_exists(file):
    """ File exists, and is not empty """
    # file_dir = os.path.split(file)[0]
    # if file_dir:
    #     if not os.path.isdir(file_dir):
    #         myjoe()  # now what?  make_all_needed_directories()
    res = os.path.isfile(file) and bool(os.path.getsize(file))
    return res

def get_calling_function(levels_back=1, ignoreInit=False, withdetails=False, debug=True):
    import inspect, os
    IGNORE_STACK = []
    a_INSPECT_STACK = inspect.stack()
    a_STACK = []
    for ct, values in enumerate(a_INSPECT_STACK):
        if ct in [0, 1]:
            continue
        v3 = values[3]
        if v3 in IGNORE_STACK:
            continue
        frame, _filename, linenum, fn, line_of_code, index = values
        filename = os.path.basename(_filename)
        a_STACK.append((fn, filename, linenum, line_of_code, index, frame))
    if a_STACK[1][0] == "__init__" and a_STACK[2][0] == "<module>":
        name = a_STACK[2][5].f_locals["__name__"]
        fn = f"{name}.py (while being imported)"
        assert fn != "snapped_already"
        return fn

    went_back_ct = 1
    a_RET_VAL, filename, linenum, function = "", "", "", ""
    for ct, a_FrameInfo in enumerate(a_STACK):
        function, filename, linenum, line_of_code, index, frame = a_FrameInfo
        if function == "__init__" and ignoreInit:
            continue
        if function in ["__setitem__", "__getitem__"]:
            continue
        # if function in ["__enter__"]:  # , "__exit__"]:
        #     myjoe("context managers")  # "__exit__" got hit 2022-09-23, and worked
        fn = ""
        if function[:2] == "__" and function[-2:] == "__":
            x_locals = frame.f_locals
            fn = x_locals['self']
            if not a_RET_VAL:
                a_RET_VAL = f"{fn}.{function}()"
            else:
                a_RET_VAL = f"{fn} - {function}()"
            if went_back_ct == levels_back:
                break
            else:
                went_back_ct += 1
                continue
        if fn:
            function = f"{function}() - {fn}()"
        if went_back_ct == levels_back:
            break
        else:
            went_back_ct += 1
            continue
    if not a_RET_VAL:
        a_RET_VAL = function

    # if withdetails:
    #     return a_RET_VAL, filename, linenum
    # else:
    return a_RET_VAL


# -------------------------------------------------------------------------------------------------------------------
# ----- WRAPPERS ----------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------
def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

# DO_NOT_MEGA_POPULATE_OPTIONS, SAVE_AN_UNDO_FILE

def wrap_mega_populate1(func):
    def wrapper(*arg, **kwargs):
        curvalue = MEG
        t1 = time.time()
        #
        res = func(*arg, **kwargs)                      # <--------------------------------------------
        #
        t2 = time.time()
        time_in_secs = t2 - t1
        msg = f"timeit(): {func.__name__}(): Time taken: {time_in_secs:,.4f} seconds"
        print(f"{msg}")
        newlogger.debug(msg)
        return res
    return wrapper


# -------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------



ALL_POTENTIAL_SOLUTIONS = {
  10: {2: [[1,2,3,4]]},

  11: {1: [[1,2,3,5]]},

  12: {2: [[1,2,3,6], [1,2,4,5]]},

  13: {1: [[1,2,3,7], [1,3,4,5]],
       3: [[1,2,4,6]]},

  14: {2: [[1,2,3,8], [1,2,4,7], [1,2,5,6], [1,3,4,6], [2,3,4,5]]},

  15: {1: [[1,2,3,9], [1,2,5,7], [1,3,4,7], [1,3,5,6]],
       3: [[1,2,4,8], [2,3,4,6]]},

  16: {0: [[1,3,5,7]],
       2: [[1,2,4,9], [1,2,5,8], [1,2,6,7], [1,3,4,8], [1,4,5,6], [2,3,4,7], [2,3,5,6]]},

  17: {1: [[1,2,5,9], [1,3,4,9], [1,3,5,8], [1,3,6,7], [1,4,5,7], [2,3,5,7]],
       3: [[1,2,6,8], [2,3,4,8], [2,4,5,6]]},

  18: {0: [[1,3,5,9]],
       2: [[1,2,6,9], [1,2,7,8], [1,3,6,8], [1,4,5,8], [1,4,6,7], [2,3,4,9], [2,3,5,8], [2,3,6,7], [2,4,5,7], [3,4,5,6]]},

  19: {1: [[1,2,7,9], [1,3,6,9], [1,3,7,8], [1,4,5,9], [1,5,6,7], [2,3,5,9], [3,4,5,7]],
       3: [[1,4,6,8], [2,3,6,8], [2,4,5,8], [2,4,6,7]]},

  20: {0: [[1,3,7,9]],
       2: [[1,2,8,9], [1,4,6,9], [1,4,7,8], [1,5,6,8], [2,3,6,9], [2,3,7,8], [2,4,5,9], [2,5,6,7], [3,4,5,8], [3,4,6,7]],
       4: [[2,4,6,8]]},

  21: {1: [[1,3,8,9], [1,4,7,9], [1,5,6,9], [1,5,7,8], [2,3,7,9], [3,4,5,9], [3,5,6,7]],
       3: [[2,4,6,9], [2,4,7,8], [2,5,6,8], [3,4,6,8]]},

  22: {0: [[1,5,7,9]],
       2: [[1,4,8,9], [1,6,7,8], [2,3,8,9], [2,4,7,9], [2,5,6,9], [2,5,7,8], [3,4,6,9], [3,4,7,8], [3,5,6,8], [4,5,6,7]]},

  23: {1: [[1,5,8,9], [1,6,7,9], [2,5,7,9], [3,4,7,9], [3,5,6,9], [3,5,7,8]],
       3: [[2,4,8,9], [2,6,7,8], [4,5,6,8]]},

  24: {0: [[3,5,7,9]],
       2: [[1,6,8,9], [2,5,8,9], [2,6,7,9], [3,4,8,9], [3,6,7,8], [4,5,6,9], [4,5,7,8]]},

  25: {1: [[1,7,8,9], [3,5,8,9], [3,6,7,9], [4,5,7,9]],
       3: [[2,6,8,9], [4,6,7,8]]},

  26: {2: [[2,7,8,9], [3,6,8,9], [4,5,8,9], [4,6,7,9], [5,6,7,8]]},

  27: {1: [[3,7,8,9], [5,6,7,9]],
       3: [[4,6,8,9]]},

  28: {2: [[4,7,8,9], [5,6,8,9]]},

  29: {1: [[5,7,8,9]]},

  30: {2: [[6,7,8,9]]}
}

