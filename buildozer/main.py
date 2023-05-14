import logging
import sys
import os
import re
from typing import Callable
#
from kivy.app import App
#from kivy.uix.image import Image
#from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
#from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics.instructions import Canvas, CanvasBase
from utils import *


TODAY, HOUR = get_sql_today()
INIT_IS_DONE = False


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
    #KIVY_logger.propagate = False
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



def scrub_text(value, margin=50):
    if value == []:
        return "", ""
    # 'value' can be any type
    ll = 1
    tmp, text = "", ""
    if isinstance(value, int):
        text = str(value)
    elif isinstance(value, list):
        ll = len(value)
        for ct in range(len(value)):
            if tmp:
                tmp += ", "
            tmp += ", ".join(map(str, value[ct:ct+1]))
            _lt = len(tmp)
            if len(tmp) >= margin:
                text += f"{tmp}\n"
                tmp = ""
        text += tmp
    elif isinstance(value, str):
        text = value
    return ll, text


def SET_COLOR(kivy_widget, color):
    """ NORMAL_COLOR    = "white"
        NO_FOCUS_COLOR  = "blanchedalmond"
        HIGHLIGHT_COLOR = "lightpink"
                        = [1.0, 0.7137254901960784, 0.7568627450980392, 1.0]
        MY_RED          = [1, 0, 0, 1]
        MY_WHITE        = [1, 1, 1, 1]
    """
    global INIT_IS_DONE
    #if INIT_IS_DONE:
    if isinstance(kivy_widget, cls_Label_and_TextInput):
        joe = kivy_widget.NAME
        kivy_widget.MYTEXTBOX.background_color = color
        if kivy_widget.NAME == "Unique to all":
            _joe = 12
    else:
            kivy_widget.background_color = color
    return


# ----- class myTextInput - START ----------------------------------------------------------------------------
class myTextInput(TextInput):
    TAB_NUM = -1
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
        self.MYAPP = args[0]
        self.ANAME = args[1]
        #
        self.AROW = kwargs.get("row", None)
        self.ACOL = kwargs.get("col", None)
        self.ANUM = kwargs.get("num", None)
        self.MYCOLOR = kwargs.get("mycolor", None)

        tabstop = False
        readonly = kwargs.get("readonly", False)
        if readonly:
            if kwargs.get("tabstop", False):
                _joe = 12  # How can I set this to readonly AND a tabstop?
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
        size = kwargs.get("size", None)

        if not readonly:  # tabstop:
            num = myTextInput.TAB_NUM
            myTextInput.TAB_NUM = num + 1
            self.TAB_NUM = myTextInput.TAB_NUM
            myTextInput.TAB_ORDER[self.TAB_NUM] = self
        else:
            self.TAB_NUM = None
            if not self.MYCOLOR:
                SET_COLOR(self, NO_FOCUS_COLOR)
            else:
                SET_COLOR(self, self.MYCOLOR)
        #
        return

    def insert_text(self, substring, from_undo=False):  # myTextInput(TextInput):
        if '.' in self.text:
            s = re.sub(self.PATTERN, '', substring)
        else:
            # To allow a period as well:  s = '.'.join(...same as below)
            s = ''.join(re.sub(self.PATTERN, '', s) for s in substring.split('.', 1))
        return super().insert_text(s, from_undo=from_undo)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):  # myTextInput
        TextInput.keyboard_on_key_down(self, window, keycode, text, modifiers)
        if not keycode[1] in [".", "tab"]:
            return
        if keycode[1] == ".":
            self.SET_TEXT()
        elif keycode[1] == "tab":
            if not self.TABSTOP:
                return
            # to make this smarter: https://kivy.org/doc/stable/api-kivy.uix.behaviors.focus.html
            INC = 1
            if "shift" in modifiers:
                INC = -1
            which = self.TAB_NUM
            next = (which + INC) % (myTextInput.TAB_NUM + 1)
            self.TAB_NEXT = next
        return

    def keyboard_on_key_up(self, window, keycode):  # myTextInput
        # Note: After key_up, for tab-shifting, 'on_focus' gets triggered
        if not keycode[1] in ["tab"]:
            return
        if keycode[1] == "tab":
            if not self.TABSTOP:
                return
            self.TAB_ORDER[self.TAB_NEXT].focus = True
        return

    def keyboard_on_textinput(self, window, text):  # myTextInput
        # This gets hit with every key hit in the/a box
        TextInput.keyboard_on_textinput(self, window, text)
        return

    def SET_TEXT(self, value=""):  # myTextInput
        ll, text = scrub_text(value)
        self.text = text
        if isinstance(self, MySolution):
            if text == "":
                text = 0
            self.MYAPP.Int_MY_SOLUTION[self.AROW][self.ACOL] = int(text)
        return
# ----- class myTextInput - END   ----------------------------------------------------------------------------


# ----- class RemainingOptions - START ------------------------------------------------------------------------------
class RemainingOptions(myTextInput):
    def __str__(self):
        res = f"RemainingOptions ({self.AROW}, {self.ACOL})"
        return res

    def __init__(self, *args, **kwargs):
        kwargs["tabstop"] = False
        super().__init__(*args, **kwargs)
        #SET_COLOR(self, )
# ----- class RemainingOptions - END   ------------------------------------------------------------------------------


# ----- class cls_Label_and_TextInput - START ------------------------------------------------------------------------------------
class cls_Label_and_TextInput(TextInput):  # cls_Label_and_TextInput
    """ top_grid = GridLayout()
        top_grid.cols = 2
        top_grid.add_widget(Label(text="Hi there", size_hint_y = None, height=40, size_hint_x = None, width=200))
        top_grid.add_widget(TextInput(text="", size_hint_y=None, height=40, size_hint_x=None, width=200))
        self.add_widget(top_grid)
    """
    NAME = "cls_Label_and_TextInput"

    def __init__(self, app, GUI, name, **kwargs):
        self.MYAPP = app
        self.NAME = name
        textbindfn = kwargs.pop("textbindfn", None)
        readonly = kwargs.pop("size", None)
        super().__init__(**kwargs)

        this_layout = BoxLayout()
        self.MYLABEL = Label(text=name)
        this_layout.add_widget(self.MYLABEL)
        #
        self.MYTEXTBOX = myTextInput(self, f"{name}", readonly=readonly)
        if callable(textbindfn):
            assert not readonly
            self.MYTEXTBOX.bind(text=textbindfn)
        self.MYTEXTBOX.bind(focus=self.on_focus)
        #
        this_layout.add_widget(self.MYTEXTBOX)
        #
        GUI.add_widget(this_layout)
        return

    def __str__(self):
        res = f"cls_Label_and_TextInput ({self.NAME})"
        return res


    def SET_TEXT(self, value=""):  # cls_Label_and_TextInput
        ll, text = scrub_text(value)
        self.MYTEXTBOX.text = text
        if text and ll != 1:
            if self.NAME == "Unique to all":
                xx = len(value.split())
                self.MYLABEL.text = f"{self.NAME} ({xx})"
            else:
                if ll != 1:
                    if self.NAME == "Potential Solutions":
                        self.MYLABEL.text = f"{self.NAME} ({ll})"
                    else:
                        self.MYLABEL.text = f"{self.NAME} ({ll})"
        else:
            self.MYLABEL.text = self.NAME
        return


    def on_focus(self, instance, value, *largs):  # cls_Label_and_TextInput
        if value is False:
            return
        if self.readonly:
            return
        self.MYAPP.reset_top_boxes(colors_only=True)
        self.MYAPP.reset_sum_colors()
        SET_COLOR(instance, HIGHLIGHT_COLOR)
        row = instance.ANUM
        self.MYAPP.hightlight_Remaining_Options()
        return

    def keyboard_on_key_up(self, window, keycode):  # cls_Label_and_TextInput
        # Note: After key_up, for tab-shifting, 'on_focus' gets triggered
        if not keycode[1] in ["tab"]:
            return
        if keycode[1] == "tab":
            if not self.TABSTOP:
                return
            self.TAB_ORDER[self.TAB_NEXT].focus = True
        return

    def keyboard_on_textinput(self, window, text):  # cls_Label_and_TextInput
        # This gets hit with every key hit in the/a box
        TextInput.keyboard_on_textinput(self, window, text)
        return


# ----- class cls_Label_and_TextInput - END   ------------------------------------------------------------------------------------


# ----- class SumRow - START ----------------------------------------------------------------------------------------
class SumRow(myTextInput):
    def __str__(self):
        res = f"SumRow for row #{self.ANUM}"
        return res

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_focus(self, instance, value, *largs):  # SumRow
        if value is False:
            return
            self.MYAPP.reset_top_boxes(colors_only=False)
        self.MYAPP.reset_sum_colors()
        SET_COLOR(instance, HIGHLIGHT_COLOR)
        row = instance.ANUM
        #self.MYAPP.hightlight_Remaining_Options(p_row=row)
        #
        # TODO: Why am I not reading the value directly from the box?
        thesum = self.MYAPP.Int_ROW_SUMS[row]
        if thesum is None:
            return
        if isinstance(thesum, int):
            assert int(instance.text) == thesum
            self.MYAPP.SUM20_INPUT.SET_TEXT(thesum)
        #
        numevens = self.MYAPP.get_numevens(row=row)
        # if isinstance(numevens, int):
        self.MYAPP.NUM_EVENS_INPUT.SET_TEXT(numevens)
        #
        must_have = self.MYAPP.get_must_have(row=row)
        if must_have:
            self.MYAPP.MUST_HAVE_INPUT.SET_TEXT(", ".join(map(str, must_have)))
        else:
            self.MYAPP.MUST_HAVE_INPUT.SET_TEXT()

        self.MYAPP.LastTopBoxes = {"row": row, "col": None, "thesum": thesum, "numevens": numevens, "musthave": must_have}

        # "One of these" is when a cell has its options set, like (1, 3, 5), therefore, any potential
        # option must have at least ONE of those numbers
        one_of_these = self.MYAPP.get_one_of_these(row=row)
        res = self.MYAPP.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=must_have, one_of_these=one_of_these)
        eliminated_sols = res[0]
        pot_sols = res[1]
        self.MYAPP.ELIMINATED_SOLUTIONS.SET_TEXT(eliminated_sols)
        if pot_sols:
            self.MYAPP.find_unique_to_all(pot_sols)
            self.MYAPP.populate_remaining_options(pot_sols, rownum=row)
            self.MYAPP.POTENTIAL_SOLUTIONS.SET_TEXT(pot_sols)
        else:
            _joe = 12  # now what?
        self.MYAPP.hightlight_Remaining_Options(p_row=row)
        return
# ----- class SumRow - END   ----------------------------------------------------------------------------------------

# ----- class SumCol - START ----------------------------------------------------------------------------------------
class SumCol(myTextInput):
    def __str__(self):
        res = f"SumCol for col #{self.ANUM}"
        return res

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_focus(self, instance, value, *largs):  # SumCol
        if value is False:
            return
        self.MYAPP.reset_top_boxes(colors_only=False)
        self.MYAPP.reset_sum_colors()
        SET_COLOR(instance, HIGHLIGHT_COLOR)
        col = instance.ANUM
        #self.MYAPP.hightlight_Remaining_Options(p_col=col)
        # TODO: Why am I not reading the value directly from the box?
        thesum = self.MYAPP.Int_COL_SUMS[col]
        if thesum is None:
            return
        if isinstance(thesum, int):
            assert int(instance.text) == thesum
            self.MYAPP.SUM20_INPUT.SET_TEXT(thesum)
        #
        numevens = self.MYAPP.get_numevens(col=col)
        self.MYAPP.NUM_EVENS_INPUT.SET_TEXT(numevens)
        #
        must_have = self.MYAPP.get_must_have(col=col)
        if must_have:
            self.MYAPP.MUST_HAVE_INPUT.SET_TEXT(", ".join(map(str, must_have)))
        else:
            self.MYAPP.MUST_HAVE_INPUT.SET_TEXT()

        self.MYAPP.LastTopBoxes = {"row": None, "col": col, "thesum": thesum, "numevens": numevens, "musthave": must_have}

        # "One of these" is when a cell has its options set, like (1, 3, 5), therefore, any potential
        # option must have at least ONE of those numbers
        one_of_these = self.MYAPP.get_one_of_these(col=col)
        res = self.MYAPP.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=must_have, one_of_these=one_of_these)
        eliminated_sols = res[0]
        pot_sols = res[1]
        self.MYAPP.ELIMINATED_SOLUTIONS.SET_TEXT(eliminated_sols)
        if pot_sols:
            self.MYAPP.find_unique_to_all(pot_sols)
            self.MYAPP.populate_remaining_options(pot_sols, colnum=col)
            self.MYAPP.POTENTIAL_SOLUTIONS.SET_TEXT(pot_sols)
        else:
            _joe = 12  # now what?
        self.MYAPP.hightlight_Remaining_Options(p_col=col)
        return
# ----- class SumCol - END   ----------------------------------------------------------------------------------------


# ----- class MySolution - START ------------------------------------------------------------------------------------
class MySolution(myTextInput):
    def __str__(self):
        res = f"MySolution({self.AROW}, {self.ACOL})"
        return res

    def __init__(self, *args, **kwargs):
        kwargs["readonly"] = True
        kwargs["mycolor"] = "white"
        kwargs["multiline"] = False
        super().__init__(*args, **kwargs)
        SET_COLOR(self, MY_SOLUTION_COLOR)

    def on_focus(self, instance, value, *largs):  # MySolution
        self.MYAPP.reset_sum_colors()
        self.MYAPP.reset_top_boxes(colors_only=True)
        if value is True:
            SET_COLOR(instance, HIGHLIGHT_COLOR)
        else:
            SET_COLOR(instance, MY_SOLUTION_COLOR)
        return

# ----- class MySolution - END   ------------------------------------------------------------------------------------





# ----- class myButton - START --------------------------------------------------------------------------------------
class myButton(ToggleButton):
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

    def __str__(self):
        res = "myButton"
        if self.MYROW is not None and self.MYCOL is not None:
            res = f"myButton ({self.MYROW}, {self.MYCOL}) {self.MYTEXT}"
        return res

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
            self.MYAPP.Int_NUM_EVENS_BY_ROW[row] = numevens
        for col in range(4):
            numevens = 0
            for row in range(4):
                if self.MYAPP.Buttons_ODD_EVEN[row][col].MYTEXT == "EVEN":
                    numevens += 1
            self.MYAPP.Int_NUM_EVENS_BY_COL[col] = numevens
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
            self.MYAPP.NUM_EVENS_INPUT.SET_TEXT(new_numevens)
            widget = self.MYAPP.MyTextInput_ROW_SUMS[row]
        elif col is not None:
            new_numevens  = self.MYAPP.get_numevens(col=_LastTopBoxes["col"])
            self.MYAPP.NUM_EVENS_INPUT.SET_TEXT(new_numevens)
            widget = self.MYAPP.MyTextInput_COL_SUMS[col]
        else:
            _joe = 12  # Nothing to do?
            #return
        self.MYAPP.MEGA_POPULATE_OPTIONS()
        if widget:
            widget.focus = True
        return

    def SET_TEXT(self, value=""):  # myButton
        ll, text = scrub_text(value)
        self.text = text
        return

# ----- class MyButton - END   --------------------------------------------------------------------------------------


# ----- class LoginScreen - START -----------------------------------------------------------------------------------


class myInputs(GridLayout):
    GUI_CREATED = False
    SUM20_INPUT = None
    NUM_EVENS_INPUT = None
    MUST_HAVE_INPUT = None
    LastTopBoxes = {"row": None, "col": None, "thesum": None, "numevens": None, "musthave": None}
    UNIQUE_TO_ALL = None
    ELIMINATED_SOLUTIONS = None
    POTENTIAL_SOLUTIONS = None
    Int_CELL_OPTIONS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
    Buttons_ODD_EVEN = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
    MyTextInputs_REMAINING_OPTIONS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
    MyTextInputs_MY_SOLUTION_CELLS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
    Int_MY_SOLUTION = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    Int_NUM_EVENS_BY_ROW = [None, None, None, None]
    Int_NUM_EVENS_BY_COL = [None, None, None, None]
    Int_ROW_SUMS = [None, None, None, None]
    Int_COL_SUMS = [None, None, None, None]
    MyTextInput_ROW_SUMS = [None, None, None, None]
    MyTextInput_COL_SUMS = [None, None, None, None]
    DO_NOT_MEGA_POPULATE = False

    def __init__(self, which, **kwargs):
        self.RESET_VARIABLES()
        #
        self.which = which
        #myVariables.__init__(self)
        GridLayout.__init__(self, **kwargs)
        self.cols = 1
        # self.row_force_default = True
        # self.row_default_height = 40
        # self.col_force_default = True
        # self.col_default_width = 400
        #
        self.CREATE_THE_GUI()
        #
        return

    def __str__(self):
        return f"myInputs()"  # {self.TAB})"

    def RESET_VARIABLES(self):
        self.LastTopBoxes = {"row": None, "col": None, "thesum": None, "numevens": None, "musthave": None}
        self.Int_CELL_OPTIONS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        self.Int_MY_SOLUTION = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.Int_NUM_EVENS_BY_ROW = [None, None, None, None]
        self.Int_NUM_EVENS_BY_COL = [None, None, None, None]
        self.Int_ROW_SUMS = [None, None, None, None]
        self.Int_COL_SUMS = [None, None, None, None]
        return

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def CREATE_THE_GUI(self):

        _joe = 12

        self.add_widget(self.MAKE_UTIL_BUTTONS(size_hint=(1, .1)))
        #
        self.add_widget(self.MAKE_Sum20_NumEvens_MustHave(size_hint=(1, .2)))
        #
        self.add_widget(self.MAKE_Sol_Section(size_hint=(1, .2)))
        #
        self.add_widget(self.MAKE_Odd_Even_Buttons(size_hint=(1, .3)))
        #
        self.add_widget(self.MAKE_Remaining_Options_and_Solutions(size_hint=(1, .3)))
        #
        self.GUI_CREATED = True
        #
        return

    def MAKE_UTIL_BUTTONS(self, size_hint):
        """ Note: GridLayout(row_force_default=True, row_default_height=100, col_force_default=True, col_default_width=400)
                  This forces the entire GridLayout to have a certain size. So if the buttons don't fit the size,
                  then it leaves a blank, black, space to fill in the rest
        """
        mainlayout = GridLayout(size_hint=size_hint)  # row_force_default=True, row_default_height=100, col_force_default=True, col_default_width=400)
        mainlayout.cols = 5

        mainlayout.add_widget(Button(text="CLEAR", on_press=self.CLEAR))
        #
        mainlayout.add_widget(Button(text="Load Puzzle", on_press=self.LoadPuzzle))
        #
        mainlayout.add_widget(Button(text="Save Puzzle", on_press=self.SavePuzzle))
        #
        mainlayout.add_widget(Button(text="Undo", on_press=self.Undo))
        #
        mainlayout.add_widget(Button(text="Exit", on_press=self.Exit))
        #
        return mainlayout

    def MAKE_Sum20_NumEvens_MustHave(self, size_hint):
        SUM_EV_MUST = GridLayout(size_hint=size_hint)  # row_force_default=True, row_default_height=40, col_force_default=True, col_default_width=400)
        SUM_EV_MUST.cols = 1
        # Accepts input:
        self.SUM20_INPUT     = cls_Label_and_TextInput(app=self, GUI=SUM_EV_MUST, name="Sum", textbindfn=self.entry_THE_SUM)
        self.NUM_EVENS_INPUT = cls_Label_and_TextInput(app=self, GUI=SUM_EV_MUST, name="# Evens", textbindfn=self.entry_NUM_EVENS)
        self.MUST_HAVE_INPUT = cls_Label_and_TextInput(app=self, GUI=SUM_EV_MUST, name="Must have", textbindfn=self.entry_MUST_HAVE)
        return SUM_EV_MUST

    def MAKE_Sol_Section(self, size_hint):
        TOP_SECTION = GridLayout(size_hint=size_hint)  # row_force_default=True, row_default_height=40, col_force_default=True, col_default_width=400)
        TOP_SECTION.cols = 1
        # Readonly:
        self.UNIQUE_TO_ALL        = cls_Label_and_TextInput(app=self, GUI=TOP_SECTION, name="Unique to all", readonly=True)
        self.POTENTIAL_SOLUTIONS  = cls_Label_and_TextInput(app=self, GUI=TOP_SECTION, name="Potential Solutions", readonly=True, multiline=False)
        self.ELIMINATED_SOLUTIONS = cls_Label_and_TextInput(app=self, GUI=TOP_SECTION, name="Eliminated Solutions", readonly=True, multiline=True)
        return TOP_SECTION

    def MAKE_Odd_Even_Buttons(self, size_hint):
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
                acell = myButton(self, text='odd', group=f"oe{row}{col}", row=row, col=col, font_size=12)         # odd/even
                self.Buttons_ODD_EVEN[row][col] = acell
                arow_middle.add_widget(acell)
            AROW.add_widget(arow_middle)

            # RIGHT:  R SUM
            arow_right_r_sum = BoxLayout()
            #
            arow_right1_txt = SumRow(self, "rowsum", num=row)
            arow_right1_txt.bind(text=self.entry_TEXT)  # entry_R_SUM)                                  # 'r sum'
            arow_right1_txt.bind(focus=arow_right1_txt.on_focus)
            arow_right_r_sum.add_widget(arow_right1_txt)
            AROW.add_widget(arow_right_r_sum)
            self.MyTextInput_ROW_SUMS[row] = arow_right1_txt
            #
            # add the row to the main GUI:
            CELLS.add_widget(AROW)
        #                                                                                                 'col sums'
        # CELLS.add_widget(self.MAKE_C_Sums_Row())
        #
        # THE C SUMS ROW
        left = .125
        middle = .647
        right = 1 - left - middle
        BOTTOM_ROW = BoxLayout()
        #
        # LEFT SIDE:
        bottom_middle = BoxLayout()
        for col in range(4):
            txt = SumCol(self, "colsum", num=col)  # , size_hint=(.8, 1))
            txt.bind(text=self.entry_TEXT)  # entry_C_SUM)
            txt.bind(focus=txt.on_focus)
            bottom_middle.add_widget(txt)
            self.MyTextInput_COL_SUMS[col] = txt
        BOTTOM_ROW.add_widget(bottom_middle)

        # RIGHT SIDE (just a blank)
        bottom_right = Label(text="")
        BOTTOM_ROW.add_widget(bottom_right)

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
                box = RemainingOptions(self, "REMAINING_OPTIONS", row=row, col=col, mycolor="white", multiline=False, readonly=True, is_focusable=False)
                self.MyTextInputs_REMAINING_OPTIONS[row][col] = box
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
                box = MySolution(self, "MY_SOLUTION", row=row, col=col)  # , mycolor="white", multiline=False)
                self.MyTextInputs_MY_SOLUTION_CELLS[row][col] = box
                box.bind(text=self.entry_A_SOLUTION)
                box.bind(focus=box.on_focus)
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
            res = [xx for xx in self.Int_MY_SOLUTION[row] if xx != 0]
        else:
            res = [xx[col] for xx in self.Int_MY_SOLUTION if xx[col] != 0]
        return res


    def entry_TEXT(self, instance, value):
        #thesum = -9
        if value:
            thesum = int(value)
        if thesum < 10:
            return
        if isinstance(instance, SumRow):
            therow = instance.ANUM
            self.Int_ROW_SUMS[therow] = int(value)
            numevens = self.get_numevens(row=therow)
            musthave = self.get_must_have(row=therow)
            res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
            eliminated_sols = res[0]
            pot_sols = res[1]
            self.ELIMINATED_SOLUTIONS.SET_TEXT(eliminated_sols)
            if pot_sols:
                self.populate_remaining_options(pot_sols, rownum=therow)
                self.find_unique_to_all(pot_sols)
            else:
                _joe = 12  # now what?
        elif isinstance(instance, SumCol):
            thecol = instance.ANUM
            self.Int_COL_SUMS[thecol] = int(value)
        else:
            _joe = 12  # What am I?
        self.MEGA_POPULATE_OPTIONS()
        return

    def SET_TEXT(self, widget, text: str):  # myInputs
        if isinstance(widget, (SumRow, SumCol, cls_Label_and_TextInput)):
            _joe = 12  # get this right son
            widget = widget.MYTEXTBOX
        if not isinstance(widget, myButton):
            if widget.ANAME == "Potential Solutions":
                _joe = 12
        if not isinstance(text, str):
            _joe = 12  # Could be a list like "[[6, 7, 8, 9]]
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
        for cell in self.MyTextInput_ROW_SUMS:
            SET_COLOR(cell, NORMAL_COLOR)
        for cell in self.MyTextInput_COL_SUMS:
            SET_COLOR(cell, NORMAL_COLOR)
        return

    def hightlight_Remaining_Options(self, p_row=None, p_col=None):
        #assert p_row is not None or p_col is not None
        # Reset all the colors:
        _joe = 12
        for row in range(4):
            for col in range(4):
                cell = self.MyTextInputs_REMAINING_OPTIONS[row][col]
                cur_color = cell.background_color
                if cur_color != MY_RED:
                    SET_COLOR(cell, REMAINING_OPTIONS_COLOR)
                else:
                    # What should I be?
                    _joe = 12
        # Now highlight:
        if p_row is not None:
            for cell in self.MyTextInputs_REMAINING_OPTIONS[p_row]:
                cur_color = cell.background_color
                if cur_color != MY_RED:
                    SET_COLOR(cell, HIGHLIGHT_COLOR)
                    _joe = cell.background_color
                else:
                    # What should I be?
                    _joe = 12
        elif p_col is not None:
            for row in self.MyTextInputs_REMAINING_OPTIONS:
                cell = row[p_col]
                cur_color = cell.background_color
                if cur_color != MY_RED:
                    SET_COLOR(cell, HIGHLIGHT_COLOR)
                    _joe = cell.background_color
                else:
                    # What should I be?
                    _joe = 12
        return

    def get_one_of_these(self, row=None, col=None):
        assert not (row is None and col is None)
        if row is not None:
            res = [xx for xx in self.Int_CELL_OPTIONS[row] if xx]
        else:
            res = [xx[col] for xx in self.Int_CELL_OPTIONS if xx[col]]
        #res = list(set(flatten_list(res)))
        return res  # .sort()


    def on_focus(self, instance, value, *largs):  # myInputs
        self.reset_sum_colors()
        # Why types am I here?  MySolution
        self.reset_top_boxes(colors_only=True)
        if value is True:
            SET_COLOR(instance, HIGHLIGHT_COLOR)
        return


    def CLEAR(self, instance):
        self.DO_NOT_MEGA_POPULATE = True
        self.RESET_VARIABLES()
        #
        self.reset_top_boxes(colors_only=False)
        #self.Int_MY_SOLUTION = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        for row in range(4):
            self.MyTextInput_ROW_SUMS[row].SET_TEXT()
            for col in range(4):
                self.MyTextInput_COL_SUMS[row].SET_TEXT()
                self.Buttons_ODD_EVEN[row][col].state = "normal"
                self.MyTextInputs_REMAINING_OPTIONS[row][col].SET_TEXT()
                self.MyTextInputs_MY_SOLUTION_CELLS[row][col].SET_TEXT()
                self.MyTextInputs_REMAINING_OPTIONS[row][col].background_color = REMAINING_OPTIONS_COLOR
        self.DO_NOT_MEGA_POPULATE = False
        self.SUM20_INPUT.MYTEXTBOX.focus = True
        return


    def Undo(self, instance):
        _joe = 12  # now what?

    def Exit(self, instance):
        sys.exit(0)



    def entry_R_POT_SOLS(self, instance, value):
        thesum = int(value)
        if thesum < 10:
            return
        therow = instance.ANUM
        self.Int_ROW_SUMS[therow] = int(value)
        numevens = sum([1 for xx in self.Buttons_ODD_EVEN[instance.ANUM] if xx.MYTEXT == "EVEN"])
        musthave = self.get_must_have(row=therow)
        res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave)
        eliminated_sols = res[0]
        pot_sols = res[1]
        self.ELIMINATED_SOLUTIONS.SET_TEXT(eliminated_sols)
        if pot_sols:
            self.populate_remaining_options(pot_sols, rownum=therow)
            self.find_unique_to_all(pot_sols)
        else:
            _joe = 12  # now what?
        self.MEGA_POPULATE_OPTIONS()
        return


    def reset_top_boxes(self, colors_only):
        SET_COLOR(self.SUM20_INPUT.MYTEXTBOX, NORMAL_COLOR)
        SET_COLOR(self.NUM_EVENS_INPUT.MYTEXTBOX, NORMAL_COLOR)
        SET_COLOR(self.MUST_HAVE_INPUT.MYTEXTBOX, NORMAL_COLOR)
        if colors_only:
            return
        self.SUM20_INPUT.SET_TEXT()
        self.NUM_EVENS_INPUT.SET_TEXT()
        self.MUST_HAVE_INPUT.SET_TEXT()
        self.UNIQUE_TO_ALL.SET_TEXT()
        self.ELIMINATED_SOLUTIONS.SET_TEXT()
        self.POTENTIAL_SOLUTIONS.SET_TEXT()
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
        for row in range(4):
            thesum = self.Int_ROW_SUMS[row]
            if not thesum: continue
            numevens = self.get_numevens(row=row)
            must_have = self.get_must_have(row=row)
            #
            res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=must_have, one_of_these=[])
            eliminated_sols = res[0]
            pot_sols = res[1]
            self.ELIMINATED_SOLUTIONS.SET_TEXT(eliminated_sols)
            if pot_sols:
                self.populate_remaining_options(pot_sols, rownum=row, ok=ok)
        #
        for col in range(4):
            thesum = self.Int_COL_SUMS[col]
            if not thesum: continue
            numevens = self.get_numevens(col=col)
            must_have = self.get_must_have(col=col)
            #
            res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=must_have, one_of_these=[])
            eliminated_sols = res[0]
            pot_sols = res[1]
            self.ELIMINATED_SOLUTIONS.SET_TEXT(eliminated_sols)
            if pot_sols:
                self.populate_remaining_options(pot_sols, colnum=col, ok=ok)
        #
        # See if there is a cell with only one option left:
        for row in range(4):
            for col in range(4):
                if self.Int_MY_SOLUTION[row][col] != 0:
                    SET_COLOR(self.MyTextInputs_REMAINING_OPTIONS[row][col], NORMAL_COLOR)
                else:
                    cell = self.Int_CELL_OPTIONS[row][col]
                    if self.Int_CELL_OPTIONS[row][col]:
                        if len(self.Int_CELL_OPTIONS[row][col]) == 1:
                            SET_COLOR(self.MyTextInputs_REMAINING_OPTIONS[row][col], MY_RED)  #  "red"
                        elif len(self.Int_CELL_OPTIONS[row][col]) == 0:
                            SET_COLOR(self.MyTextInputs_REMAINING_OPTIONS[row][col], NORMAL_COLOR)
        return


    @static_vars(ct=0)
    def find_unique_to_all(self, pot_sols, ok=False):
        global INIT_IS_DONE
        if not ok:
            _joe = 12
        self.find_unique_to_all.__func__.ct = self.find_unique_to_all.ct + 1
        #
        ll = len(pot_sols)
        if ll == 1:
            # there is only one solution left, so every number is 'unique' to all
            res = pot_sols[0]
        else:
            adict = {}
            for arr in pot_sols:
                for num1 in arr:
                    adict[num1] = adict.get(num1, 0) + 1
            res = []
            for num2, ct in adict.items():
                if ct == ll:
                    res.append(num2)  # found one!
        if res:
            unique_str = ", ".join([str(xx) for xx in res])
            self.UNIQUE_TO_ALL.SET_TEXT(unique_str)
            if len(res) == 1:
                SET_COLOR(self.UNIQUE_TO_ALL, MY_RED)
            else:
                SET_COLOR(self.UNIQUE_TO_ALL, NO_FOCUS_COLOR)
        else:
            self.UNIQUE_TO_ALL.SET_TEXT()
            SET_COLOR(self.UNIQUE_TO_ALL, NO_FOCUS_COLOR)
        return res


    def populate_remaining_options(self, pot_sols, rownum=None, colnum=None, ok=False):
        global INIT_IS_DONE
        # -----------------------------------------------------------------------
        def net_out(row, col, these_options):
            cur_opts = self.Int_CELL_OPTIONS[row][col]
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
        # -----------------------------------------------------------------------
        assert rownum is not None or colnum is not None
        unique_to_all = self.find_unique_to_all(pot_sols, ok=ok)
        unique_str = ""
        if unique_to_all:
            unique_str = ", ".join([str(xx) for xx in unique_to_all])
        self.UNIQUE_TO_ALL.SET_TEXT(unique_str)
        flat_pot_sols = list(set(flatten_list(pot_sols)))
        if not rownum is None:
            the_cells = self.MyTextInputs_REMAINING_OPTIONS
            the_row = the_cells[rownum]
            odd_evens = self.Buttons_ODD_EVEN[rownum]
            for col in range(4):
                sol = self.Int_MY_SOLUTION[rownum][col]
                if sol and sol in flat_pot_sols:
                    flat_pot_sols.remove(sol)
            even_pot_sols = [xx for xx in flat_pot_sols if xx in [2, 4, 6, 8]]
            even_pot_sols.sort()
            odd_pot_sols = [xx for xx in flat_pot_sols if xx not in [2, 4, 6, 8]]
            odd_pot_sols.sort()
            for col, cell in enumerate(the_row):
                if self.Int_MY_SOLUTION[rownum][col] != 0:
                    # A solved cell has no remaining options
                    self.SET_TEXT(cell, "")
                    continue
                if odd_evens[col].MYTEXT == "EVEN":
                    kk, kkstr = net_out(rownum, col, even_pot_sols)
                    self.Int_CELL_OPTIONS[rownum][col] = kk
                    self.SET_TEXT(cell, kkstr)
                else:
                    kk, kkstr = net_out(rownum, col, odd_pot_sols)
                    self.Int_CELL_OPTIONS[rownum][col] = kk
                    self.SET_TEXT(cell, kkstr)
                if INIT_IS_DONE and len(unique_to_all) != 1:
                    for uu in unique_to_all:
                        if sum([1 for xx in self.Int_CELL_OPTIONS[rownum] if uu in xx]) == 1:
                            for ct in range(4):
                                if uu in self.Int_CELL_OPTIONS[rownum][ct]:
                                    # TODO: Must remove other red cells I made like this
                                    SET_COLOR(self.MyTextInputs_REMAINING_OPTIONS[rownum][ct], MY_RED)
                                    SET_COLOR(self.MyTextInputs_MY_SOLUTION_CELLS[rownum][ct], MY_RED)
                if len(unique_to_all) == 1 and unique_to_all[0] in kk:
                    SET_COLOR(cell, MY_RED)
                    SET_COLOR(self.UNIQUE_TO_ALL, MY_RED)
                else:
                    # Number is probably a solution already
                    SET_COLOR(cell, REMAINING_OPTIONS_COLOR)
                    SET_COLOR(self.UNIQUE_TO_ALL, NO_FOCUS_COLOR)
        else:
            for row in range(4):
                sol = self.Int_MY_SOLUTION[row][colnum]
                if sol and sol in flat_pot_sols:
                    flat_pot_sols.remove(sol)
            even_pot_sols = [xx for xx in flat_pot_sols if xx in [2, 4, 6, 8]]
            even_pot_sols.sort()
            odd_pot_sols = [xx for xx in flat_pot_sols if xx not in [2, 4, 6, 8]]
            odd_pot_sols.sort()
            for row in range(4):
                if self.Int_MY_SOLUTION[row][colnum] != 0:
                    # A solved cell has no remaining options
                    self.MyTextInputs_REMAINING_OPTIONS[row][colnum].SET_TEXT()
                    continue
                if self.Buttons_ODD_EVEN[row][colnum].MYTEXT == "EVEN":
                    kk, kkstr = net_out(row, colnum, even_pot_sols)
                    self.Int_CELL_OPTIONS[row][colnum] = kk
                    self.MyTextInputs_REMAINING_OPTIONS[row][colnum].SET_TEXT(kkstr)
                else:
                    kk, kkstr = net_out(row, colnum, odd_pot_sols)
                    self.Int_CELL_OPTIONS[row][colnum] = kk
                    self.MyTextInputs_REMAINING_OPTIONS[row][colnum].SET_TEXT(kkstr)
                if INIT_IS_DONE and len(unique_to_all) != 1 and colnum==3:
                    for uu in unique_to_all:
                        if sum([1 for xx in [xx[colnum] for xx in self.Int_CELL_OPTIONS] if uu in xx]) == 1:
                            for ct in range(4):
                                if uu in self.Int_CELL_OPTIONS[ct][colnum]:
                                    # TODO: Must remove other red cells I made like this
                                    SET_COLOR(self.MyTextInputs_REMAINING_OPTIONS[ct][colnum], MY_RED)
                                    SET_COLOR(self.MyTextInputs_MY_SOLUTION_CELLS[ct][colnum], MY_RED)
                if len(unique_to_all) == 1 and unique_to_all[0] in kk:
                    SET_COLOR(self.MyTextInputs_REMAINING_OPTIONS[row][colnum], MY_RED)
                    SET_COLOR(self.UNIQUE_TO_ALL, MY_RED)
                else:
                    # Number is probably a solution already
                    SET_COLOR(self.MyTextInputs_REMAINING_OPTIONS[row][colnum], REMAINING_OPTIONS_COLOR)
                    SET_COLOR(self.UNIQUE_TO_ALL, NO_FOCUS_COLOR)
        return



    def entry_A_SOLUTION(self, instance, value):
        # when I enter something into a solution, it then acts as a 'must have' for that row and col
        if value == "":
            sol = 0
        else:
            sol = int(value)
        row = instance.AROW
        col = instance.ACOL
        self.Int_MY_SOLUTION[row][col] = sol
        global INIT_IS_DONE
        if INIT_IS_DONE and self.DO_NOT_MEGA_POPULATE is False:
            self.MEGA_POPULATE_OPTIONS(ok=True)
        return



    def populate_potential_solutions_box(self, *, thesum, numevens, must_have, one_of_these):
        """ """
        all_sols, good_sols, eliminated_sols = [], [], []

        # if thesum == "" or numevens == "" or thesum is None or numevens is None or thesum == "None" or numevens == "None":
        if not (thesum == 0 or numevens == 0):
            if not thesum or not numevens:
                return eliminated_sols, good_sols

        thesum = int(thesum)
        if thesum < 10:
            return eliminated_sols, good_sols

        if isinstance(must_have, str):
            must_have = list(map(int, must_have.replace(",", "").split()))
        numevens = int(numevens)
        self.POTENTIAL_SOLUTIONS.SET_TEXT()

        if not (thesum in ALL_POTENTIAL_SOLUTIONS and numevens in ALL_POTENTIAL_SOLUTIONS[thesum]):
            return eliminated_sols, good_sols

        all_sols = ALL_POTENTIAL_SOLUTIONS[thesum][numevens]
        pot_sols = all_sols.copy()
        if not must_have and not one_of_these:
            self.POTENTIAL_SOLUTIONS.SET_TEXT(pot_sols)
            return eliminated_sols, pot_sols
        #
        tmp_sols = []
        if not must_have:
            tmp_sols = pot_sols
        else:
            for a_sol in pot_sols:
                res = all([yy in a_sol for yy in must_have])
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
        if len(good_sols) == 1:
            _joe = 12
        self.POTENTIAL_SOLUTIONS.SET_TEXT(good_sols)
        #
        eliminated_sols.sort()
        good_sols.sort()
        return eliminated_sols, good_sols


    def entry_THE_SUM(self, instance, value):
        # this is the one at the very top of the GUI
        thesum = value
        numevens = self.NUM_EVENS_INPUT.MYTEXTBOX.text
        musthave = self.MUST_HAVE_INPUT.MYTEXTBOX.text
        if thesum and numevens:
            self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
        return

    def entry_NUM_EVENS(self, instance, value):
        thesum = self.SUM20_INPUT.MYTEXTBOX.text
        numevens = value
        musthave = self.MUST_HAVE_INPUT.MYTEXTBOX.text
        if thesum and numevens:
            self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
        return

    def entry_MUST_HAVE(self, instance, value):
        thesum = self.SUM20_INPUT.MYTEXTBOX.text
        numevens = self.NUM_EVENS_INPUT.MYTEXTBOX.text
        musthave = value
        if thesum and numevens:
            self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
        return


    def SavePuzzle(self, instance=None):
        _joe = 12  # now what?

    def LoadPuzzle(self, instance=None):
        global INIT_IS_DONE

        PUZZLES = {}

        PUZZLES[0] = {"rowsum": [(0, 12), (1, 17), (2, 21), (3, 20)],
                      "colsum": [(0, 10), (1, 22), (2, 10), (3, 28)],
                      "oddevens": [(0,2), (0,3), (1,0), (2,0), (2,1), (2,3), (3,1), (3,2)],
                      "solutions": [(0, 2, 2),
                                    (1, 0, 2), (1, 2, 1),
                                    (2, 0, 4), (2, 2, 3), (2, 3, 8),
                                    (3, 2, 4)]
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

        apuzzle = PUZZLES[0]

        for cell in apuzzle["oddevens"]:
            row, col = cell
            self.Buttons_ODD_EVEN[row][col].state = "down"

        for arr in apuzzle["rowsum"]:
            row, val = arr
            self.MyTextInput_ROW_SUMS[row].SET_TEXT(val)

        for arr in apuzzle["colsum"]:
            col, val = arr
            self.MyTextInput_COL_SUMS[col].SET_TEXT(val)

        # for cell in apuzzle["oddevens"]:
        #     row, col = cell
        #     self.Buttons_ODD_EVEN[row][col].state = "down"

        for row, col, num in apuzzle["solutions"]:
            self.MyTextInputs_MY_SOLUTION_CELLS[row][col].SET_TEXT(num)

        self.reset_top_boxes(colors_only=False)
        self.MEGA_POPULATE_OPTIONS()
        for row in range(4):
            self.MyTextInput_ROW_SUMS[row].focus = True
        for col in range(4):
            self.MyTextInput_COL_SUMS[col].focus = True

        INIT_IS_DONE = True
        return

# ----- class myInputs - END   -----------------------------------------------------------------------------------


# ----- class MainApp - START ---------------------------------------------------------------------------------------
class MainApp(App):
    def __init__(self):
        super().__init__()

    def build(self):
        main_layout = myInputs(which)
        machine = os.environ.get("MACHINE")
        if machine == "PC":
            create_loggers()
            #main_layout.LoadPuzzle()
        main_layout.SUM20_INPUT.MYTEXTBOX.focus = True
        return main_layout
# ----- class MainApp - END   ---------------------------------------------------------------------------------------


if __name__ == "__main__":
    which = "TEST"
    if "pydevd" not in sys.modules:
        which = "PRODUCTION"
    #
    app = MainApp()
    app.title = which
    app.run()
