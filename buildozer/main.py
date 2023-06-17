# "2023-06-11"

# Python GUI's With Kivy:
# https://www.youtube.com/playlist?list=PLCC34OHNcOtpz7PJQ7Tv7hqFBP_xDDjqg
# How To Set The Height And Width of Widgets - Python Kivy GUI Tutorial #4:
# https://www.youtube.com/watch?v=AxKksRhcmOA

from copy import deepcopy
import sys
import re
#
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from utils import *

TODAY, HOUR = get_sql_today()
#INIT_IS_DONE = False
DO_NOT_MEGA_POPULATE_OPTIONS = False
DO_NOT_CHECK_SOLUTION = False
RIP_IT_GOOD_CT = 0

# -------------------------------------------------------------------------------------------------------------------
def wrap_mega_populate(func):
    def wrapper(*arg, **kwargs):
        global DO_NOT_MEGA_POPULATE_OPTIONS
        cur_mega_status = DO_NOT_MEGA_POPULATE_OPTIONS
        DO_NOT_MEGA_POPULATE_OPTIONS = True
        #
        res = func(*arg, **kwargs)                      # <--------------------------------------------
        #
        DO_NOT_MEGA_POPULATE_OPTIONS = cur_mega_status
        return res
    return wrapper

def wrap_do_not_check_SET_SOLUTION(func):
    def wrapper(*arg, **kwargs):
        global DO_NOT_CHECK_SOLUTION
        cur_mega_status = DO_NOT_CHECK_SOLUTION
        DO_NOT_CHECK_SOLUTION = True
        #
        res = func(*arg, **kwargs)                      # <--------------------------------------------
        #
        DO_NOT_CHECK_SOLUTION = cur_mega_status
        return res
    return wrapper
# -------------------------------------------------------------------------------------------------------------------


# ----- class INIT_IS_DONE - START ----------------------------------------------------------------------------------
class INIT_IS_DONE:
    _INIT_IS_DONE = False
    _MEGA_DO_NOT_TURN_IT_ON = True

    @classmethod
    def __bool__(cls):
        return cls._INIT_IS_DONE


    @classmethod
    def __init__(cls, MYAPP):  # Note: I only want one instance of this
        cls.MYAPP = MYAPP
        cls.NO_NEW_VARIABLES = True

    def __setattr__(self, key, value):
        if "NO_NEW_VARIABLES" not in self.__dict__ or self.NO_NEW_VARIABLES is False:
            self.__dict__[key] = value
        else:
            if key in self.__dict__:
                self.__dict__[key] = value
                return True
            else:
                msg = f"cls_UNDO_FILES.__setattr__() : Attempting to set new variable '{key}' - not allowed!"
                print(msg)
                raise UserWarning
        return

    # @classmethod
    # def Set_MEGA_DO_NOT_TURN_IT_ON(cls, do_not_turn_it_on:bool):
    #     cls._MEGA_DO_NOT_TURN_IT_ON = do_not_turn_it_on

    @classmethod
    def Set_MEGA_DO_NOT_TURN_IT_ON_on(cls):
        cls._MEGA_DO_NOT_TURN_IT_ON = True

    @classmethod
    def Set_MEGA_DO_NOT_TURN_IT_ON_off(cls):
        cls._MEGA_DO_NOT_TURN_IT_ON = False


    @classmethod
    def Turn_INIT_IS_DONE_on(cls):
        if not cls._MEGA_DO_NOT_TURN_IT_ON:
            cls._INIT_IS_DONE = True
        else:
            _joe = 12  # wrong!

    @classmethod
    def Turn_INIT_IS_DONE_off(cls):
        cls._INIT_IS_DONE = False

# ----- class INIT_IS_DONE - END   ----------------------------------------------------------------------------------


# ----- class UNDO_FILES - START ------------------------------------------------------------------------------------
class cls_UNDO_FILES:
    GO_BACK_TO = None  # this can be accessed from the outside of the class
    MYAPP = None
    _SAVE_AN_UNDO_FILE = False
    _LAST_UNDO_FILE_NUM = 0
    _GREATEST_UNDO_FILE_NUM = 0
    _LAST_SUM = 0
    _LAST_BUTTONS = None  # [['', '', '', ''], ['', '', '', ''], ['', '', '', ''], ['', '', '', '']]
    _ROW_SUMS_int = [0, 0, 0, 0]
    _COL_SUMS_int = [0, 0, 0, 0]
    _MY_SOLUTION_int = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    _THE_ACTUAL_SOLUTION_int = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

    @classmethod
    def turn_undo_saving_off(cls):
        cls._SAVE_AN_UNDO_FILE = False

    @classmethod
    def turn_undo_saving_on(cls):
        cls._SAVE_AN_UNDO_FILE = True


    @classmethod
    def __setattr__(cls, key, value):
        if "NO_NEW_VARIABLES" not in cls.__dict__ or cls.NO_NEW_VARIABLES is False:
            cls.__dict__[key] = value
        else:
            if key in cls.__dict__:
                cls.__dict__[key] = value
                return True
            else:
                msg = f"cls_UNDO_FILES.__setattr__() : Attempting to set new variable '{key}' - not allowed!"
                print(msg)
                raise UserWarning
        return

    @classmethod  # Note: I only want one instance of this
    def __init__(cls, MYAPP):
        cls.MYAPP = MYAPP
        cls.reset_variables()
        #
        cls.NO_NEW_VARIABLES = True
        return

    @classmethod
    def reset_variables(cls):
        cls._ROW_SUMS_int = cls.MYAPP.ROW_SUMS_int
        cls._COL_SUMS_int = cls.MYAPP.COL_SUMS_int
        cls._MY_SOLUTION_int = cls.MYAPP.MY_SOLUTION_int
        cls._THE_ACTUAL_SOLUTION_int = cls.MYAPP.THE_ACTUAL_SOLUTION_int
        cls._LAST_BUTTONS = cls.copy_buttons(cls.MYAPP.Buttons_ODD_EVEN)
        return


    @classmethod
    def CLEAR(cls):
        cls.reset_variables()
        # # fixme: just use 'reset_variables'?
        # cls._ROW_SUMS_int = [0, 0, 0, 0]
        # cls._COL_SUMS_int = [0, 0, 0, 0]
        return


    @classmethod
    def UNDO(cls, instance):  # cls_UNDO_FILES
        cls._LAST_UNDO_FILE_NUM = max(0, cls._LAST_UNDO_FILE_NUM - 1)
        #previous_file = f"UndoFiles/{TODAY}_{cls._LAST_UNDO_FILE_NUM}.txt"
        previous_file = f"UndoFiles/{cls._LAST_UNDO_FILE_NUM}.txt"
        if not file_exists(previous_file):
            cls.CLEAR()
            cls.MYAPP.reset_remaining_options_colors()
            instance.text = f"UNDO"
            cls.MYAPP.button_forward.text = f"Forward ({cls._GREATEST_UNDO_FILE_NUM})"
            return
        #
        cls.MYAPP.Undo_engine(instance, previous_file)

        cls.reset_variables()
        #
        if cls.GO_BACK_TO is None:
            cls.MYAPP.button_undo.text = f"UNDO c ({cls._LAST_UNDO_FILE_NUM})"
        else:
            cls.MYAPP.button_undo.text = f"UNDO c ({cls._LAST_UNDO_FILE_NUM}/{cls.GO_BACK_TO})"
        forwards_left = cls._GREATEST_UNDO_FILE_NUM - cls._LAST_UNDO_FILE_NUM
        cls.MYAPP.button_forward.text = f"Forward ({forwards_left})"
        #
        cls.MYAPP.RipItGood()
        return


    @classmethod
    def is_something_new(cls):
        """ This is what is saved in the file, so this is what I check for differences:
            self.ROW_SUMS_int[xx],       self.COL_SUMS_int[xx]            self.MY_SOLUTION_int[row][col]
            self.THE_ACTUAL_SOLUTION_int[0][0]  self.Buttons_ODD_EVEN[row][col]
        """
        _joe = cls._SAVE_AN_UNDO_FILE
        res = did_I_come_here_from("RipItGood")
        if not res:
            fn = get_calling_function()
            if fn not in ["Save_Undo_Level"]:
                myjoe(fn)  # 2023-06-05
        if cls._SAVE_AN_UNDO_FILE is False:
            return False
        #
        mysum = 0
        if cls.MYAPP.ROW_SUMS_int != cls._ROW_SUMS_int:
            myjoe()  # 2023-06-05
        if cls.MYAPP.COL_SUMS_int != cls._COL_SUMS_int:
            myjoe()  # 2023-06-05
        for ct, arr in enumerate([cls.MYAPP.ROW_SUMS_int, cls.MYAPP.COL_SUMS_int]):
            for num in arr:
                mysum += num
        #
        if cls._MY_SOLUTION_int != cls.MYAPP.MY_SOLUTION_int:
            myjoe()  # 2023-06-05
        if cls._THE_ACTUAL_SOLUTION_int != cls.MYAPP.THE_ACTUAL_SOLUTION_int:
            myjoe()  # 2023-06-05
        for ct, darr in enumerate([cls.MYAPP.MY_SOLUTION_int, cls.MYAPP.THE_ACTUAL_SOLUTION_int]):
            arr = flatten_list(darr)
            for num in arr:
                mysum += num
        #
        for row in range(4):
            for col in range(4):
                if cls._LAST_BUTTONS[row][col]:
                    if cls._LAST_BUTTONS[row][col] != cls.MYAPP.Buttons_ODD_EVEN[row][col].MYTEXT:
                        mysum += 1
                        cls._LAST_BUTTONS[row][col] = cls.MYAPP.Buttons_ODD_EVEN[row][col].MYTEXT
        #
        res = mysum - cls._LAST_SUM
        cls._LAST_SUM = mysum
        #
        cls.reset_variables()
        # cls._ROW_SUMS_int = cls.MYAPP.ROW_SUMS_int
        # cls._COL_SUMS_int = cls.MYAPP.COL_SUMS_int
        # cls._MY_SOLUTION_int = cls.MYAPP.MY_SOLUTION_int
        # cls._THE_ACTUAL_SOLUTION_int = cls.MYAPP.THE_ACTUAL_SOLUTION_int
        # cls._LAST_BUTTONS = cls.copy_buttons(cls.MYAPP.Buttons_ODD_EVEN)
        return res


    @classmethod
    def copy_buttons(cls, other_buttons):
        tmp = [['', '', '', ''], ['', '', '', ''], ['', '', '', ''], ['', '', '', '']]
        for row in range(4):
            for col in range(4):
                if other_buttons[row][col]:  # inits to None
                    tmp[row][col] = other_buttons[row][col].MYTEXT
        return tmp


    @classmethod
    def set_go_back_to_level(cls):
        # only set it if it hasn't been set before
        if cls.GO_BACK_TO is None:
            cls.GO_BACK_TO = cls._GREATEST_UNDO_FILE_NUM - 1
            cls.update_Undo_Button_Text()
        return

    @classmethod
    def __missing__(cls, key):
        _joe = 12  #

    @classmethod
    def Save_Undo_Level(cls):
        if not INIT_IS_DONE:
            return
        if not cls.is_something_new():
            return
        DIR = "UndoFiles"
        cls_UNDO_FILES._LAST_UNDO_FILE_NUM += 1
        cls_UNDO_FILES._GREATEST_UNDO_FILE_NUM = max(cls._GREATEST_UNDO_FILE_NUM, cls._LAST_UNDO_FILE_NUM)
        #
        #filename = f"{DIR}/{TODAY}_{cls._LAST_UNDO_FILE_NUM}.txt"
        filename = f"{DIR}/undo_file_{cls._LAST_UNDO_FILE_NUM}.txt"
        cls.MYAPP.SavePuzzle(filename=filename)
        #
        cls.update_Undo_Button_Text()
        return


    @classmethod
    def update_Undo_Button_Text(cls):
        if cls.GO_BACK_TO is None:
            cls.MYAPP.button_undo.text = f"UNDO a ({cls._LAST_UNDO_FILE_NUM})"
        else:
            cls.MYAPP.button_undo.text = f"UNDO a ({cls._LAST_UNDO_FILE_NUM}/{cls.GO_BACK_TO})"
        #
        return
# ----- class UNDO_FILES - END   ------------------------------------------------------------------------------------

#SAVE_AN_UNDO_FILE = False


def SET_FOCUS(dinge, FLAG:bool=True):
    if isinstance(dinge, myLabel_and_Text):
        dinge = dinge.MYTEXTBOX
    dinge.focus = FLAG
    return


# -------------------------------------------------------------------------------------------------------------------
class EXIT_RIP_IT(Exception):
    def __init__(self):
        pass
# -------------------------------------------------------------------------------------------------------------------
class WHO_HAS_THE_FOCUS(Exception):
    def __init__(self, who, widget):
        self.WHO = who
        self.widget = widget

def who_has_the_focus(self, layout):
    try:
        _who_has_the_focus(layout)
    except WHO_HAS_THE_FOCUS as err:
        return err.widget
    return

def _who_has_the_focus(layout):
    for dinge in layout.children:
        if isinstance(dinge, (Label)):
            continue
        if isinstance(dinge, (GridLayout, BoxLayout)):
            _who_has_the_focus(dinge)
        else:
            if dinge.focus is True:
                if hasattr(dinge, "name"):
                    whoami = dinge.name
                elif hasattr(dinge, "ANAME"):
                    whoami = dinge.ANAME
                else:
                    _joe = 12  # ??
                raise WHO_HAS_THE_FOCUS(whoami, dinge)
    return


def SET_RED(widget):  # solo
    if isinstance(widget, RemainingOptions):
        row = widget.AROW
        col = widget.ACOL
        _joe = 12  #
    if isinstance(widget, myLabel_and_Text):
        if widget.NAME == "Number in all":
            myjoe()  # 2023-06-10   what am I doing here?
    if isinstance(widget, mySolution):
        # Todo: Call this directly from mySolution.SET_RED()
        myjoe()  # 2023-06-10
    SET_COLOR(widget, MY_RED)
    return

def SET_COLOR(widget, color, force=False):  # standalone function
    # https://www.w3.org/TR/SVG11/types.html#ColorKeywords
    """ NORMAL_COLOR    = "white"
        NO_FOCUS_COLOR  = "blanchedalmond"
        HIGHLIGHT_COLOR = "lightpink"    [1.0, 0.7137254901960784, 0.7568627450980392, 1.0]
        MY_RED          = [1, 0, 0, 1]
        MY_WHITE        = [1, 1, 1, 1]
    """
    if isinstance(widget, mySolution):
        myjoe()  # 2023-06-05   use other color functions
    if isinstance(widget, RemainingOptions):
        if force:
            widget.background_color = color
        else:
            current_color = widget.background_color
            if current_color in [MY_RED, [1, 0, 0, 1], "red"]:
                if current_color != color:
                    row = widget.AROW
                    col = widget.ACOL
                    if widget.MYAPP.MY_SOLUTION_int[row][col] != 0:
                        # As this cell has been solved, revert the color
                        pass
                    else:
                        # Do not remove the red color as it's probably for another col/row
                        return
    if isinstance(widget, myLabel_and_Text):
        widget.MYTEXTBOX.background_color = color
    else:
        widget.background_color = color
    return


# ----- class myTextInput - START ----------------------------------------------------------------------------
class myTextInput(TextInput):
    TOTAL_NUMBER_OF_TABS = -1
    TAB_ORDER = {}
    TAB_NEXT = None
    TABSTOP = None
    PATTERN = re.compile('[^0-9]')  # To only allow floats (0 - 9 and a single period)

    def __str__(self):
        if not self.ANUM is None:
            if self.ANAME == "rowsum":
                res = f"myTextInput(rowsum) for row #{self.ANUM}"
            elif self.ANAME == "colsum":
                res = f"myTextInput(colsum) for row #{self.ANUM}"
        elif self.AROW or self.ACOL:
            res = f"myTextInput('{self.ANAME}') -> ({self.AROW}, {self.ACOL})"
        else:
            res = f"myTextInput: Single cell: '{self.ANAME}'"
        return res

    def __init__(self, *args, **kwargs):
        self.MYAPP = args[0]  # self.MYTEXTBOX = myTextInput(self, f"{name}", readonly=self.READONLY)
        self.ANAME = args[1]  # super().__init__(*args, **kwargs)
        #
        self.AROW = kwargs.get("row", None)
        self.ACOL = kwargs.get("col", None)
        self.ANUM = kwargs.get("num", None)
        self.MYCOLOR = kwargs.get("mycolor", None)
        tabstop = False
        readonly = kwargs.get("readonly", False)
        if readonly:
            if kwargs.get("tabstop", False):
                raise UserWarning  # How can I set this to readonly AND a tabstop?
        else:
            tabstop = kwargs.get("tabstop", True)
        assert not (readonly and tabstop)
        self.TABSTOP = tabstop
        #
        kwargs["halign"] = "center"

        for arg in ["row", "col", "num", "mycolor", "tabstop", "readonly", "size"]:
            kwargs.pop(arg, None)
        super().__init__(**kwargs)          # <--------------------------------------------------------------
        #
        # Set the color for this widget:
        if hasattr(self, "SET_COLOR"):
            self.SET_COLOR("normal")
        else:
            if not self.MYCOLOR:
                SET_COLOR(self, NO_FOCUS_COLOR)
            else:
                SET_COLOR(self, self.MYCOLOR)

        # Set the 'tab-ability' for this widget:
        self.MY_TAB_NUMBER = None
        if readonly is False:
            # This is a 'tabstop', something that can be tabbed into:
            num = myTextInput.TOTAL_NUMBER_OF_TABS
            myTextInput.TOTAL_NUMBER_OF_TABS = num + 1
            self.MY_TAB_NUMBER = myTextInput.TOTAL_NUMBER_OF_TABS
            myTextInput.TAB_ORDER[self.MY_TAB_NUMBER] = self
        #
        return

    # -------------------------------------------------------------------------------------------------------------------
    def keyboard_on_key_down(self, window, keycode, text, modifiers):  # myTextInput
        #global INIT_IS_DONE  # I need this
        # 1)
        TextInput.keyboard_on_key_down(self, window, keycode, text, modifiers)
        if keycode[1] == "tab" and self.TABSTOP:
            if not "shift" in modifiers:  # a regular tab forward
                next_tab = (self.MY_TAB_NUMBER + 1) % (myTextInput.TOTAL_NUMBER_OF_TABS + 1)
                if next_tab == 0:
                    # Don't go back to the 1st ("sum") but go to the first RowSum
                    next_tab = 3
            else:   # a back-tab
                next_tab = (self.MY_TAB_NUMBER - 1) % (myTextInput.TOTAL_NUMBER_OF_TABS + 1)
                if next_tab == 2:
                    # Don't go back to the 1st ("sum") but go to the first RowSum
                    next_tab = myTextInput.TOTAL_NUMBER_OF_TABS
            self.TAB_NEXT = next_tab
            next_widget = self.TAB_ORDER[self.TAB_NEXT]
            self.MYAPP.INIT_IS_DONE_HANDLER.Turn_INIT_IS_DONE_on()     # If I'm tabbing, then this is ok
            SET_FOCUS(self, False)  # "SumRow for row #0" --> RowCol().on_focus()
            SET_FOCUS(next_widget)  # "SumCol for col #0" --> nowhere?
        return

    def keyboard_on_textinput(self, window, text):  # myTextInput
        # 2) This gets hit with every key hit in the/a box
        TextInput.keyboard_on_textinput(self, window, text)
        return

    def insert_text(self, substring, from_undo=False):  # myTextInput(TextInput):
        # 3) After 'keyboard_on_textinput()'
        if substring is None:
            return
        if '.' in self.text:
            s = re.sub(self.PATTERN, '', substring)
        else:
            # To allow a period as well:  s = '.'.join(...same as below)
            s = ''.join(re.sub(self.PATTERN, '', s) for s in substring.split('.', 1))
        if isinstance(self, mySolution):
            # Check this # is an option for this cell
            if self.MYAPP.INIT_IS_DONE_HANDLER and int(s) in self.MYAPP.CELL_OPTIONS_int[self.AROW][self.ACOL]:
                res = super().insert_text(s, from_undo=from_undo)
            else:
                _joe = 12  # int(s) is not an option for this cell!
        else:
            res = super().insert_text(s, from_undo=from_undo)
        return #res

    # def keyboard_on_key_up(self, window, keycode):  # myTextInput
    #     global INIT_IS_DONE  # need this
    #     # 4) Note: After key_up, for tab-shifting, 'on_focus' gets triggered
    #     if not keycode[1] in ["tab"]:
    #         return
    #     if keycode[1] == "tab":
    #         if not self.TABSTOP:
    #             return
    #         next_widget = self.TAB_ORDER[self.TAB_NEXT]
    #     INIT_IS_DONE = True  # If I'm tabbing, then this is ok
    #     #next_widget.focus = True  # works
    #     SET_FOCUS(next_widget)
    #     return
    # -------------------------------------------------------------------------------------------------------------------

    def SET_TEXT(self, value=""):  # myTextInput
        ll, text = scrub_text(value)
        self.text = text
        assert not isinstance(self, mySolution)
        return
# ----- class myTextInput - END   ----------------------------------------------------------------------------


# ----- class Explanation - START -----------------------------------------------------------------------------------
class cls_Explanation(TextInput):
    MY_DATA = {}
    def __init__(self, MYAPP):
        super().__init__(readonly=True, multiline=True)
        self.MYAPP = MYAPP
        SET_COLOR(self, "brown")


    def CLEAR(self):
        self.MY_DATA = {}
        self.SET_TEXT()
        return

    def SET_TEXT(self):
        self.text = ""
        if not self.MY_DATA:
            return
        tmp = ""
        reasons = []
        allkeys = list(self.MY_DATA.keys())
        allkeys.sort()
        for arr in allkeys:
            row, col = arr
            num = self.MY_DATA[arr]
            reason = f"Cell ({row},{col}) takes {num}"
            reasons.append(reason)
        tmp = ""
        for reason in reasons:
            tmp += f"{reason}\t"
        tmp = tmp[:-1]  # get rid of final '\t'
        self.text = tmp
        return

    def SET_ERROR(self, msg):
        self.MY_DATA = {}
        self.MYAPP.UNDO_HANDLER.set_go_back_to_level()
        self.text = msg
        SET_RED(self)
        return

    def ADD_EXPLANATION(self, row, col, num):
        # only thing that calls this is:                            def refresh_remaining_options(
        the_true_solution = self.MYAPP.THE_ACTUAL_SOLUTION_int[row][col]
        if the_true_solution not in [0, num]:
            msg = f"WARNING! Putting {num} into ({row}, {col}) doesn't work, as the real solution is {the_true_solution}!"
            self.MYAPP.UNDO_HANDLER.set_go_back_to_level()
        if (row, col) in self.MY_DATA:
            curnum = self.MY_DATA[(row, col)]
            if curnum == num:
                # I already know about this one, nothing to do
                return
            else:
                if all([xx != 0 for xx in self.MYAPP.ROW_SUMS_int + self.MYAPP.COL_SUMS_int]):
                    # Do not report on this until all the sums have been filled in
                    _msg = f"You want to put #{num} in for cell ({row}, {col}), but I previously deduced #{curnum} HAS TO go there?!"
                    _joe = 12  # I have something else stored as needing to go into this cell!
                    return
        self.MY_DATA[(row, col)] = num
        return
# ----- class Explanation - END   -----------------------------------------------------------------------------------

# ----- class RemainingOptions - START ------------------------------------------------------------------------------
class RemainingOptions(myTextInput):
    def __str__(self):
        res = f"RemainingOptions ({self.AROW}, {self.ACOL})"
        return res

    def __init__(self, *args, **kwargs):
        kwargs["tabstop"] = False
        super().__init__(*args, **kwargs)

    def keyboard_on_textinput(self, window, text):  # RemainingOptions
        TextInput.keyboard_on_textinput(self, window, text)
        return


    def on_focus(self, instance, value, *largs):                     # RemainingOptions
        if value is False:
            return
        row = instance.AROW
        col = instance.ACOL
        arr = self.MYAPP.CELL_OPTIONS_int[row][col]
        if len(arr) == 1:
            # There is only one option left for this cell, so place it as a solution:
            num = arr[0]
            res = self.MYAPP.SET_SOLUTION(row, col, num)             # RemainingOptions
            if res:
                instance.SET_TEXT()
                SET_COLOR(instance, REMAINING_OPTIONS_COLOR)
                self.MYAPP.UNDO_HANDLER.Save_Undo_Level()
        else:
            if (row, col) in self.MYAPP.EXPLANATION.MY_DATA:
                # I have something here I can place though
                num = self.MYAPP.EXPLANATION.MY_DATA[(row, col)]
                res = self.MYAPP.SET_SOLUTION(row, col, num)         # RemainingOptions
                if res:
                    instance.SET_TEXT()
                    SET_COLOR(instance, REMAINING_OPTIONS_COLOR)
        SET_FOCUS(instance)
        return
# ----- class RemainingOptions - END   ------------------------------------------------------------------------------


# ----- class myLabel_and_Text - START ------------------------------------------------------------------------------------
class myLabel_and_Text:  # (TextInput):  # myLabel_and_Text
    """ top_grid = GridLayout()
        top_grid.cols = 2
        top_grid.add_widget(Label(text="Hi there", size_hint_y = None, height=40, size_hint_x = None, width=200))
        top_grid.add_widget(TextInput(text="", size_hint_y=None, height=40, size_hint_x=None, width=200))
        self.add_widget(top_grid)
    """
    NAME = "myLabel_and_Text"

    def __init__(self, app, GUI, name, readonly, **kwargs):
        self.MYAPP = app
        self.MYGUI = GUI
        self.NAME = name
        self.READONLY = readonly
        textbindfn = kwargs.pop("textbindfn", None)
        font_size = kwargs.pop("font_size", None)  # default is 15

        this_layout = BoxLayout()
        # 1) The label:
        self.MYLABEL = Label(text=name)
        this_layout.add_widget(self.MYLABEL)
        # 2) The textbox next to it:
        if font_size:
            self.MYTEXTBOX = myTextInput(self, f"{name}", readonly=self.READONLY, font_size=font_size)
        else:
            self.MYTEXTBOX = myTextInput(self, f"{name}", readonly=self.READONLY)
        if callable(textbindfn):
            assert not self.READONLY
            self.MYTEXTBOX.bind(text=textbindfn)      # myLabel_and_Text
            self.MYTEXTBOX.bind(focus=self.on_focus)  # myLabel_and_Text
        #
        this_layout.add_widget(self.MYTEXTBOX)
        #
        GUI.add_widget(this_layout)
        return

    def __str__(self):
        res = f"myLabel_and_Text ({self.NAME})"
        return res


    def SET_TEXT(self, value=""):  # myLabel_and_Text
        # 1) Change the box text:
        ll, text = scrub_text(value)
        self.MYTEXTBOX.text = text   # <---------------------------------------
        if not text:
            self.MYLABEL.text = self.NAME
            return
        # -------------------------------------------------------------------------------------------------------------------
        # 2) Change some of the labels:
        if self.NAME == "Number in all":
            xx = len(value.split())
            if xx == 1:
                self.MYLABEL.text = f"Number in all "   # ({xx})"
            else:
                self.MYLABEL.text = f"Numbers in all"  # ({xx})"
        #
        elif self.NAME == "Remaining Solutions":
            self.MYLABEL.text = f"Remaining Solutions ({ll})"
        #
        elif self.NAME == "Eliminated Solutions":
            # I always want this to give the # of elims
            self.MYLABEL.text = f"Eliminated Solutions ({ll})"
        return


    def on_focus(self, instance, value, *largs):  # myLabel_and_Text
        if value is False:
            return
        if self.READONLY:
            return
        self.MYAPP.reset_top_boxes(colors_only=True)
        self.MYAPP.reset_sum_colors()
        SET_COLOR(instance, HIGHLIGHT_COLOR)
        #   row = instance.ANUM
        self.MYAPP.hightlight_Remaining_Options()
        return

    def keyboard_on_key_up(self, window, keycode):  # myLabel_and_Text
        # Note: After key_up, for tab-shifting, 'on_focus' gets triggered
        if not keycode[1] in ["tab"]:
            return
        if keycode[1] == "tab":
            if not self.MYTEXTBOX.TABSTOP:
                return
            #self.MYTEXTBOX.TAB_ORDER[self.MYTEXTBOX.TAB_NEXT].focus = True
            SET_FOCUS(self.MYTEXTBOX.TAB_ORDER[self.MYTEXTBOX.TAB_NEXT])
        return

    def keyboard_on_key_down(self, window, keycode, text, modifiers):  # myTextInput
        TextInput.keyboard_on_key_down(self, window, keycode, text, modifiers)
        if not keycode[1] in [".", "tab"]:
            return
        if keycode[1] == ".":
            self.SET_TEXT()
        elif keycode[1] == "tab":
            if not self.MYTEXTBOX.TABSTOP:
                return
            # to make this smarter: https://kivy.org/doc/stable/api-kivy.uix.behaviors.focus.html
            INC = 1
            if "shift" in modifiers:
                INC = -1
            which = self.MYTEXTBOX.MY_TAB_NUMBER
            next_tabber = (which + INC) % (myTextInput.TOTAL_NUMBER_OF_TABS + 1)
            self.MYTEXTBOX.TAB_NEXT = next_tabber
        return


    def keyboard_on_textinput(self, window, text):  # myLabel_and_Text
        # This gets hit with every key hit in the/a box
        TextInput.keyboard_on_textinput(self, window, text)
        return
# ----- class myLabel_and_Text - END   ------------------------------------------------------------------------------------


# ----- class RowCol - START ----------------------------------------------------------------------------------------
class RowCol(myTextInput):
    def __init__(self, *args, **kwargs):
        self.MYAPP = args[0]
        self.ANAME = args[1]
        kwargs["mycolor"] = NORMAL_COLOR
        kwargs["font_size"] = 13
        super().__init__(*args, **kwargs)
        self.bind(text=self.on_text_entry)  # RowCol
        #self.bind(text=self.tabber)
        return

    def on_text_entry(self, instance, value):
        if value != '' and int(value) >= 10:
            if isinstance(self, SumRow):
                self.MYAPP.ROW_SUMS_int[instance.ANUM] = int(value)
            else:
                self.MYAPP.COL_SUMS_int[instance.ANUM] = int(value)
            self.tabber(instance, value)
        return


    def tabber(self, instance, value):
        if not INIT_IS_DONE:
            return
        if value == "":
            return
        if int(value) < 10:
            return
        _joe = self.MY_TAB_NUMBER
        next_tab = (self.MY_TAB_NUMBER + 1) % (myTextInput.TOTAL_NUMBER_OF_TABS + 1)
        if next_tab == 0:
            # Don't go back to the 1st ("sum") but go to the first RowSum
            next_tab = 3
        self.TAB_NEXT = next_tab
        next_widget = self.TAB_ORDER[self.TAB_NEXT]
        SET_FOCUS(self, False)  # "SumRow for row #0" --> RowCol().on_focus()
        SET_FOCUS(next_widget)  # "SumCol for col #0" --> nowhere?
        return


    def get_sum(self):
        if isinstance(self, SumRow):
            sum = self.MYAPP.ROW_SUMS_int[self.ANUM]
        else:
            sum = self.MYAPP.COL_SUMS_int[self.ANUM]
        if sum is None:
            return
        return sum

    def get_num_evens(self, set_text=False):
        if isinstance(self, SumRow):
            num = self.MYAPP.get_numevens(row=self.ANUM)
        else:
            num = self.MYAPP.get_numevens(col=self.ANUM)
        if set_text:
            if str(num) != self.MYAPP.NUM_EVENS_box.MYTEXTBOX.text:
                self.MYAPP.NUM_EVENS_box.SET_TEXT(num)
        return num

    def get_must_have(self, set_text=False):
        if isinstance(self, SumRow):
            musthave = self.MYAPP.get_must_have(row=self.ANUM)
        else:
            musthave = self.MYAPP.get_must_have(col=self.ANUM)
        if set_text:
            if musthave:
                self.MYAPP.MUST_HAVE_INPUT.SET_TEXT(", ".join(map(str, musthave)))
            else:
                self.MYAPP.MUST_HAVE_INPUT.SET_TEXT()
        musthave.sort()
        return musthave

    def set_last_box(self, thesum, numevens, musthave):
        self.MYAPP.LastTopBoxes = {"row": None, "col": None, "thesum": thesum, "Number of evens": numevens, "Must Have": musthave}
        if isinstance(self, SumRow):
            self.MYAPP.LastTopBoxes = {"row": self.ANUM}
        else:
            self.MYAPP.LastTopBoxes = {"col": self.ANUM}
        return

    def get_one_of_these(self):
        if isinstance(self, SumRow):
            oneofthese = self.MYAPP.get_one_of_these(row=self.ANUM)
        else:
            oneofthese = self.MYAPP.get_one_of_these(col=self.ANUM)
        return oneofthese

    def update_GUI(self, pot_sols, thesum, numevens, musthave):
        #res = self.MYAPP.populate_potential_solutions_box(thesum=thesum, numevens=numevens, musthave=musthave, one_of_these=one_of_these)
        if not pot_sols:
            return
        self.MYAPP.REMAINING_SOLUTIONS_text.SET_TEXT(pot_sols)
        self.MYAPP.THESUM_box.SET_TEXT(thesum)
        self.MYAPP.NUM_EVENS_box.SET_TEXT(numevens)
        self.MYAPP.MUST_HAVE_INPUT.SET_TEXT(musthave)
        if isinstance(self, SumRow):
            self.MYAPP.refresh_remaining_options(pot_sols, rownum=self.ANUM)
            self.MYAPP.hightlight_Remaining_Options(p_row=self.ANUM)
        else:
            self.MYAPP.refresh_remaining_options(pot_sols, colnum=self.ANUM)
            self.MYAPP.hightlight_Remaining_Options(p_col=self.ANUM)
        return

    def on_focus(self, instance, value, *largs):  # RowCol
        # If I'm typing into a row or col sum#, then INIT is done
        self.MYAPP.INIT_IS_DONE_HANDLER.Turn_INIT_IS_DONE_on()
        #
        if value is False:
            SET_COLOR(self, NORMAL_COLOR)
            return

        # TODO: Don't do highlighting coloring when I click on it myself?
        self.MYAPP.reset_top_boxes(colors_only=False)
        SET_COLOR(self, HIGHLIGHT_COLOR)
        #
        thesum = self.get_sum()
        if thesum is None:
            return
        numevens = self.get_num_evens()
        musthave = self.get_must_have()
        #
        self.MYAPP.THESUM_box.SET_TEXT(thesum)
        self.MYAPP.NUM_EVENS_box.SET_TEXT(numevens)
        self.MYAPP.MUST_HAVE_INPUT.SET_TEXT(musthave)
        #
        self.set_last_box(thesum, numevens, musthave)
        oneofthese = self.get_one_of_these()
        #
        res = self.MYAPP.populate_potential_solutions_box(thesum=thesum, numevens=numevens, musthave=musthave, one_of_these=oneofthese)
        #
        eliminated_sols = res[0]
        pot_sols = res[1]
        self.MYAPP.ELIMINATED_text.SET_TEXT(eliminated_sols)
        if value and pot_sols:
            self.update_GUI(pot_sols, thesum, numevens, musthave)
        self.MYAPP.UNDO_HANDLER.Save_Undo_Level()
        return
# ----- class RowCol - END   ----------------------------------------------------------------------------------------


# ----- class SumRow - START ----------------------------------------------------------------------------------------
class SumRow(RowCol):  # myTextInput):
    def __str__(self):
        val = self.MYAPP.ROW_SUMS_int[self.ANUM]
        res = f"'SumRow for row #{self.ANUM}' ({val})"
        return res

    def __init__(self, *args, **kwargs):
        # self.MYAPP = args[0]  # self.MYTEXTBOX = myTextInput(self, f"{name}", readonly=self.READONLY)
        # self.ANAME = args[1]  # super().__init__(*args, **kwargs)
        # kwargs["mycolor"] = NORMAL_COLOR
        super().__init__(*args, **kwargs)
# ----- class SumRow - END   ----------------------------------------------------------------------------------------

# ----- class SumCol - START ----------------------------------------------------------------------------------------
class SumCol(RowCol):
    def __str__(self):
        val = self.MYAPP.COL_SUMS_int[self.ANUM]
        res = f"'SumCol for col #{self.ANUM}' ({val})"
        return res

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
# ----- class SumCol - END   ----------------------------------------------------------------------------------------


# ----- class mySolution - START ------------------------------------------------------------------------------------
class mySolution(myTextInput):
    def __str__(self):
        res = f"mySolution({self.AROW}, {self.ACOL})"
        return res

    def __init__(self, *args, **kwargs):
        self.NORMAL_COLOR = MY_SOLUTION_COLOR
        self.HIGHLIGHT_COLOR = MY_SOLUTION_HIGHLIGHT_COLOR
        kwargs["readonly"] = True
        kwargs["mycolor"] = self.NORMAL_COLOR
        kwargs["multiline"] = False
        super().__init__(*args, **kwargs)
        self.SET_COLOR("normal")

    def SET_RED(self):
        self.background_color = MY_RED
        return

    def SET_COLOR(self, which):  # mySolution
        if which == "normal":
            self.SET_COLOR_NORMAL()
        elif which == "highlight":
            self.SET_COLOR_HIGHLIGHT()
        else:
            myjoe()  # ???  2023-06-05
        return

    def SET_COLOR_NORMAL(self):
        self.background_color = self.NORMAL_COLOR
        return

    def SET_COLOR_HIGHLIGHT(self):
        self.background_color = self.HIGHLIGHT_COLOR
        return

    def on_focus(self, instance, value, *largs):  # mySolution
        if value is False:
            self.SET_COLOR_NORMAL()
            return
        self.MYAPP.reset_sum_colors()  # works
        self.MYAPP.reset_top_boxes(colors_only=True)
        if value is True:
            self.SET_COLOR_HIGHLIGHT()
        else:
            self.SET_COLOR_NORMAL()
        #
        if self.MYAPP.MY_SOLUTION_int[instance.AROW][instance.ACOL] != 0:
            # Only do this when there is something put into the solution
            self.MYAPP.RipItGood()
        return

    def SET_TEXT(self, value=""):  # mySolution
        row = self.AROW
        col = self.ACOL
        #
        if value == "":
            num = 0
        else:
            num = int(value)
        if self.MYAPP.INIT_IS_DONE_HANDLER:
            options = self.MYAPP.CELL_OPTIONS_int[row][col]
            if num !=0 and num not in options:
                return False  # do not let this bad # go into this cell
        else:
            _joe = 12  #
        ll, text = scrub_text(value)
        #self.text = num
        self.text = text  # this generates a new UNDO file when text!='', and it also helps with creating recursion
        self.MYAPP.SET_SOLUTION(row, col, num)
        self.MYAPP.CELL_OPTIONS_int[row][col] = []
        if all([yy!=0 for xx in self.MYAPP.MY_SOLUTION_int for yy in xx]):
            for row in range(4):
                for col in range(4):
                    SET_FOCUS(self.MYAPP.MY_SOLUTION_boxes[row][col], False)
                    SET_RED(self.MYAPP.MY_SOLUTION_boxes[row][col])
            # TODO: self.MEGA_POPULATE_OPTIONS(ok=True)???
            SET_FOCUS(self.MYAPP.THESUM_box.MYTEXTBOX)
        return
# ----- class mySolution - END   ------------------------------------------------------------------------------------

# ----- class myButton - START --------------------------------------------------------------------------------------
class myButton(ToggleButton):

    def __str__(self):
        res = "myButton"
        if self.MYROW is not None and self.MYCOL is not None:
            res = f"myButton ({self.MYROW}, {self.MYCOL}) {self.MYTEXT}"
        return res

    def __init__(self, app, **kwargs):
        # , font_size=12
        self.MYAPP = app
        self.MYROW = kwargs.get("row", None)
        self.MYCOL = kwargs.get("col", None)
        self.MYTEXT = kwargs.get("text", "")
        self.MYGROUP = kwargs.get("group", "")
        for arg in ["row", "col", "text", "group"]:
            kwargs.pop(arg, None)
        super(myButton, self).__init__(**kwargs)
        self.source = 'atlas://data/images/defaulttheme/checkbox_off'
        return

    # def __getattr__(self, item):
    #     return self.MYTEXT


    def on_state(self, widget, value):
        #self.MYAPP.reset_top_boxes()
        if value == "down":
            self.source = 'atlas://data/images/defaulttheme/checkbox_on'
            #self.source = 'atlas://data/images/defaulttheme/checkbox_off'
            self.MYAPP.SET_TEXT(self, "EVEN")
            self.MYTEXT = "EVEN"
        else:
            self.source = 'atlas://data/images/defaulttheme/checkbox_off'
            #self.source = 'atlas://data/images/defaulttheme/checkbox_on'
            self.MYAPP.SET_TEXT(self, "")
            self.MYTEXT = "odd"
        self.resum_numevens()
        return

    def resum_numevens(self):
        for row in range(4):
            numevens = sum([1 for xx in self.MYAPP.Buttons_ODD_EVEN[row] if xx.MYTEXT == "EVEN"])
            self.MYAPP.NUM_EVENS_BY_ROW_int[row] = numevens
        for col in range(4):
            numevens = 0
            for row in range(4):
                if self.MYAPP.Buttons_ODD_EVEN[row][col].MYTEXT == "EVEN":
                    numevens += 1
            self.MYAPP.NUM_EVENS_BY_COL_int[col] = numevens
        return

    def on_release(self):
        self.resum_numevens()
        # All a button can do is change the # of evens in a row/col
        _LastTopBoxes = self.MYAPP.LastTopBoxes
        row = _LastTopBoxes["row"]
        col = _LastTopBoxes["col"]
        widget = None
        if row is not None:
            new_numevens  = self.MYAPP.get_numevens(row)
            self.MYAPP.NUM_EVENS_box.SET_TEXT(new_numevens)
            widget = self.MYAPP.ROW_SUMS_boxes[row]
        elif col is not None:
            new_numevens  = self.MYAPP.get_numevens(col=_LastTopBoxes["col"])
            self.MYAPP.NUM_EVENS_box.SET_TEXT(new_numevens)
            widget = self.MYAPP.COL_SUMS_boxes[col]
        else:
            _joe = 12  # Nothing to do?
            #return
        #self.MYAPP.SAVE_AN_UNDO_FILE = True
        self.MYAPP.MEGA_POPULATE_OPTIONS()
        if widget:
            SET_FOCUS(widget)
        return

    def SET_TEXT(self, value=""):  # myButton
        ll, text = scrub_text(value)
        self.text = text
        return
# ----- class MyButton - END   --------------------------------------------------------------------------------------


# ----- class myInputs - START --------------------------------------------------------------------------------------
class myInputs(GridLayout):
    Buttons_ODD_EVEN = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
    CELL_OPTIONS_boxes = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
    CELL_OPTIONS_int = [[[], [], [], []], [[], [], [], []], [[], [], [], []], [[], [], [], []]]
    COL_SUMS_boxes = [0, 0, 0, 0]
    ELIMINATED_text = None
    EXPLANATION = None
    GREATEST_UNDO_FILE_NUM = 0
    #GUI_CREATED = False
    COL_SUMS_int = [0, 0, 0, 0]
    NUM_EVENS_BY_COL_int = [0, 0, 0, 0]
    NUM_EVENS_BY_ROW_int = [0, 0, 0, 0]
    ROW_SUMS_int = [0, 0, 0, 0]
    LAST_UNDO_FILE_NUM = 0
    LastTopBoxes = {"row": None, "col": None, "thesum": None, "Number of evens": None, "Must Have": None}
    MUST_HAVE_INPUT = None
    MY_SOLUTION_boxes = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
    MY_SOLUTION_int = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    NUMBERS_IN_ALL_text = None
    NUM_EVENS_box = None
    REMAINING_SOLUTIONS_text = None
    ROW_SUMS_boxes = [0, 0, 0, 0]
    THESUM_box = None
    THE_ACTUAL_SOLUTION_int = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    button_forward = None
    button_undo = None


    def __init__(self, which, **kwargs):
        self.which = which
        self.UNDO_HANDLER = cls_UNDO_FILES(MYAPP=self)
        self.INIT_IS_DONE_HANDLER = INIT_IS_DONE(MYAPP=self)
        GridLayout.__init__(self, **kwargs)
        self.cols = 1
        self.CREATE_THE_GUI()
        return


    def __str__(self):
        return f"myInputs()"

    def __missing__(self, key):
        _joe = 12  #


    def RESET_VARIABLES(self):
        if not INIT_IS_DONE:
            return  # there is nothing to reset
        self.COL_SUMS_int = [0, 0, 0, 0]
        self.MY_SOLUTION_int = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.THE_ACTUAL_SOLUTION_int = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.CELL_OPTIONS_int = [[[], [], [], []], [[], [], [], []], [[], [], [], []], [[], [], [], []]]
        self.ROW_SUMS_int = [0, 0, 0, 0]
        self.NUM_EVENS_BY_ROW_int = [0, 0, 0, 0]
        self.NUM_EVENS_BY_COL_int = [0, 0, 0, 0]
        cls_Explanation.MY_DATA = {}
        #
        self.THESUM_box.SET_TEXT()
        self.NUM_EVENS_box.SET_TEXT()
        self.MUST_HAVE_INPUT.SET_TEXT()
        self.NUMBERS_IN_ALL_text.SET_TEXT()
        self.REMAINING_SOLUTIONS_text.SET_TEXT()
        self.ELIMINATED_text.SET_TEXT()
        #
        for dd in self.COL_SUMS_boxes:
            dd.SET_TEXT()
        for row in range(4):
            self.ROW_SUMS_boxes[row].SET_TEXT()
            self.COL_SUMS_boxes[row].SET_TEXT()
            for col in range(4):
                self.MY_SOLUTION_boxes[row][col].SET_TEXT()
                self.CELL_OPTIONS_boxes[row][col].SET_TEXT()
        self.LastTopBoxes = {"row": None, "col": None, "thesum": None, "Number of evens": None, "Must Have": None}
        #
        return

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def CREATE_THE_GUI(self):
        #
        self.add_widget(self.MAKE_Menu_Buttons(size_hint=(1, .15)))
        #
        self.add_widget(self.MAKE_Top_Section(size_hint=(1, .3)))
        #
        self.add_widget(self.MAKE_Buttons(size_hint=(1, .25)))
        #
        self.add_widget(self.MAKE_Remaining_Options_and_Solutions(size_hint=(1, .3)))
        #
        #self.GUI_CREATED = True
        #
        return

    def MAKE_Menu_Buttons(self, size_hint):
        """ Note: GridLayout(row_force_default=True, row_default_height=100, col_force_default=True, col_default_width=400)
                  This forces the entire GridLayout to have a certain size. So if the buttons don't fit the size,
                  then it leaves a blank, black, space to fill in the rest
        """
        mainlayout = GridLayout(size_hint=size_hint)  # row_force_default=True, row_default_height=100, col_force_default=True, col_default_width=400)
        mainlayout.cols = 1

        sublayout1 = GridLayout()
        sublayout1.cols = 4
        sublayout2 = GridLayout()
        sublayout2.cols = 4

        sublayout1.add_widget(Button(text="CLEAR", on_press=self.CLEAR_btn))
        # mainlayout.add_widget(Button(text="Choose Puzzle", on_press=self.ChoosePuzzle))
        sublayout1.add_widget(Button(text="Load Puzzle (don't)", on_press=self.LoadPuzzle))
        sublayout1.add_widget(Button(text="Save Puzzle", on_press=self.SavePuzzle))
        sublayout1.add_widget(Button(text="Load saved Puzzle", on_press=self.LoadSavedPuzzle_btn))
        sublayout2.add_widget(Button(text="Rip it good", on_press=self.RipItGood_btn))
        #
        self.button_undo = Button(text="UNDO", on_press=self.UNDO_HANDLER.UNDO)  #  self.UNDO)
        sublayout2.add_widget(self.button_undo)
        #
        self.button_forward = Button(text="Forward", on_press=self.ForwardOne)
        sublayout2.add_widget(self.button_forward)
        #
        sublayout2.add_widget(Button(text="Exit", on_press=self.Exit))
        #
        mainlayout.add_widget(sublayout1)
        mainlayout.add_widget(sublayout2)
        #
        return mainlayout


    def MAKE_Top_Section(self, size_hint):
        """ """
        TOP_SEC = GridLayout(size_hint=size_hint)  # row_force_default=True, row_default_height=40, col_force_default=True, col_default_width=400)
        TOP_SEC.cols = 1
        # Accepts input:
        self.THESUM_box = myLabel_and_Text(app=self, GUI=TOP_SEC, name="The sum", readonly=False)            #, font_size=13), textbindfn=self.entry_COVER_NEW)
        self.NUM_EVENS_box = myLabel_and_Text(app=self, GUI=TOP_SEC, name="Number of evens", readonly=False) #, font_size=13), textbindfn=self.entry_COVER_NEW)
        self.MUST_HAVE_INPUT = myLabel_and_Text(app=self, GUI=TOP_SEC, name="Must Have", readonly=False)     #, font_size=13), textbindfn=self.entry_COVER_NEW)
        # Readonly:
        self.NUMBERS_IN_ALL_text = myLabel_and_Text(app=self, GUI=TOP_SEC, name="Number in all", readonly=True)                             #, font_size=11)
        self.REMAINING_SOLUTIONS_text = myLabel_and_Text(app=self, GUI=TOP_SEC, name="Remaining Solutions", readonly=True, multiline=False) #, font_size=13)
        self.ELIMINATED_text = myLabel_and_Text(app=self, GUI=TOP_SEC, name="Eliminated Solutions", readonly=True, multiline=True)          #, font_size=13)
        return TOP_SEC


    def MAKE_Buttons(self, size_hint):
        # The 4x4 of odd/even cells
        CELLS = GridLayout(size_hint=size_hint)  #size_hint=size_hint)
        CELLS.cols = 1
        #
        left = .125
        middle = .647
        right = 1 - left - middle
        #
        # THE BUTTONS:
        for row in range(4):
            AROW = BoxLayout()
            # LEFT:  (this is the main chunk of this section)
            arow_middle = BoxLayout()
            #
            for col in range(4):
                acell = myButton(self, text='odd', group=f"oe{row}{col}", row=row, col=col, font_size=12)
                self.Buttons_ODD_EVEN[row][col] = acell
                arow_middle.add_widget(acell)
            AROW.add_widget(arow_middle)

            # RIGHT:  R SUM
            arow_right_r_sum = BoxLayout()
            #
            rowsum = SumRow(self, "rowsum", num=row)
            arow_right_r_sum.add_widget(rowsum)
            AROW.add_widget(arow_right_r_sum)
            self.ROW_SUMS_boxes[row] = rowsum
            #
            # add the row to the main GUI:
            CELLS.add_widget(AROW)

        # ---------------------------------------
        # THE C SUMS ROW
        # ---------------------------------------
        left = .125
        middle = .647
        right = 1 - left - middle
        BOTTOM_ROW = BoxLayout()
        #
        # LEFT SIDE:
        bottom_middle = BoxLayout()
        for col in range(4):
            sumcolbox = SumCol(self, "colsum", num=col)
            bottom_middle.add_widget(sumcolbox)
            self.COL_SUMS_boxes[col] = sumcolbox
        BOTTOM_ROW.add_widget(bottom_middle)
        BOTTOM_ROW.add_widget(Label(text=""))

        self.EXPLANATION = cls_Explanation(MYAPP=self)
        CELLS.add_widget(self.EXPLANATION)

        CELLS.add_widget(BOTTOM_ROW)

        return CELLS

    def MAKE_Remaining_Options_and_Solutions(self, size_hint):
        MAIN = GridLayout(size_hint=size_hint)
        MAIN.cols = 2
        #
        OPTIONS = GridLayout()
        OPTIONS.cols = 1
        OPTIONS.add_widget(Label(text="REMAINING OPTIONS:"))
        for row in range(4):
            row_layout = BoxLayout()
            for col in range(4):
                box = RemainingOptions(self, "REMAINING_OPTIONS", row=row, col=col, mycolor="white", multiline=False, readonly=True)  # , is_focusable=False)
                self.CELL_OPTIONS_boxes[row][col] = box
                row_layout.add_widget(box)
            OPTIONS.add_widget(row_layout)
        #
        MAIN.add_widget(OPTIONS)

        SOLUTIONS = GridLayout()  # size_hint=size_hint)
        SOLUTIONS.cols = 1
        #
        SOLUTIONS.add_widget(Label(text="MY SOLUTION:"))
        #
        for row in range(4):
            row_layout = BoxLayout()
            for col in range(4):
                box = mySolution(self, "MY_SOLUTION_int", row=row, col=col)  # , mycolor="white", multiline=False)
                self.MY_SOLUTION_boxes[row][col] = box
                box.bind(text=self.entry_A_SOLUTION)
                row_layout.add_widget(box)
            SOLUTIONS.add_widget(row_layout)
        #
        MAIN.add_widget(SOLUTIONS)

        return MAIN
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


    def get_must_have(self, row=None, col=None):
        assert not (row is None and col is None)
        if row is not None:
            res = [xx for xx in self.MY_SOLUTION_int[row] if xx != 0]
        else:
            res = [xx[col] for xx in self.MY_SOLUTION_int if xx[col] != 0]
        return res


    def entry_TEXT(self, instance, value):
        if value:
            thesum = int(value)
        else:
            return
        if thesum < 10:
            return
        if isinstance(instance, SumRow):
            therow = instance.ANUM  # tab after this
            self.ROW_SUMS_int[therow] = int(value)
            numevens = self.get_numevens(row=therow)
            musthave = self.get_must_have(row=therow)
            res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, musthave=musthave, one_of_these=[])
            eliminated_sols = res[0]
            pot_sols = res[1]
            self.ELIMINATED_text.SET_TEXT(eliminated_sols)
            if pot_sols:
                self.refresh_remaining_options(pot_sols, rownum=therow)
        elif isinstance(instance, SumCol):
            thecol = instance.ANUM
            self.COL_SUMS_int[thecol] = int(value)
        self.MEGA_POPULATE_OPTIONS()

        # which = instance.MY_TAB_NUMBER
        # next_tabber = (which + 1) % (myTextInput.TOTAL_NUMBER_OF_TABS + 1)
        # instance.TAB_NEXT = next_tabber
        # instance.TAB_ORDER[instance.TAB_NEXT].focus = True

        return

    def SET_TEXT(self, widget, value: str):  # myInputs
        text = value
        if isinstance(widget, (SumRow, SumCol, myLabel_and_Text)):
            widget = widget.MYTEXTBOX
        if not isinstance(text, str):
            text = str(text)
        widget.text = text
        return


    def keyboard_on_key_up(self, window, keycode):  # myInputs
        if keycode[1] == "tab":
            _joe = 12
        # elif keycode[1] == "backspace":
        #     print("print backspace up", keycode)
        #TextInput.keyboard_on_key_down(self, window, keycode, text, modifiers)
        return

    def reset_sum_colors(self):
        for cell in self.ROW_SUMS_boxes:
            SET_COLOR(cell, NORMAL_COLOR)
        for cell in self.COL_SUMS_boxes:
            SET_COLOR(cell, NORMAL_COLOR)
        return

    def reset_remaining_options_colors(self, force=False):
        for row in range(4):
            for col in range(4):
                cell = self.CELL_OPTIONS_boxes[row][col]
                if force and cell.background_color != MY_RED:
                    cell.background_color = REMAINING_OPTIONS_COLOR
                else:
                    SET_COLOR(cell, REMAINING_OPTIONS_COLOR)
        return


    def hightlight_Remaining_Options(self, p_row=None, p_col=None):
        for row in range(4):
            for col in range(4):
                cur_color = self.CELL_OPTIONS_boxes[row][col].background_color
                if cur_color != MY_RED:
                    SET_COLOR(self.CELL_OPTIONS_boxes[row][col], REMAINING_OPTIONS_COLOR)
        if p_row is not None:
            # Highlight row:
            for cell in self.CELL_OPTIONS_boxes[p_row]:
                cur_color = cell.background_color
                if cur_color != MY_RED:
                    SET_COLOR(cell, HIGHLIGHT_COLOR)
                    _joe = cell.background_color
        elif p_col is not None:
            # Highlight col:
            for row in self.CELL_OPTIONS_boxes:
                cell = row[p_col]
                cur_color = cell.background_color
                if cur_color != MY_RED:
                    SET_COLOR(cell, HIGHLIGHT_COLOR)
                    _joe = cell.background_color
        return

    def get_one_of_these(self, row=None, col=None):
        assert not (row is None and col is None)
        if row is not None:
            res = [xx for xx in self.CELL_OPTIONS_int[row] if xx]
        else:
            res = [xx[col] for xx in self.CELL_OPTIONS_int if xx[col]]
        #res = list(set(flatten_list(res)))
        return res  # .sort()


    def on_focus(self, instance, value, *largs):  # myInputs
        self.reset_sum_colors()  # DOES THIS GET HIT?
        self.reset_top_boxes(colors_only=True)
        if value is True:
            SET_COLOR(instance, HIGHLIGHT_COLOR)
        return


    def CLEAR_btn(self, instance=None):
        delete_undo_files()
        self.LAST_UNDO_FILE_NUM = 0
        self.UNDO_HANDLER.CLEAR()
        self.CLEAR(instance)
        return

    def CLEAR(self, instance=None):
        global DO_NOT_MEGA_POPULATE_OPTIONS
        # FIXME: Should 'INIT_IS_DONE' be reset here too?
        self.button_undo.text = "UNDO"
        self.button_forward.text = "Forward"
        #
        cur_dnmp_status = DO_NOT_MEGA_POPULATE_OPTIONS
        DO_NOT_MEGA_POPULATE_OPTIONS = True
        self.RESET_VARIABLES()
        self.reset_top_boxes(colors_only=False)
        for row in range(4):
            self.ROW_SUMS_boxes[row].SET_TEXT()
            for col in range(4):
                self.canvas.ask_update()
                self.COL_SUMS_boxes[row].SET_TEXT()
                self.Buttons_ODD_EVEN[row][col].state = "normal"
                self.CELL_OPTIONS_boxes[row][col].SET_TEXT()
                SET_COLOR(self.CELL_OPTIONS_boxes[row][col], REMAINING_OPTIONS_COLOR, force=True)
                self.MY_SOLUTION_boxes[row][col].SET_TEXT()
                # SET_COLOR(self.MY_SOLUTION_boxes[row][col], MY_SOLUTION_COLOR)
                self.MY_SOLUTION_boxes[row][col].SET_COLOR_NORMAL()
        self.EXPLANATION.CLEAR()
        DO_NOT_MEGA_POPULATE_OPTIONS = cur_dnmp_status
        #
        #SET_FOCUS(self.THESUM_box)
        return


    def ForwardOne(self, instance):
        forward = self.LAST_UNDO_FILE_NUM + 1
        forward_file = f"UndoFiles/{TODAY}_{forward}.txt"
        if not file_exists(forward_file):
            return
        #
        self.LAST_UNDO_FILE_NUM += 1
        forwards_left = self.GREATEST_UNDO_FILE_NUM - self.LAST_UNDO_FILE_NUM
        #
        self.Undo_engine(instance, forward_file)
        #
        if self.UNDO_HANDLER.GO_BACK_TO is None:
            self.button_undo.text = f"UNDO b ({self.LAST_UNDO_FILE_NUM})"
        else:
            self.button_undo.text = f"UNDO b ({self.LAST_UNDO_FILE_NUM}/{self.UNDO_HANDLER.GO_BACK_TO})"
        if forwards_left:
            self.button_forward.text = f"Forward ({forwards_left})"
        else:
            self.button_forward.text = f"Forward"
        return


    def Undo(self, instance):  # myInputs
        # FIXME: DEBUG THIS, IT DOESN'T WORK AT ALL!
        self.LAST_UNDO_FILE_NUM = max(0, self.LAST_UNDO_FILE_NUM - 1)
        previous_file = f"UndoFiles/{TODAY}_{self.LAST_UNDO_FILE_NUM}.txt"
        if not file_exists(previous_file):
            self.CLEAR()
            self.reset_remaining_options_colors()
            instance.text = f"UNDO"
            self.button_forward.text = f"Forward ({self.GREATEST_UNDO_FILE_NUM})"
            return
        self.Undo_engine(instance, previous_file)
        #
        if self.UNDO_HANDLER.GO_BACK_TO is None:
            self.button_undo.text = f"UNDO c ({self.LAST_UNDO_FILE_NUM})"
        else:
            self.button_undo.text = f"UNDO c ({self.LAST_UNDO_FILE_NUM}/{self.UNDO_HANDLER.GO_BACK_TO})"
        forwards_left = self.GREATEST_UNDO_FILE_NUM - self.LAST_UNDO_FILE_NUM
        self.button_forward.text = f"Forward ({forwards_left})"
        return


    def Undo_engine(self, instance, required_file):
        self.UNDO_HANDLER.turn_undo_saving_off()
        self.LoadSavedPuzzle(filename=required_file, from_undo=True)
        self.UNDO_HANDLER.turn_undo_saving_on()
        return


    def Exit(self, instance):
        sys.exit(0)



    def entry_R_POT_SOLS(self, instance, value):
        thesum = int(value)  # does this get hit?
        if thesum < 10:
            return
        therow = instance.ANUM
        self.ROW_SUMS_int[therow] = int(value)
        numevens = sum([1 for xx in self.Buttons_ODD_EVEN[instance.ANUM] if xx.MYTEXT == "EVEN"])
        musthave = self.get_must_have(row=therow)
        res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, musthave=musthave, one_of_these=(0/0))
        eliminated_sols = res[0]
        pot_sols = res[1]
        self.ELIMINATED_text.SET_TEXT(eliminated_sols)
        if pot_sols:
            self.refresh_remaining_options(pot_sols, rownum=therow)
            #self.find_unique_to_all(pot_sols)
        else:
            _joe = 12  # now what?
        self.MEGA_POPULATE_OPTIONS()
        return


    def reset_top_boxes(self, colors_only):
        SET_COLOR(self.THESUM_box.MYTEXTBOX, NORMAL_COLOR)
        SET_COLOR(self.NUM_EVENS_box.MYTEXTBOX, NORMAL_COLOR)
        SET_COLOR(self.MUST_HAVE_INPUT.MYTEXTBOX, NORMAL_COLOR)

        if colors_only:
            return
        self.THESUM_box.SET_TEXT()
        self.NUM_EVENS_box.SET_TEXT()
        self.MUST_HAVE_INPUT.SET_TEXT()
        self.NUMBERS_IN_ALL_text.SET_TEXT()
        self.ELIMINATED_text.SET_TEXT()
        self.REMAINING_SOLUTIONS_text.SET_TEXT()
        #
        return


    def get_numevens(self, row=None, col=None):
        assert isinstance(row, int) or isinstance(col, int)
        if not row is None:
            numevens = sum([1 for xx in self.Buttons_ODD_EVEN[row] if xx.MYTEXT == "EVEN"])
        else:
            numevens = 0
            for row in range(4):
                if self.Buttons_ODD_EVEN[row][col].MYTEXT == "EVEN":
                    numevens += 1
        return numevens


    def MEGA_POPULATE_OPTIONS(self, ok=False):
        """ """
        if DO_NOT_MEGA_POPULATE_OPTIONS:
            return

        for row in range(4):
            thesum = self.ROW_SUMS_int[row]
            if not thesum: continue
            numevens = self.get_numevens(row=row)
            musthave = self.get_must_have(row=row)
            #
            res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, musthave=musthave, one_of_these=[])
            eliminated_sols = res[0]
            pot_sols = res[1]
            self.ELIMINATED_text.SET_TEXT(eliminated_sols)
            if pot_sols:
                res = self.refresh_remaining_options(pot_sols, rownum=row)
                if res:
                    return res
        #
        for col in range(4):
            thesum = self.COL_SUMS_int[col]
            if not thesum: continue
            numevens = self.get_numevens(col=col)
            musthave = self.get_must_have(col=col)
            #
            res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, musthave=musthave, one_of_these=[])
            eliminated_sols = res[0]
            pot_sols = res[1]
            self.ELIMINATED_text.SET_TEXT(eliminated_sols)
            if pot_sols:
                res = self.refresh_remaining_options(pot_sols, colnum=col)
                if res:
                    return res
        #
        # See if there is a cell with only one option left:
        for row in range(4):
            for col in range(4):
                if self.MY_SOLUTION_int[row][col] != 0:
                    SET_COLOR(self.CELL_OPTIONS_boxes[row][col], REMAINING_OPTIONS_COLOR)
                else:
                    cell = self.CELL_OPTIONS_int[row][col]
                    if self.CELL_OPTIONS_int[row][col]:
                        if len(self.CELL_OPTIONS_int[row][col]) == 1:
                            #SET_COLOR(self.CELL_OPTIONS_boxes[row][col], MY_RED)  #  "red"
                            SET_RED(self.CELL_OPTIONS_boxes[row][col])
                        elif len(self.CELL_OPTIONS_int[row][col]) == 0:
                            SET_COLOR(self.CELL_OPTIONS_boxes[row][col], NORMAL_COLOR)
        #
        # Back this up as a future 'undo' level
        #if SAVE_AN_UNDO_FILE:
        #    self.Save_Undo_Level()
        self.UNDO_HANDLER.Save_Undo_Level()
        return


    def get_solutions_for_row_and_col(self, rownum, colnum):
        sols = {}
        if rownum:
            for num in self.MY_SOLUTION_int[rownum]:
                sols[num] = 1
        if colnum:
            for row in range(4):
                sols[self.MY_SOLUTION_int[row][colnum]] = 1
        sols.pop(0, None)
        sollist = list(set(sols.keys()))
        return sollist


    def find_unique_to_all(self, pot_sols, rownum=None, colnum=None):
        row_col_sols = self.get_solutions_for_row_and_col(rownum, colnum)
        ll = len(pot_sols)
        if ll == 1:
            # If there is only one solution left, every number in it is 'unique'
            uta = pot_sols[0]
        else:
            adict = {}
            for arr in pot_sols:
                for num1 in arr:
                    adict[num1] = adict.get(num1, 0) + 1
            uta = []
            for num2, ct in adict.items():
                if ct == ll:
                    uta.append(num2)  # found one!
        # from the #s that are in all remaining solutions, remove any that are a solution
        # for this row/col
        # for num in uta:
        #     if num in row_col_sols:
        #         uta.remove(num)
        if uta:
            if len(uta) == len(flatten_list(pot_sols)):
                self.NUMBERS_IN_ALL_text.SET_TEXT()  # Note: this returns
            else:
                unique_str = ", ".join([str(xx) for xx in uta])
                self.NUMBERS_IN_ALL_text.SET_TEXT(unique_str)
                if len(uta) == 1:
                    if rownum is not None and not any([True for xx in self.MY_SOLUTION_int[rownum] if xx != 0]):
                        SET_RED(self.NUMBERS_IN_ALL_text)  # Note: this returns
                    elif colnum is not None and not any([xx[colnum] for xx in self.MY_SOLUTION_int if xx[colnum] != 0]):
                        SET_RED(self.NUMBERS_IN_ALL_text)
                    #SET_RED(self.NUMBERS_IN_ALL_text)
                else:
                    SET_COLOR(self.NUMBERS_IN_ALL_text, NO_FOCUS_COLOR)  # Note: this returns
        else:
            self.NUMBERS_IN_ALL_text.SET_TEXT()
            SET_COLOR(self.NUMBERS_IN_ALL_text, NO_FOCUS_COLOR)
            # Note: this returns
        return uta


    def net_out(self, row, col, these_options):
        cur_opts = self.CELL_OPTIONS_int[row][col]
        opts = None
        if not cur_opts is None:
            _joe = 12  # only can remove options here
        if not cur_opts:
            opts = these_options
        else:
            opts = [xx for xx in cur_opts if xx in these_options]
        opts.sort()
        opts_str = ", ".join([str(xx) for xx in opts])
        return opts, opts_str


    def net_out_new(self, row, col, pot_sols, set_text=False):
        """ """
        flat_pot_sols = list(set(flatten_list(pot_sols)))
        flat_pot_sols.sort()
        even_pot_sols = [xx for xx in flat_pot_sols if xx in [2, 4, 6, 8]]
        odd_pot_sols = [xx for xx in flat_pot_sols if xx in [1, 3, 5, 7, 9]]
        #
        if self.Buttons_ODD_EVEN[row][col].MYTEXT == "EVEN":
            kk, kkstr = self.net_out(row, col, even_pot_sols)
        else:
            kk, kkstr = self.net_out(row, col, odd_pot_sols)
        #
        self.CELL_OPTIONS_int[row][col] = kk
        if set_text:
            self.SET_TEXT(self.CELL_OPTIONS_boxes[row][col], kkstr)
            self.CELL_OPTIONS_boxes[row][col].SET_TEXT(kkstr)

        cur_opts = kk  # self.CELL_OPTIONS_int[row][col]
        #opts = None
        if not cur_opts:
            opts = flat_pot_sols
        else:
            opts = [xx for xx in cur_opts if xx in flat_pot_sols]
        opts.sort()
        opts_str = ", ".join([str(xx) for xx in opts])
        return opts, opts_str


    def mega_recalculate_cell_options(self):
        _joe = 12  #
        for row in range(4):
            rowsumbox = self.ROW_SUMS_boxes[row]
            for col, celloptions in enumerate(self.ROW_SUMS_boxes):
                # sol = self.MY_SOLUTION_int[row][col]
                thesum = rowsumbox.get_sum()
                numevens = rowsumbox.get_num_evens()
                musthave = rowsumbox.get_must_have()
                oneofthese = rowsumbox.get_one_of_these()
                #
                res = self.populate_potential_solutions_box(thesum, numevens, musthave, oneofthese)
                pot_sols = res[1]
                #
                kk, kkstr = self.net_out_new(row, col, pot_sols)
                self.CELL_OPTIONS_int[row][col] = kk
        #
        for col in range(4):
            colsumbox = self.COL_SUMS_boxes[col]
            for row, celloptions in enumerate(self.COL_SUMS_boxes):
                # sol = self.MY_SOLUTION_int[row][col]
                thesum = colsumbox.get_sum()
                numevens = colsumbox.get_num_evens()
                musthave = colsumbox.get_must_have()
                oneofthese = colsumbox.get_one_of_these()
                #
                res = self.populate_potential_solutions_box(thesum, numevens, musthave, oneofthese)
                pot_sols = res[1]
                #
                kk, kkstr = self.net_out_new(row, col, pot_sols)
                self.CELL_OPTIONS_int[row][col] = kk
        #
        return


    def refresh_remaining_options(self, pot_sols, rownum=None, colnum=None, ok=False):
        # -----------------------------------------------------------------------
        assert rownum is not None or colnum is not None
        #self.reset_remaining_options_colors() ###########################################
        # TODO:
        # 1) use mega_recalculate_cell_options()
        # 2) I should tigten this up into just one section, not an if-else block
        fn = get_calling_function()
        if fn not in ["MEGA_POPULATE_OPTIONS", "update_GUI"]:
            _joe = 12  #
        unique_to_all = self.find_unique_to_all(pot_sols, rownum=rownum, colnum=colnum)
        flat_pot_sols = list(set(flatten_list(pot_sols)))
        flat_pot_sols.sort()
        even_pot_sols = [xx for xx in flat_pot_sols if xx in [2, 4, 6, 8]]
        odd_pot_sols = [xx for xx in flat_pot_sols if xx not in [2, 4, 6, 8]]
        even_pot_sols.sort()
        odd_pot_sols.sort()

        ALL_SUMS_ARE_FILLED_IN = all([xx != 0 for xx in self.ROW_SUMS_int + self.COL_SUMS_int])

        # Fixme: I need to make a version of this that just generates #s for CELL_OPTIONS_int, *THEN* updates the boxes

        if not rownum is None:
            for col in range(4):
                sol = self.MY_SOLUTION_int[rownum][col]
                if sol and sol in flat_pot_sols:
                    flat_pot_sols.remove(sol)
            for col, THE_CELL in enumerate(self.CELL_OPTIONS_boxes[rownum]):
                if self.MY_SOLUTION_int[rownum][col] != 0:
                    # A solved cell has no remaining options
                    self.SET_TEXT(THE_CELL, "")
                    continue
                if self.Buttons_ODD_EVEN[rownum][col].MYTEXT == "EVEN":
                    kk, kkstr = self.net_out(rownum, col, even_pot_sols)
                    self.CELL_OPTIONS_int[rownum][col] = kk
                    self.SET_TEXT(THE_CELL, kkstr)
                else:
                    kk, kkstr = self.net_out(rownum, col, odd_pot_sols)
                    self.CELL_OPTIONS_int[rownum][col] = kk
                    self.SET_TEXT(THE_CELL, kkstr)
                #
                if len(unique_to_all) == 1 and unique_to_all[0] in kk:
                    if len(kk) == 1:
                        self.EXPLANATION.ADD_EXPLANATION(THE_CELL.AROW, col, kk[0])                    # <------------------------------
                        SET_RED(THE_CELL)
                        SET_RED(self.NUMBERS_IN_ALL_text)
                    else:
                        SET_COLOR(THE_CELL, "palevioletred")
                if self.INIT_IS_DONE_HANDLER and ALL_SUMS_ARE_FILLED_IN and len(unique_to_all) != 1:
                    for uu in unique_to_all:
                        if sum([1 for xx in self.CELL_OPTIONS_int[rownum] if uu in xx]) == 1:
                            for ct in range(4):
                                co = self.CELL_OPTIONS_int[rownum][ct]
                                if uu in co:
                                    self.EXPLANATION.ADD_EXPLANATION(rownum, ct, uu)               # <------------------------------xxxxx
                                    SET_RED(self.CELL_OPTIONS_boxes[rownum][ct])
                                    break  # -> "for uu in unique_to_all:" Add it to below
                else:
                    # Number is probably a solution already
                    SET_COLOR(THE_CELL, REMAINING_OPTIONS_COLOR)
                    SET_COLOR(self.NUMBERS_IN_ALL_text, NO_FOCUS_COLOR)
            # -----------------------------
        else:  # doing a column
            # -----------------------------
            for row in range(4):
                sol = self.MY_SOLUTION_int[row][colnum]
                if sol and sol in flat_pot_sols:
                    flat_pot_sols.remove(sol)
            even_pot_sols = [xx for xx in flat_pot_sols if xx in [2, 4, 6, 8]]
            even_pot_sols.sort()
            odd_pot_sols = [xx for xx in flat_pot_sols if xx not in [2, 4, 6, 8]]
            odd_pot_sols.sort()
            for row in range(4):
                THE_CELL = self.CELL_OPTIONS_boxes[row][colnum]  # THE_CELL  THE_CELL  THE_CELL  THE_CELL
                if self.MY_SOLUTION_int[row][colnum] != 0:
                    # A solved cell has no remaining options
                    if THE_CELL.text:
                        THE_CELL.SET_TEXT()
                    continue
                if self.Buttons_ODD_EVEN[row][colnum].MYTEXT == "EVEN":
                    kk, kkstr = self.net_out(row, colnum, even_pot_sols)
                    self.CELL_OPTIONS_int[row][colnum] = kk
                    THE_CELL.SET_TEXT(kkstr)
                else:
                    kk, kkstr = self.net_out(row, colnum, odd_pot_sols)
                    self.CELL_OPTIONS_int[row][colnum] = kk
                    THE_CELL.SET_TEXT(kkstr)
                #
                if len(unique_to_all) == 1 and unique_to_all[0] in kk:
                    if len(kk) == 1:
                        self.EXPLANATION.ADD_EXPLANATION(row, colnum, unique_to_all[0])            # <------------------------------
                        SET_RED(THE_CELL)
                        SET_RED(self.NUMBERS_IN_ALL_text)
                    else:
                        # Number is probably a solution already
                        SET_COLOR(THE_CELL, REMAINING_OPTIONS_COLOR)
                        SET_COLOR(self.NUMBERS_IN_ALL_text, NO_FOCUS_COLOR)
                if self.INIT_IS_DONE_HANDLER and ALL_SUMS_ARE_FILLED_IN and len(unique_to_all) != 1:
                    for uu in unique_to_all:
                        if sum([1 for xx in [xx[colnum] for xx in self.CELL_OPTIONS_int] if uu in xx]) == 1:
                            for ct in range(4):
                                co = self.CELL_OPTIONS_int[ct][colnum]
                                if uu in co:
                                    self.EXPLANATION.ADD_EXPLANATION(ct, colnum, uu)               # <------------------------------
                                    SET_RED(self.CELL_OPTIONS_boxes[ct][colnum])
                else:
                    # Number is probably a solution already
                    SET_COLOR(THE_CELL, REMAINING_OPTIONS_COLOR)
                    SET_COLOR(self.NUMBERS_IN_ALL_text, NO_FOCUS_COLOR)
        #
        self.EXPLANATION.SET_TEXT()
        return False


    def entry_A_SOLUTION(self, instance, value):
        global DO_NOT_CHECK_SOLUTION
        if DO_NOT_CHECK_SOLUTION is True:
            return
        # when I enter something into a solution, it then acts as a 'must have' for that row and col
        if value == "":
            sol = 0
        else:
            sol = int(value)
        row = instance.AROW
        col = instance.ACOL
        if self.MY_SOLUTION_int[row][col] != sol or self.CELL_OPTIONS_int[row][col] != []:
            if self.SET_SOLUTION(row, col, sol):
                if self.INIT_IS_DONE_HANDLER and DO_NOT_MEGA_POPULATE_OPTIONS is False:
                    self.MEGA_POPULATE_OPTIONS(ok=True)  # entry_A_SOLUTION
        return



    def populate_potential_solutions_box(self, thesum, numevens, musthave, one_of_these, set_text=False):
        if set_text:
            self.REMAINING_SOLUTIONS_text.SET_TEXT()
        #
        all_sols, good_sols, eliminated_sols = [], [], []
        if not (thesum == 0 or numevens == 0):
            if not thesum or not numevens:
                return eliminated_sols, good_sols
        #
        thesum = int(thesum)
        if thesum < 10:
            return eliminated_sols, good_sols
        #
        if isinstance(musthave, str):
            musthave = list(map(int, musthave.replace(",", "").split()))
        numevens = int(numevens)
        #
        if not (thesum in ALL_POTENTIAL_SOLUTIONS and numevens in ALL_POTENTIAL_SOLUTIONS[thesum]):
            return eliminated_sols, good_sols
        #
        all_sols = ALL_POTENTIAL_SOLUTIONS[thesum][numevens]
        pot_sols = all_sols.copy()
        if not musthave and not one_of_these:
            if set_text:
                self.REMAINING_SOLUTIONS_text.SET_TEXT(pot_sols)
            return eliminated_sols, pot_sols
        #
        tmp_sols = []
        if not musthave:
            tmp_sols = pot_sols
        else:
            for a_sol in pot_sols:
                res = all([yy in a_sol for yy in musthave])
                if res:
                    tmp_sols.append(a_sol)
                else:
                    eliminated_sols.append(a_sol)
        #
        if not one_of_these:
            good_sols = tmp_sols
        else:
            # For each set of #s for a cell, the solution should have at least one of them
            for one_sol in tmp_sols:
                res = True  # assume it'll work
                for arr in one_of_these:
                    rr = any([xx in arr for xx in one_sol])
                    res = res and rr
                if res:
                    good_sols.append(one_sol)
                else:
                    eliminated_sols.append(one_sol)
        eliminated_sols.sort()
        good_sols.sort()
        if set_text:
            self.REMAINING_SOLUTIONS_text.SET_TEXT(good_sols)
        #
        return eliminated_sols, good_sols


    def entry_COVER(self, instance, value):
        #global SAVE_AN_UNDO_FILE
        #curstatus = SAVE_AN_UNDO_FILE
        #SAVE_AN_UNDO_FILE = False

        if instance.ANAME == "The sum":
            cur = self.THESUM_box.MYTEXTBOX.text
            if cur != value:
                self.entry_THE_SUM(instance, value)
        elif instance.ANAME == "Number of evens":
            cur = self.NUM_EVENS_box.MYTEXTBOX.text
            if cur != value:
                self.entry_NUM_EVENS(instance, value)
        elif instance.ANAME == "Must Have":
            cur = self.MUST_HAVE_INPUT.MYTEXTBOX.text
            if cur != value:
                self.entry_MUST_HAVE(instance, value)
        else:
            _joe = 12  # ??
        #SAVE_AN_UNDO_FILE = curstatus
        return


    # -------------------------------------------------------------------------------------------------------------------
    def entry_COVER_NEW(self, instance, value):
        _joe = 12  #
        return
        #global SAVE_AN_UNDO_FILE

        thesum = self.THESUM_box.MYTEXTBOX.text
        numevens = self.NUM_EVENS_box.MYTEXTBOX.text
        musthave = self.MUST_HAVE_INPUT.MYTEXTBOX.text
        #
        if self.INIT_IS_DONE_HANDLER and thesum and numevens:
            #curstatus = SAVE_AN_UNDO_FILE
            #SAVE_AN_UNDO_FILE = True
            self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, musthave=musthave, one_of_these=[])
            self.MEGA_POPULATE_OPTIONS(ok=True)
            #SAVE_AN_UNDO_FILE = curstatus
        return
    # -------------------------------------------------------------------------------------------------------------------


    def SavePuzzle(self, instance=None, filename=""):
        if not filename:
            filename = f"saved_puzzle.txt"
        with open(filename, "w") as file:
            # Odd/even:
            for row in range(4):
                for col in range(4):
                    file.write(f"{self.Buttons_ODD_EVEN[row][col].MYTEXT}\n")
            # Row sums:
            for xx in range(4):
                val1 = self.ROW_SUMS_int[xx] or 0
                file.write(f"{val1}\n")
            # Col sums:
            for xx in range(4):
                val2 = self.COL_SUMS_int[xx] or 0
                file.write(f"{val2}\n")
            # My solution:
            for row in range(4):
                for col in range(4):
                    file.write(f"{self.MY_SOLUTION_int[row][col]}\n")
            # THE solution:
            if self.THE_ACTUAL_SOLUTION_int[0][0] != 0:
                for row in range(4):
                    solrow = "".join(map(str, self.THE_ACTUAL_SOLUTION_int[row]))
                    file.write(f"{solrow}\n")
        return

    def LoadSavedPuzzle_btn(self, instance=None):
        self.LoadSavedPuzzle_engine(instance=instance)
        return

    @wrap_mega_populate
    def LoadSavedPuzzle_engine(self, instance=None):
        self.INIT_IS_DONE_HANDLER.Set_MEGA_DO_NOT_TURN_IT_ON_on()
        #
        self.LoadSavedPuzzle(instance)
        #
        self.UNDO_HANDLER.turn_undo_saving_on()
        #
        self.INIT_IS_DONE_HANDLER.Set_MEGA_DO_NOT_TURN_IT_ON_off()
        SET_FOCUS(self.ROW_SUMS_boxes[0])
        return

    @wrap_do_not_check_SET_SOLUTION
    def LoadSavedPuzzle(self, instance=None, filename="", from_undo=False):
        global DO_NOT_MEGA_POPULATE_OPTIONS
        #
        self.INIT_IS_DONE_HANDLER.Set_MEGA_DO_NOT_TURN_IT_ON_on()
        if self.INIT_IS_DONE_HANDLER:
            self.CLEAR()
        #
        filename = filename or f"saved_puzzle.txt"
        with open(filename, "r") as file:
            onebigline = file.read()
            all_lines = onebigline.split()
        #
        ct = -1
        # Odd/Even buttons:
        for row in range(4):
            for col in range(4):
                ct += 1
                res2 = all_lines[ct]
                if res2.lower() == "even":
                    self.Buttons_ODD_EVEN[row][col].state = "down"

        # -----------------------------------------------------------------------
        # First, load the data into variables:
        # -----------------------------------------------------------------------
        # Row sums:
        for xx in range(4):
            ct += 1
            res0 = int(all_lines[ct])
            self.ROW_SUMS_int[xx] = res0
        # Col sums:
        for xx in range(4):
            ct += 1
            res1 = int(all_lines[ct])
            self.COL_SUMS_int[xx] = res1
        # My solution so far:
        for row in range(4):
            for col in range(4):
                ct += 1
                res3 = int(all_lines[ct])
                if res3 == 0:
                    continue
                self.MY_SOLUTION_int[row][col] = res3

        del ct, res0, res1, res2, res3, onebigline, file, filename
        # Is the REAL solution provided?
        if len(all_lines) > 40:
            thesol = {}
            thesol[0] = all_lines[40]
            thesol[1] = all_lines[41]
            thesol[2] = all_lines[42]
            thesol[3] = all_lines[43]
            for row in range(4):
                for col in range(4):
                    ts = int(thesol[row][col])
                    self.THE_ACTUAL_SOLUTION_int[row][col] = ts

        # -----------------------------------------------------------------------
        # Now, put the data onto the GUI screen:
        # -----------------------------------------------------------------------
        self.mega_recalculate_cell_options()
        #
        DO_NOT_MEGA_POPULATE_OPTIONS = True
        #
        # Row sums:
        for ct in range(4):
            num = self.ROW_SUMS_int[ct]
            if num == 0:
                num = ""
            widget = self.ROW_SUMS_boxes[ct]
            widget.SET_TEXT(num)  # sets 'INIT_IS_DONE' to true via SET_FOCUS()
        #
        # Col sums:
        for ct in range(4):
            num = self.COL_SUMS_int[ct]
            if num == 0:
                num = ""
            widget = self.COL_SUMS_boxes[ct]
            widget.SET_TEXT(num)  # sets 'INIT_IS_DONE' to true via SET_FOCUS()
        #
        # My solution so far:
        for row in range(4):
            for col in range(4):
                num = self.MY_SOLUTION_int[row][col]
                if num != 0:
                    self.MY_SOLUTION_boxes[row][col].text = str(num)
        #
        #if not from_undo:
        self.RipItGood()  # turns 'INIT_IS_DONE' one
        self.UNDO_HANDLER.Save_Undo_Level()
        #
        self.INIT_IS_DONE_HANDLER.Set_MEGA_DO_NOT_TURN_IT_ON_off()
        self.INIT_IS_DONE_HANDLER.Turn_INIT_IS_DONE_on()
        DO_NOT_MEGA_POPULATE_OPTIONS = False
        return


    def ChoosePuzzle(self, instance=None):
        tt = APP_MainApp()
        tt.title = "Choose a puzzle!"
        tt.run()
        return

    def LoadPuzzle(self, instance=None):
        global DO_NOT_MEGA_POPULATE_OPTIONS

        cur_dnmp_status = DO_NOT_MEGA_POPULATE_OPTIONS
        DO_NOT_MEGA_POPULATE_OPTIONS = True

        #global INIT_IS_DONE  # need this
        if self.INIT_IS_DONE_HANDLER:
            # No need to clear if this is the first time through
            self.CLEAR(instance)
        #
        PUZZLES = {}
        PUZZLES[0] = {"rowsum": [(0, 12), (1, 17), (2, 21), (3, 20)],
                      "colsum": [(0, 10), (1, 22), (2, 10), (3, 28)],
                      "oddevens": [(0,2), (0,3), (1,0), (2,0), (2,1), (2,3), (3,1), (3,2)],
                      "solutions": []  #(0, 2, 2), (1, 0, 2), (1, 2, 1), (2, 0, 4), (2, 2, 3), (2, 3, 8), (3, 2, 4)]
                      }
        PUZZLES[1] = {"rowsum": [(0, 30), (1, 25), (2, 13), (3, 29)],
                      "colsum": [(0, 26), (1, 20), (2, 28), (3, 23)],
                      "oddevens": [(0,0), (0,3), (1,0), (1,1), (1,2), (2,2), (3,1)],
                      "solutions": [(1, 2, 8), (2, 2, 4), (3, 1, 8), (0, 0, 8), (0, 3, 6)]
                      }
        PUZZLES[2] = {"rowsum": [(0, 27), (1, 13), (2, 13), (3, 25)],
                      "colsum": [(0, 16), (1, 14), (2, 25), (3, 23)],
                      "oddevens": [(0,3), (1,1), (2,3), (3,1), (3,2), (3,3)],
                      "solutions": [(3, 0, 7), (0, 2, 9)]
                      }
        #
        apuzzle = PUZZLES[0]
        #
        for cell in apuzzle["oddevens"]:
            row, col = cell
            self.Buttons_ODD_EVEN[row][col].state = "down"
        #
        for arr in apuzzle["rowsum"]:
            row, val = arr
            self.ROW_SUMS_boxes[row].SET_TEXT(val)
        #
        for arr in apuzzle["colsum"]:
            col, val = arr
            self.COL_SUMS_boxes[col].SET_TEXT(val)
        #
        for row, col, num in apuzzle["solutions"]:
            self.MY_SOLUTION_boxes[row][col].SET_TEXT(num)
        #
        #self.RipItGood()
        #
        self.INIT_IS_DONE_HANDLER.Turn_INIT_IS_DONE_on()
        # SET_FOCUS(main_layout.THESUM_box)  # works, 'myLabel_and_Text'
        SET_FOCUS(self.THESUM_box)  # .MYTEXTBOX)
        DO_NOT_MEGA_POPULATE_OPTIONS = cur_dnmp_status
        return

    def post_check_solution_number_truly_worked(self, p_row, p_col, p_num):
        # 1) if any row or col has two cells, with only one option left each, and they're both the same #,
        #    then something went wrong
        for row in range(4):
            tmp = {}
            rowopts = self.CELL_OPTIONS_int[row]
            # singletons = [xx[0] for xx in rowopts if len(xx)==1]
            for arr in rowopts:
                if len(arr) == 1:
                    num = arr[0]
                    tmp[num] = tmp.get(num, 0) + 1
            for key, val in tmp.items():
                if val != 1:
                    msg = f"#{p_num} can NOT go into ({p_row}, {p_col}) as it would then leave bad remaining options for row #{row}!"
                    return msg
        for col in range(4):
            tmp = {}
            colopts = [xx[col] for xx in self.CELL_OPTIONS_int]
            for arr in colopts:
                if len(arr) == 1:
                    num = arr[0]
                    tmp[num] = tmp.get(num, 0) + 1
            for key, val in tmp.items():
                if val != 1:
                    msg = f"#{p_num} can NOT go into ({p_row}, {p_col}) as it would then leave bad remaining options for col #{col}!"
                    return msg
        return



    def pre_check_solution_number_works(self, row, col, num):
        # 1) Check if this num already exists in this row or col
        if self.INIT_IS_DONE_HANDLER and num != 0:
            co = self.CELL_OPTIONS_int[row][col]
            if num in self.MY_SOLUTION_int[row]:
                if len(co) == 1:
                    _joe = 12  # 'num' is the last option left for this cell, yet it was already placed as an option!
                msg = f"#{num} is already in ROW #{row}, you can't also put it in cell ({row}, {col})!"
                return msg
            if num in [xx[col] for xx in self.MY_SOLUTION_int]:
                if len(co) == 1:
                    _joe = 12  # 'num' is the last option left for this cell!!!!
                msg = f"#{num} is already in COL #{col}, you can't also put it in cell ({row}, {col})!"
                return msg  # what if 'num' is the last option left for this cell?

        # 2) Check if placing this number would complete a row/col, and then <> that row/col stated total:
        my_sols_copy = deepcopy(self.MY_SOLUTION_int)
        my_sols_copy[row][col] = num
        #
        rowsum = sum([xx for xx in my_sols_copy[row] if xx != 0])
        if len([True for xx in my_sols_copy[row] if xx != 0]) == 4:
            #mysum = sum([xx for xx in my_sols_copy[row] if xx != 0])
            truerowsum = self.ROW_SUMS_int[row]
            if rowsum != truerowsum:
                return False
        #
        colsum = sum([xx[col] for xx in my_sols_copy if xx[col] != 0])
        if len([True for xx in my_sols_copy if xx[col] != 0]) == 4:
            #mysum = sum([xx[col] for xx in my_sols_copy if xx[col] != 0])
            truecolsum = self.COL_SUMS_int[col]
            if colsum != truecolsum:
                return False
        return True

    def strip_num_from_options(self, p_row, p_col, num):
        self.CELL_OPTIONS_int[p_row][p_col] = []
        # As this was just placed as a solution, it can't go elsewhere in this row or column
        for row in range(4):
            current_options = self.CELL_OPTIONS_int[row][p_col]
            if num in current_options:
                current_options.remove(num)
                self.CELL_OPTIONS_int[row][p_col] = current_options
        for col in range(4):
            current_options = self.CELL_OPTIONS_int[p_row][col]
            if num in current_options:
                current_options.remove(num)
                self.CELL_OPTIONS_int[p_row][col] = current_options
        return


    def SET_SOLUTION(self, row, col, num):
        global DO_NOT_CHECK_SOLUTION
        if DO_NOT_CHECK_SOLUTION is True:
            return
        #
        num = int(num)
        if self.INIT_IS_DONE_HANDLER:
            if self.MY_SOLUTION_int[row][col] == num:
                return False  # It is already there
            if num not in [0] + self.CELL_OPTIONS_int[row][col]:
                _msg = f"{num} IS ALREADY IN ROW #{row}, {col})!"
                myjoe()  # 2023-06-06  Todo: Create/post some explanatory text here?
        # -----------------------------------------------------------------------
        res = self.pre_check_solution_number_works(row, col, num)
        if not res is True:
            myjoe()  # todo: 'res' should be explanatory text?
            self.EXPLANATION.text = res  # f"{num} IS ALREADY IN ROW #{row}, {col})!"
            return
        # -----------------------------------------------------------------------
        self.MY_SOLUTION_int[row][col] = num
        self.strip_num_from_options(row, col, num)
        if num == 0:
            self.MY_SOLUTION_boxes[row][col].text = ""
        else:
            self.MY_SOLUTION_boxes[row][col].text = str(num)  # This recurses back to 'SET_SOLUTION'
        self.CELL_OPTIONS_boxes[row][col].SET_TEXT()
        #
        EVERY_SOLUTION_CELL_IS_FILLED_IN = all([yy != 0 for xx in self.MY_SOLUTION_int for yy in xx])
        if EVERY_SOLUTION_CELL_IS_FILLED_IN:
            self.EXPLANATION.CLEAR()
            for row in range(4):
                for col in range(4):  # Why is this handled here?
                    SET_FOCUS(self.MY_SOLUTION_boxes[row][col], False)
                    self.MY_SOLUTION_boxes[row][col].SET_RED()
        #
        if self.EXPLANATION.MY_DATA.get((row, col), None) == num:
            # remove it, reset box
            self.EXPLANATION.MY_DATA.pop((row, col), None)
            self.EXPLANATION.SET_TEXT()
        #self.ROW_SUMS_boxes[row].focus = True  # cause recalc
        #self.COL_SUMS_boxes[col].focus = True  # cause recalc
        #
        #self.RipItGood()
        #
        res = self.post_check_solution_number_truly_worked(row, col, num)
        if res:
            self.EXPLANATION.SET_ERROR(res)
            return
        #
        return True

    def RipItGood_btn(self, instance=None):
        global RIP_IT_GOOD_CT
        RIP_IT_GOOD_CT = 0
        self.RipItGood(instance)
        return

    def RipItGood(self, instance=None):
        global RIP_IT_GOOD_CT
        RIP_IT_GOOD_CT += 1
        if RIP_IT_GOOD_CT > 1:
            _joe = 12  #
        self.RipItGood_engine(instance=None)
        return


    @wrap_mega_populate
    def RipItGood_engine(self, instance=None):
        self.reset_top_boxes(colors_only=False)
        for row in range(4):
            SET_FOCUS(self.ROW_SUMS_boxes[row])     # this does checking and work
            self.ROW_SUMS_boxes[row].focus = False  # this doesn't
        for col in range(4):
            SET_FOCUS(self.COL_SUMS_boxes[col])     # this does checking and work
            self.COL_SUMS_boxes[col].focus = False  # this doesn't
        self.MEGA_POPULATE_OPTIONS()
        self.reset_remaining_options_colors(force=True)
        return
# ----- class myInputs - END   --------------------------------------------------------------------------------------


# ----- class AskQuestion - START -----------------------------------------------------------------------------------
class AskQuestion(App):
    """ 1) Do this via a 'Screen Manager':
           https://kivy.org/doc/stable/api-kivy.uix.screenmanager.html?highlight=multiple%20windows
        2) app2 = AskQuestion()
           app2.run()
    """
    def __init__(self):
        super().__init__()

    def build(self):  # AskQuestion
        questionlayout = GridLayout()
        questionlayout.cols = 1
        #questionlayout.add_widget(myLabel_and_Text(app=self, GUI=questionlayout, name="Choose Puzzle", readonly=False))
        questionlayout.add_widget(TextInput(text="hi"))
        return questionlayout
# ----- class AskQuestion - END   -----------------------------------------------------------------------------------



# ----- class APP_MainApp - START ---------------------------------------------------------------------------------------
class APP_MainApp(App):
    def __init__(self):
        super().__init__()

    def build(self):  # APP_MainApp
        delete_undo_files()
        # backup_to_one_drive()
        main_layout = myInputs(which)
        machine = os.environ.get("MACHINE")
        if machine == "PC":
            create_loggers()
        SET_FOCUS(main_layout.THESUM_box)
        return main_layout
# ----- class APP_MainApp - END   ---------------------------------------------------------------------------------------


if __name__ == "__main__":
    which = "TEST"
    if "pydevd" not in sys.modules:
        which = "PRODUCTION"
    #
    app = APP_MainApp()
    app.title = which
    app.run()
