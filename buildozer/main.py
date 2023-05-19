# Python GUI's With Kivy:
# https://www.youtube.com/playlist?list=PLCC34OHNcOtpz7PJQ7Tv7hqFBP_xDDjqg
# How To Set The Height And Width of Widgets - Python Kivy GUI Tutorial #4:
# https://www.youtube.com/watch?v=AxKksRhcmOA

#import logging
from copy import deepcopy
#import pickle
import sys
#import os
import re
#from typing import Callable
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
#from kivy.graphics.instructions import Canvas, CanvasBase
from utils import *


TODAY, HOUR = get_sql_today()
INIT_IS_DONE = False


def SET_FOCUS(dinge, FLAG:bool=True):
    if isinstance(dinge, cls_Label_and_TextInput):
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
# -------------------------------------------------------------------------------------------------------------------

def SET_RED(widget):
    if isinstance(widget, RemainingOptions):
        row = widget.AROW
        col = widget.ACOL
    if isinstance(widget, cls_Label_and_TextInput):
        if widget.NAME == "Number in all":
            _joe = 12  #
    SET_COLOR(widget, MY_RED, ok=True)
    return

def SET_COLOR(widget, color, ok=False):
    # https://www.w3.org/TR/SVG11/types.html#ColorKeywords
    """ NORMAL_COLOR    = "white"
        NO_FOCUS_COLOR  = "blanchedalmond"
        HIGHLIGHT_COLOR = "lightpink"
                        = [1.0, 0.7137254901960784, 0.7568627450980392, 1.0]
        MY_RED          = [1, 0, 0, 1]
        MY_WHITE        = [1, 1, 1, 1]
    """
    if not isinstance(widget, (cls_Label_and_TextInput, RemainingOptions, MySolution, myTextInput, TextInput, cls_Explanation)):
        _joe = 12  #
    if color in [MY_RED, [1, 0, 0, 1], "red"] and not ok:
        _joe = 12  # use new function SET_RED instead of calling this directly
    if isinstance(widget, cls_Label_and_TextInput):
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

    #def on_focus(self, instance, value, *largs):  # myTextInput
    #    _joe = 12  #

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
        if not readonly:  # tabstop:
            num = myTextInput.TOTAL_NUMBER_OF_TABS
            myTextInput.TOTAL_NUMBER_OF_TABS = num + 1
            self.MY_TAB_NUMBER = myTextInput.TOTAL_NUMBER_OF_TABS
            myTextInput.TAB_ORDER[self.MY_TAB_NUMBER] = self
        else:
            self.MY_TAB_NUMBER = None
            if not self.MYCOLOR:
                SET_COLOR(self, NO_FOCUS_COLOR)
            else:
                SET_COLOR(self, self.MYCOLOR)
        #
        return

    # -------------------------------------------------------------------------------------------------------------------
    def keyboard_on_key_down(self, window, keycode, text, modifiers):  # myTextInput
        global INIT_IS_DONE  # I need this

        # 1)
        TextInput.keyboard_on_key_down(self, window, keycode, text, modifiers)
        if keycode[1] == "tab" and self.TABSTOP:
            INC = 1
            if "shift" in modifiers:  # a 'back tab'
                INC = -1
            next_tab = (self.MY_TAB_NUMBER + INC) % (myTextInput.TOTAL_NUMBER_OF_TABS + 1)
            self.TAB_NEXT = next_tab
            next_widget = self.TAB_ORDER[self.TAB_NEXT]
            INIT_IS_DONE = True  # If I'm tabbing, then this is ok
            SET_FOCUS(self, False)  # "SumRow for row #0" --> RowCol().on_focus()
            SET_FOCUS(next_widget)  # "SumCol for col #0" --> nowhere?
        return
        #
        # if not keycode[1] in [".", "tab"]:
        #     return
        # if keycode[1] == ".":
        #     self.SET_TEXT()
        # elif keycode[1] == "tab":
        #     if not self.TABSTOP:
        #         return
        #     # to make this smarter: https://kivy.org/doc/stable/api-kivy.uix.behaviors.focus.html
        #     # I need to do this bit here because it gets the 'modifiers', like "shift"
        #     INCREMENT = 1
        #     if "shift" in modifiers:
        #         INCREMENT = -1  # a 'back tab'
        #     current_tab = self.MY_TAB_NUMBER
        #     next_tab = (current_tab + INCREMENT) % (myTextInput.TOTAL_NUMBER_OF_TABS + 1)
        #     self.TAB_NEXT = next_tab
        # return

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
        if isinstance(self, MySolution):
            # Check this # is an option for this cell
            if INIT_IS_DONE and int(s) in self.MYAPP.Int_CELL_OPTIONS[self.AROW][self.ACOL]:
                res = super().insert_text(s, from_undo=from_undo)
            else:
                _joe = 12  #
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
        assert not isinstance(self, MySolution)
        return
# ----- class myTextInput - END   ----------------------------------------------------------------------------


# ----- class Explanation - START -----------------------------------------------------------------------------------
class cls_Explanation(TextInput):
    MY_DATA = {}
    def __init__(self):
        super().__init__(readonly=True, multiline=True)


    def SET_TEXT(self, text=""):
        self.text = text
        return


    def SET_EXPLANATION(self, row, col, num):
        if self.MY_DATA.get((row, col), None) == num:
            # Nothing to do
            return
        self.MY_DATA[(row, col)] = num
        self.text = ""
        tmp = ""
        for ct, ((row, col), num) in enumerate(self.MY_DATA.items()):
            reason = f"#{num} must go into cell ({row}, {col})"
            if tmp:
                tmp = f"{tmp}   {reason}"
                self.text = tmp
                tmp = ""
            else:
                tmp = reason
        if tmp:
            self.text = tmp
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


    def on_focus(self, instance, value, *largs):  # RemainingOptions
        if value is False:  # works
            return
        row = instance.AROW
        col = instance.ACOL
        arr = self.MYAPP.Int_CELL_OPTIONS[row][col]
        if len(arr) == 1:
            # There is only one option left for this cell, so place it as a solution:
            num = arr[0]
            res = self.MYAPP.SET_SOLUTION(row, col, num)
            if res:
                instance.SET_TEXT()
                SET_COLOR(instance, REMAINING_OPTIONS_COLOR)
            else:
                _joe = 12  # ???
        else:
            if (row, col) in self.MYAPP.EXPLANATION.MY_DATA:
                # I have something here I can place though
                num = self.MYAPP.EXPLANATION.MY_DATA[(row, col)]
                res = self.MYAPP.SET_SOLUTION(row, col, num)
                if res:
                    instance.SET_TEXT()
                    SET_COLOR(instance, REMAINING_OPTIONS_COLOR)
                else:
                    _joe = 12  # ???
        #instance.focus = True
        SET_FOCUS(instance)
        return
# ----- class RemainingOptions - END   ------------------------------------------------------------------------------


# ----- class cls_Label_and_TextInput - START ------------------------------------------------------------------------------------
class cls_Label_and_TextInput:  # (TextInput):  # cls_Label_and_TextInput
    """ top_grid = GridLayout()
        top_grid.cols = 2
        top_grid.add_widget(Label(text="Hi there", size_hint_y = None, height=40, size_hint_x = None, width=200))
        top_grid.add_widget(TextInput(text="", size_hint_y=None, height=40, size_hint_x=None, width=200))
        self.add_widget(top_grid)
    """
    NAME = "cls_Label_and_TextInput"

    def __init__(self, app, GUI, name, readonly, **kwargs):
        self.MYAPP = app
        self.MYGUI = GUI
        self.NAME = name
        self.READONLY = readonly
        textbindfn = kwargs.pop("textbindfn", None)
        this_layout = BoxLayout()
        #
        # The label:
        self.MYLABEL = Label(text=name)
        this_layout.add_widget(self.MYLABEL)
        #
        # The textbox next to it:
        self.MYTEXTBOX = myTextInput(self, f"{name}", readonly=self.READONLY)
        if callable(textbindfn):
            assert not self.READONLY
            self.MYTEXTBOX.bind(text=textbindfn)  #  cls_Label_and_TextInput
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
        if not self.NAME in ["Number in all", "Remaining Solutions", "Eliminated Solutions"]:
            # I don't change these labels
            return
        if not text:
            self.MYLABEL.text = self.NAME
            return
        #
        if self.NAME == "Number in all":
            xx = len(value.split())
            if xx == 1:
                self.MYLABEL.text = f"Number in all ({xx})"
            else:
                self.MYLABEL.text = f"Numbers in all ({xx})"
        elif self.NAME == "Remaining Solutions":
            self.MYLABEL.text = f"{self.NAME} ({ll})"
        else:  # "Eliminated Solutions":
            # I always want this to give the # of elims
            self.MYLABEL.text = f"{self.NAME} ({ll})"
        #
        return


    def on_focus(self, instance, value, *largs):  # cls_Label_and_TextInput
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

    def keyboard_on_key_up(self, window, keycode):  # cls_Label_and_TextInput
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


    def keyboard_on_textinput(self, window, text):  # cls_Label_and_TextInput
        # This gets hit with every key hit in the/a box
        TextInput.keyboard_on_textinput(self, window, text)
        return
# ----- class cls_Label_and_TextInput - END   ------------------------------------------------------------------------------------


# ----- class RowCol - START ----------------------------------------------------------------------------------------
class RowCol(myTextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_my_sum(self):
        #rowcolnum = instance.ANUM
        if isinstance(self, SumRow):
            sum = self.MYAPP.Int_ROW_SUMS[self.ANUM]
        else:
            sum = self.MYAPP.Int_COL_SUMS[self.ANUM]
        if sum is None:
            return
        if isinstance(sum, int):
            if self.text:
                assert int(self.text) == sum
            else:
                self.MYAPP.SUM20_INPUT.SET_TEXT()
        return sum

    def get_num_evens(self):
        #rowcolnum = instance.ANUM
        if isinstance(self, SumRow):
            num = self.MYAPP.get_numevens(row=self.ANUM)
        else:
            num = self.MYAPP.get_numevens(col=self.ANUM)
        if str(num) != self.MYAPP.NUM_EVENS_INPUT.MYTEXTBOX.text:
            self.MYAPP.NUM_EVENS_INPUT.SET_TEXT(num)
        return num

    def get_must_have(self):
        #rowcolnum = instance.ANUM
        if isinstance(self, SumRow):
            must_have = self.MYAPP.get_must_have(row=self.ANUM)
        else:
            must_have = self.MYAPP.get_must_have(col=self.ANUM)
        if must_have:
            self.MYAPP.MUST_HAVE_INPUT.SET_TEXT(", ".join(map(str, must_have)))
        else:
            self.MYAPP.MUST_HAVE_INPUT.SET_TEXT()
        return must_have


    def set_last_box(self, thesum, numevens, musthave):
        self.MYAPP.LastTopBoxes = {"row": None, "col": None, "thesum": thesum, "numevens": numevens, "musthave": musthave}
        if isinstance(self, SumRow):
            self.MYAPP.LastTopBoxes = {"row": self.ANUM}
        else:
            self.MYAPP.LastTopBoxes = {"col": self.ANUM}
        return

    def get_one_of_these(self):
        if isinstance(self, SumRow):
            one_of_these = self.MYAPP.get_one_of_these(row=self.ANUM)
        else:
            one_of_these = self.MYAPP.get_one_of_these(col=self.ANUM)
        return one_of_these

    def update_GUI(self, pot_sols, thesum, numevens, musthave,one_of_these):
        res = self.MYAPP.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=one_of_these)
        if pot_sols:
            self.MYAPP.POTENTIAL_SOLUTIONS.SET_TEXT(pot_sols)
            if isinstance(self, SumRow):
                self.MYAPP.refresh_remaining_options(pot_sols, rownum=self.ANUM)
                self.MYAPP.hightlight_Remaining_Options(p_row=self.ANUM)
            else:
                self.MYAPP.refresh_remaining_options(pot_sols, colnum=self.ANUM)
                self.MYAPP.hightlight_Remaining_Options(p_col=self.ANUM)
        return


    def on_focus(self, instance, value, *largs):  # RowCol
        #dinge = instance.ANUM
        #rowcolnum = instance.ANUM
        self.MYAPP.reset_top_boxes(colors_only=False)
        #self.MYAPP.reset_sum_colors()
        if value is True:
            SET_COLOR(self, HIGHLIGHT_COLOR)
        else:
            SET_COLOR(self, NORMAL_COLOR)
            return

        thesum = self.get_my_sum()
        if thesum is None:
            return
        numevens = self.get_num_evens()
        musthave = self.get_must_have()
        self.set_last_box(thesum, numevens, musthave)

        one_of_these = self.get_one_of_these()
        #
        res = self.MYAPP.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=one_of_these)
        #
        eliminated_sols = res[0]
        pot_sols = res[1]
        self.MYAPP.ELIMINATED_SOLUTIONS.SET_TEXT(eliminated_sols)
        self.update_GUI(pot_sols, thesum, numevens, musthave,one_of_these)
        return
# ----- class RowCol - END   ----------------------------------------------------------------------------------------


# ----- class SumRow - START ----------------------------------------------------------------------------------------
class SumRow(RowCol):  # myTextInput):
    def __str__(self):
        res = f"SumRow for row #{self.ANUM}"
        return res

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def xx_on_focus(self, instance, value, *largs):  # SumRow
        dinge = instance.ANUM
        if value is False:
            return
        self.MYAPP.reset_top_boxes(colors_only=False)
        self.MYAPP.reset_sum_colors()
        SET_COLOR(instance, HIGHLIGHT_COLOR)

        thesum = self.MYAPP.Int_ROW_SUMS[dinge]
        if thesum is None:
            return
        if isinstance(thesum, int):
            if instance.text:
                assert int(instance.text) == thesum
                # self.MYAPP.SUM20_INPUT.SET_TEXT(thesum)
            else:
                self.MYAPP.SUM20_INPUT.SET_TEXT()
        #
        numevens = self.MYAPP.get_numevens(row=dinge)
        if str(numevens) != self.MYAPP.NUM_EVENS_INPUT.MYTEXTBOX.text:
            self.MYAPP.NUM_EVENS_INPUT.SET_TEXT(numevens)
        #
        must_have = self.MYAPP.get_must_have(row=dinge)
        if must_have:
            self.MYAPP.MUST_HAVE_INPUT.SET_TEXT(", ".join(map(str, must_have)))
        else:
            self.MYAPP.MUST_HAVE_INPUT.SET_TEXT()

        self.MYAPP.LastTopBoxes = {"row": dinge, "col": None, "thesum": thesum, "numevens": numevens, "musthave": must_have}

        # "One of these" is when a cell has its options set, like (1, 3, 5), therefore, any potential
        # option must have at least ONE of those numbers
        one_of_these = self.MYAPP.get_one_of_these(row=dinge)
        res = self.MYAPP.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=must_have, one_of_these=one_of_these)
        eliminated_sols = res[0]
        pot_sols = res[1]
        self.MYAPP.ELIMINATED_SOLUTIONS.SET_TEXT(eliminated_sols)
        if pot_sols:
            #self.MYAPP.find_unique_to_all(pot_sols, instance)
            self.MYAPP.refresh_remaining_options(pot_sols, rownum=dinge)
            self.MYAPP.POTENTIAL_SOLUTIONS.SET_TEXT(pot_sols)
        else:
            _joe = 12  # now what?
        self.MYAPP.hightlight_Remaining_Options(p_row=dinge)  # SumRow
        return
# ----- class SumRow - END   ----------------------------------------------------------------------------------------

# ----- class SumCol - START ----------------------------------------------------------------------------------------
class SumCol(RowCol):
    def __str__(self):
        res = f"SumCol for col #{self.ANUM}"
        return res

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def xx_on_focus(self, instance, value, *largs):  # SumCol
        dinge = instance.ANUM
        if value is False:
            return
        self.MYAPP.reset_top_boxes(colors_only=False)
        self.MYAPP.reset_sum_colors()
        SET_COLOR(instance, HIGHLIGHT_COLOR)

        thesum = self.MYAPP.Int_COL_SUMS[dinge]
        if thesum is None:
            return
        if isinstance(thesum, int):
            if instance.text != "":
                assert int(instance.text) == thesum
            self.MYAPP.SUM20_INPUT.SET_TEXT(thesum)
        #
        numevens = self.MYAPP.get_numevens(col=dinge)
        self.MYAPP.NUM_EVENS_INPUT.SET_TEXT(numevens)
        #
        must_have = self.MYAPP.get_must_have(col=dinge)
        if must_have:
            self.MYAPP.MUST_HAVE_INPUT.SET_TEXT(", ".join(map(str, must_have)))
        else:
            self.MYAPP.MUST_HAVE_INPUT.SET_TEXT()

        self.MYAPP.LastTopBoxes = {"row": None, "col": dinge, "thesum": thesum, "numevens": numevens, "musthave": must_have}

        # "One of these" is when a cell has its options set, like (1, 3, 5), therefore, any potential
        # option must have at least ONE of those numbers
        one_of_these = self.MYAPP.get_one_of_these(col=dinge)
        res = self.MYAPP.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=must_have, one_of_these=one_of_these)
        eliminated_sols = res[0]
        pot_sols = res[1]
        self.MYAPP.ELIMINATED_SOLUTIONS.SET_TEXT(eliminated_sols)
        if pot_sols:
            #self.MYAPP.find_unique_to_all(pot_sols)
            self.MYAPP.refresh_remaining_options(pot_sols, colnum=dinge)
            self.MYAPP.POTENTIAL_SOLUTIONS.SET_TEXT(pot_sols)
        else:
            _joe = 12  # now what?
        self.MYAPP.hightlight_Remaining_Options(p_col=dinge)  # SumCol
        return
# ----- class SumCol - END   ----------------------------------------------------------------------------------------


# ----- class MySolution - START ------------------------------------------------------------------------------------
class MySolution(myTextInput):
    def __str__(self):
        res = f"MySolution({self.AROW}, {self.ACOL})"
        return res

    def __init__(self, *args, **kwargs):
        kwargs["readonly"] = True
        kwargs["mycolor"] = MY_SOLUTION_COLOR
        kwargs["multiline"] = False
        super().__init__(*args, **kwargs)
        SET_COLOR(self, MY_SOLUTION_COLOR)

    def on_focus(self, instance, value, *largs):  # MySolution
        if value is False:
            SET_COLOR(self, MY_SOLUTION_COLOR)
            return
        self.MYAPP.reset_sum_colors()  # works
        self.MYAPP.reset_top_boxes(colors_only=True)
        if value is True:
            SET_COLOR(instance, HIGHLIGHT_COLOR)
        else:
            SET_COLOR(instance, MY_SOLUTION_COLOR)
        #
        if self.MYAPP.Int_MY_SOLUTION[instance.AROW][instance.ACOL] != 0:
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
        if INIT_IS_DONE:
            options = self.MYAPP.Int_CELL_OPTIONS[row][col]
            if num !=0 and num not in options:
                return False  # do not let this bad # go into this cell
        else:
            _joe = 12  #
        ll, text = scrub_text(value)
        #self.text = num
        self.text = text  # this generates a new UNDO file when text!='', and it also helps with creating recursion
        self.MYAPP.SET_SOLUTION(row, col, num)
        self.MYAPP.Int_CELL_OPTIONS[row][col] = []
        if all([yy!=0 for xx in self.MYAPP.Int_MY_SOLUTION for yy in xx]):
            # self.MYAPP.SUM20_INPUT.MYLABEL.text = "I AM DONE!"
            # self.MYAPP.NUM_EVENS_INPUT.MYLABEL.text = "I AM DONE!"
            # self.MYAPP.MUST_HAVE_INPUT.MYLABEL.text = "I AM DONE!"
            # self.MYAPP.NUMBER_IN_ALL.MYLABEL.text = "I AM DONE!"
            # self.MYAPP.POTENTIAL_SOLUTIONS.MYLABEL.text = "I AM DONE!"
            # self.MYAPP.ELIMINATED_SOLUTIONS.MYLABEL.text = "I AM DONE!"
            for row in range(4):
                for col in range(4):
                    SET_FOCUS(self.MYAPP.MyTextInput_MY_SOLUTION_CELLS[row][col], False)
                    SET_RED(self.MYAPP.MyTextInput_MY_SOLUTION_CELLS[row][col])
            # TODO: self.MEGA_POPULATE_OPTIONS(ok=True)???
            SET_FOCUS(self.MYAPP.SUM20_INPUT.MYTEXTBOX)
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
        self.MYAPP.SAVE_AN_UNDO_FILE = True
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
    GUI_CREATED = False
    SUM20_INPUT = None
    NUM_EVENS_INPUT = None
    MUST_HAVE_INPUT = None
    LastTopBoxes = {"row": None, "col": None, "thesum": None, "numevens": None, "musthave": None}
    NUMBER_IN_ALL = None
    ELIMINATED_SOLUTIONS = None
    POTENTIAL_SOLUTIONS = None
    # -------------------------------------------------------------------------------------------------------------------
    Int_CELL_OPTIONS = [[[], [], [], []], [[], [], [], []], [[], [], [], []], [[], [], [], []], ]
    Int_MY_SOLUTION = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    Buttons_ODD_EVEN = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
    BUTTON_UNDO = None
    BUTTON_FORWARD = None
    #
    MyTextInput_REMAINING_OPTIONS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
    MyTextInput_MY_SOLUTION_CELLS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
    #
    Int_NUM_EVENS_BY_ROW = [None, None, None, None]
    Int_NUM_EVENS_BY_COL = [None, None, None, None]
    Int_ROW_SUMS = [None, None, None, None]
    Int_COL_SUMS = [None, None, None, None]
    MyTextInput_ROW_SUMS = [None, None, None, None]
    MyTextInput_COL_SUMS = [None, None, None, None]

    LAST_UNDO_FILE_NUM = 0
    GREATEST_UNDO_FILE_NUM = 0
    SAVE_AN_UNDO_FILE = False
    DO_NOT_MEGA_POPULATE = False
    EXPLANATION = None

    def __init__(self, which, **kwargs):
        self.which = which
        GridLayout.__init__(self, **kwargs)
        self.cols = 1
        self.CREATE_THE_GUI()
        return

    def __str__(self):
        return f"myInputs()"  # {self.TAB})"

    def RESET_VARIABLES(self):
        if not INIT_IS_DONE:
            return  # there is nothing to reset
        self.SUM20_INPUT.SET_TEXT()
        self.NUM_EVENS_INPUT.SET_TEXT()
        self.MUST_HAVE_INPUT.SET_TEXT()
        self.NUMBER_IN_ALL.SET_TEXT()
        self.POTENTIAL_SOLUTIONS.SET_TEXT()
        self.ELIMINATED_SOLUTIONS.SET_TEXT()
        #
        for dd in self.MyTextInput_COL_SUMS:
            dd.SET_TEXT()
        for row in range(4):
            self.MyTextInput_ROW_SUMS[row].SET_TEXT()
            self.MyTextInput_COL_SUMS[row].SET_TEXT()
            for col in range(4):
                self.MyTextInput_MY_SOLUTION_CELLS[row][col].SET_TEXT()
                self.MyTextInput_REMAINING_OPTIONS[row][col].SET_TEXT()
        self.Int_COL_SUMS = [None, None, None, None]  # MyTextInput_COL_SUMS
        self.Int_MY_SOLUTION = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]  # MyTextInput_MY_SOLUTION_CELLS
        self.Int_CELL_OPTIONS = [[[], [], [], []], [[], [], [], []], [[], [], [], []], [[], [], [], []]]  # MyTextInput_REMAINING_OPTIONS
        self.Int_ROW_SUMS = [None, None, None, None]  # MyTextInput_ROW_SUMS

        self.LastTopBoxes = {"row": None, "col": None, "thesum": None, "numevens": None, "musthave": None}

        self.Int_NUM_EVENS_BY_ROW = [None, None, None, None]
        self.Int_NUM_EVENS_BY_COL = [None, None, None, None]

        return

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def CREATE_THE_GUI(self):
        #
        self.add_widget(self.MAKE_UTIL_BUTTONS(size_hint=(1, .2)))
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
        mainlayout.cols = 1

        sublayout1 = GridLayout()
        sublayout1.cols = 4
        sublayout2 = GridLayout()
        sublayout2.cols = 4

        sublayout1.add_widget(Button(text="CLEAR", on_press=self.CLEAR_btn))
        #
        #mainlayout.add_widget(Button(text="Choose Puzzle", on_press=self.ChoosePuzzle))
        #
        sublayout1.add_widget(Button(text="Save Puzzle", on_press=self.SavePuzzle))
        #
        sublayout1.add_widget(Button(text="Load\nPuzzle", on_press=self.LoadPuzzle))
        #
        sublayout1.add_widget(Button(text="Load saved\nPuzzle", on_press=self.btn_LoadSavedPuzzle))
        #
        #
        sublayout2.add_widget(Button(text="Rip it good", on_press=self.RipItGood))
        #
        self.BUTTON_UNDO = Button(text="Back", on_press=self.Undo)
        sublayout2.add_widget(self.BUTTON_UNDO)
        #
        self.BUTTON_FORWARD = Button(text="Forward", on_press=self.ForwardOne)
        sublayout2.add_widget(self.BUTTON_FORWARD)
        #
        sublayout2.add_widget(Button(text="Exit", on_press=self.Exit))
        #
        mainlayout.add_widget(sublayout1)
        mainlayout.add_widget(sublayout2)
        #
        return mainlayout

    def MAKE_Sum20_NumEvens_MustHave(self, size_hint):
        SUM_EV_MUST = GridLayout(size_hint=size_hint)  # row_force_default=True, row_default_height=40, col_force_default=True, col_default_width=400)
        SUM_EV_MUST.cols = 1
        # Accepts input:
        self.SUM20_INPUT = cls_Label_and_TextInput(app=self, GUI=SUM_EV_MUST, name="Sum", readonly=False, textbindfn=self.entry_COVER_NEW)
        self.NUM_EVENS_INPUT = cls_Label_and_TextInput(app=self, GUI=SUM_EV_MUST, name="# Evens", readonly=False, textbindfn=self.entry_COVER_NEW)
        self.MUST_HAVE_INPUT = cls_Label_and_TextInput(app=self, GUI=SUM_EV_MUST, name="Must have", readonly=False, textbindfn=self.entry_COVER_NEW)
        return SUM_EV_MUST

    def MAKE_Sol_Section(self, size_hint):
        TOP_SECTION = GridLayout(size_hint=size_hint)  # row_force_default=True, row_default_height=40, col_force_default=True, col_default_width=400)
        TOP_SECTION.cols = 1
        # Readonly:
        self.NUMBER_IN_ALL = cls_Label_and_TextInput(app=self, GUI=TOP_SECTION, name="Number in all", readonly=True)
        self.POTENTIAL_SOLUTIONS = cls_Label_and_TextInput(app=self, GUI=TOP_SECTION, name="Remaining Solutions", readonly=True, multiline=False)
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
                acell = myButton(self, text='odd', group=f"oe{row}{col}", row=row, col=col, font_size=12)  # odd/even
                self.Buttons_ODD_EVEN[row][col] = acell
                arow_middle.add_widget(acell)
            AROW.add_widget(arow_middle)

            # RIGHT:  R SUM
            arow_right_r_sum = BoxLayout()
            #
            sumrowbox = SumRow(self, "rowsum", num=row)
            sumrowbox.bind(text=self.entry_TEXT)  # entry_R_SUM)                                     # 'r sum'
            #sumrowbox.bind(focus=sumrowbox.on_focus)
            arow_right_r_sum.add_widget(sumrowbox)
            AROW.add_widget(arow_right_r_sum)
            self.MyTextInput_ROW_SUMS[row] = sumrowbox
            #
            # add the row to the main GUI:
            CELLS.add_widget(AROW)

        # ---------------------------------------                                                          'col sums'
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
            sumcolbox.bind(text=self.entry_TEXT)
            bottom_middle.add_widget(sumcolbox)
            self.MyTextInput_COL_SUMS[col] = sumcolbox
        BOTTOM_ROW.add_widget(bottom_middle)

        # RIGHT SIDE (just a blank)
        #bottom_right = Label(text="")
        #self.EXPLANATION = myTextInput(self, "EXPLANATION", readonly=True, multiline=True)
        self.EXPLANATION = cls_Explanation()
        SET_COLOR(self.EXPLANATION, "brown")
        BOTTOM_ROW.add_widget(self.EXPLANATION)

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
                self.MyTextInput_REMAINING_OPTIONS[row][col] = box
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
                self.MyTextInput_MY_SOLUTION_CELLS[row][col] = box
                box.bind(text=self.entry_A_SOLUTION)
                #box.bind(focus=box.on_focus)
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
        if value:
            thesum = int(value)
        else:
            return
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
                self.refresh_remaining_options(pot_sols, rownum=therow)
                #self.find_unique_to_all(pot_sols)
            else:
                _joe = 12  # now what?
        elif isinstance(instance, SumCol):
            thecol = instance.ANUM
            self.Int_COL_SUMS[thecol] = int(value)
        else:
            _joe = 12  # What am I?
        self.MEGA_POPULATE_OPTIONS()

        # which = instance.MY_TAB_NUMBER
        # next_tabber = (which + 1) % (myTextInput.TOTAL_NUMBER_OF_TABS + 1)
        # instance.TAB_NEXT = next_tabber
        # instance.TAB_ORDER[instance.TAB_NEXT].focus = True

        return

    def SET_TEXT(self, widget, value: str):  # myInputs
        text = value
        if isinstance(widget, (SumRow, SumCol, cls_Label_and_TextInput)):
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
        for cell in self.MyTextInput_ROW_SUMS:
            SET_COLOR(cell, NORMAL_COLOR)
        for cell in self.MyTextInput_COL_SUMS:
            SET_COLOR(cell, NORMAL_COLOR)
        return

    def reset_remaining_options_colors(self):
        for row in range(4):
            for col in range(4):
                SET_COLOR(self.MyTextInput_REMAINING_OPTIONS[row][col], REMAINING_OPTIONS_COLOR)
        return


    def hightlight_Remaining_Options(self, p_row=None, p_col=None):
        _joe = 12
        for row in range(4):
            for col in range(4):
                cur_color = self.MyTextInput_REMAINING_OPTIONS[row][col].background_color
                if cur_color != MY_RED:
                    SET_COLOR(self.MyTextInput_REMAINING_OPTIONS[row][col], REMAINING_OPTIONS_COLOR)
        if p_row is not None:
            # Highlight row:
            for cell in self.MyTextInput_REMAINING_OPTIONS[p_row]:
                cur_color = cell.background_color
                if cur_color != MY_RED:
                    SET_COLOR(cell, HIGHLIGHT_COLOR)
                    _joe = cell.background_color
        elif p_col is not None:
            # Highlight col:
            for row in self.MyTextInput_REMAINING_OPTIONS:
                cell = row[p_col]
                cur_color = cell.background_color
                if cur_color != MY_RED:
                    SET_COLOR(cell, HIGHLIGHT_COLOR)
                    _joe = cell.background_color
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
        self.reset_sum_colors()  # DOES THIS GET HIT?
        self.reset_top_boxes(colors_only=True)
        if value is True:
            SET_COLOR(instance, HIGHLIGHT_COLOR)
        return


    def CLEAR_btn(self, instance=None):
        delete_undo_files()
        self.LAST_UNDO_FILE_NUM = 0
        self.CLEAR(instance)
        return

    def CLEAR(self, instance=None):
        #self.LAST_UNDO_FILE_NUM = 0
        self.EXPLANATION.SET_TEXT()
        self.BUTTON_UNDO.text = "Undo"
        self.BUTTON_FORWARD.text = "Forward"
        cur_dnmp_status = self.DO_NOT_MEGA_POPULATE
        self.DO_NOT_MEGA_POPULATE = True
        self.RESET_VARIABLES()
        self.reset_top_boxes(colors_only=False)
        for row in range(4):
            self.MyTextInput_ROW_SUMS[row].SET_TEXT()
            for col in range(4):
                self.MyTextInput_COL_SUMS[row].SET_TEXT()
                self.Buttons_ODD_EVEN[row][col].state = "normal"
                self.MyTextInput_REMAINING_OPTIONS[row][col].SET_TEXT()
                SET_COLOR(self.MyTextInput_REMAINING_OPTIONS[row][col], REMAINING_OPTIONS_COLOR)
                self.MyTextInput_MY_SOLUTION_CELLS[row][col].SET_TEXT()
                SET_COLOR(self.MyTextInput_MY_SOLUTION_CELLS[row][col], MY_SOLUTION_COLOR)
        self.DO_NOT_MEGA_POPULATE = cur_dnmp_status
        SET_FOCUS(self.SUM20_INPUT)
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
        self.BUTTON_UNDO.text = f"Undo ({self.LAST_UNDO_FILE_NUM})"
        if forwards_left:
            self.BUTTON_FORWARD.text = f"Forward ({forwards_left})"
        else:
            self.BUTTON_FORWARD.text = f"Forward"
        return


    def Undo(self, instance):
        self.LAST_UNDO_FILE_NUM = max(0, self.LAST_UNDO_FILE_NUM - 1)
        previous_file = f"UndoFiles/{TODAY}_{self.LAST_UNDO_FILE_NUM}.txt"
        if not file_exists(previous_file):
            self.CLEAR()
            self.reset_remaining_options_colors()
            instance.text = f"Undo"
            self.BUTTON_FORWARD.text = f"Forward ({self.GREATEST_UNDO_FILE_NUM})"
            return
        self.Undo_engine(instance, previous_file)
        #
        self.BUTTON_UNDO.text = f"Undo ({self.LAST_UNDO_FILE_NUM})"
        forwards_left = self.GREATEST_UNDO_FILE_NUM - self.LAST_UNDO_FILE_NUM
        self.BUTTON_FORWARD.text = f"Forward ({forwards_left})"
        return


    def Undo_engine(self, instance, required_file):
        self.SAVE_AN_UNDO_FILE = False
        self.LoadSavedPuzzle(filename=required_file, from_undo=True)
        # need to recreate CELL OPTIONS
        self.SAVE_AN_UNDO_FILE = True
        #
        return


    def Exit(self, instance):
        sys.exit(0)



    def entry_R_POT_SOLS(self, instance, value):
        thesum = int(value)  # does this get hit?
        if thesum < 10:
            return
        therow = instance.ANUM
        self.Int_ROW_SUMS[therow] = int(value)
        numevens = sum([1 for xx in self.Buttons_ODD_EVEN[instance.ANUM] if xx.MYTEXT == "EVEN"])
        musthave = self.get_must_have(row=therow)
        res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=(0/0))
        eliminated_sols = res[0]
        pot_sols = res[1]
        self.ELIMINATED_SOLUTIONS.SET_TEXT(eliminated_sols)
        if pot_sols:
            self.refresh_remaining_options(pot_sols, rownum=therow)
            #self.find_unique_to_all(pot_sols)
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
        self.NUMBER_IN_ALL.SET_TEXT()
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


    def Save_Undo_Level(self):
        if not self.SAVE_AN_UNDO_FILE:
            return
        DIR = "UndoFiles"
        self.LAST_UNDO_FILE_NUM += 1
        self.GREATEST_UNDO_FILE_NUM = max(self.GREATEST_UNDO_FILE_NUM, self.LAST_UNDO_FILE_NUM)
        self.BUTTON_UNDO.text = f"Undo ({self.LAST_UNDO_FILE_NUM})"
        filename = f"{DIR}/{TODAY}_{self.LAST_UNDO_FILE_NUM}.txt"
        self.SavePuzzle(filename=filename)
        return


    def MEGA_POPULATE_OPTIONS(self, ok=False):
        if self.DO_NOT_MEGA_POPULATE:
            return

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
                res = self.refresh_remaining_options(pot_sols, rownum=row, ok=ok)
                if res:
                    return res
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
                res = self.refresh_remaining_options(pot_sols, colnum=col, ok=ok)
                if res:
                    return res
        #
        # See if there is a cell with only one option left:
        for row in range(4):
            for col in range(4):
                if self.Int_MY_SOLUTION[row][col] != 0:
                    SET_COLOR(self.MyTextInput_REMAINING_OPTIONS[row][col], REMAINING_OPTIONS_COLOR)
                else:
                    cell = self.Int_CELL_OPTIONS[row][col]
                    if self.Int_CELL_OPTIONS[row][col]:
                        if len(self.Int_CELL_OPTIONS[row][col]) == 1:
                            #SET_COLOR(self.MyTextInput_REMAINING_OPTIONS[row][col], MY_RED)  #  "red"
                            SET_RED(self.MyTextInput_REMAINING_OPTIONS[row][col])
                        elif len(self.Int_CELL_OPTIONS[row][col]) == 0:
                            SET_COLOR(self.MyTextInput_REMAINING_OPTIONS[row][col], NORMAL_COLOR)
        #
        # Back this up as a future 'undo' level
        if self.SAVE_AN_UNDO_FILE:
            self.Save_Undo_Level()
        #
        return


    @static_vars(ct=0)
    def find_unique_to_all(self, pot_sols, rownum=None, colnum=None, ok=False):
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
            if len(res) == len(flatten_list(pot_sols)):
                self.NUMBER_IN_ALL.SET_TEXT()
            else:
                unique_str = ", ".join([str(xx) for xx in res])
                self.NUMBER_IN_ALL.SET_TEXT(unique_str)
                if len(res) == 1:
                    if rownum is not None and not any([True for xx in self.Int_MY_SOLUTION[rownum] if xx!=0]):
                        SET_RED(self.NUMBER_IN_ALL)
                    elif colnum is not None and not any([xx[colnum] for xx in self.Int_MY_SOLUTION if xx[colnum] != 0]):
                        SET_RED(self.NUMBER_IN_ALL)
                    #SET_RED(self.NUMBER_IN_ALL)
                else:
                    SET_COLOR(self.NUMBER_IN_ALL, NO_FOCUS_COLOR)
        else:
            self.NUMBER_IN_ALL.SET_TEXT()
            SET_COLOR(self.NUMBER_IN_ALL, NO_FOCUS_COLOR)
        return res


    def net_out(self, row, col, these_options):
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


    def refresh_remaining_options(self, pot_sols, rownum=None, colnum=None, ok=False):
        # -----------------------------------------------------------------------
        # -----------------------------------------------------------------------
        assert rownum is not None or colnum is not None
        self.reset_remaining_options_colors() ###########################################
        unique_to_all = self.find_unique_to_all(pot_sols, rownum=rownum, colnum=colnum, ok=ok)
        flat_pot_sols = list(set(flatten_list(pot_sols)))
        if not rownum is None:
            odd_evens = self.Buttons_ODD_EVEN[rownum]
            for col in range(4):
                sol = self.Int_MY_SOLUTION[rownum][col]
                if sol and sol in flat_pot_sols:
                    flat_pot_sols.remove(sol)
            even_pot_sols = [xx for xx in flat_pot_sols if xx in [2, 4, 6, 8]]
            even_pot_sols.sort()
            odd_pot_sols = [xx for xx in flat_pot_sols if xx not in [2, 4, 6, 8]]
            odd_pot_sols.sort()
            for col, cell in enumerate(self.MyTextInput_REMAINING_OPTIONS[rownum]):
                if self.Int_MY_SOLUTION[rownum][col] != 0:
                    # A solved cell has no remaining options
                    self.SET_TEXT(cell, "")
                    continue
                if odd_evens[col].MYTEXT == "EVEN":
                    kk, kkstr = self.net_out(rownum, col, even_pot_sols)
                    self.Int_CELL_OPTIONS[rownum][col] = kk
                    self.SET_TEXT(cell, kkstr)
                else:
                    kk, kkstr = self.net_out(rownum, col, odd_pot_sols)
                    self.Int_CELL_OPTIONS[rownum][col] = kk
                    self.SET_TEXT(cell, kkstr)
                if INIT_IS_DONE and len(unique_to_all) != 1:
                    for uu in unique_to_all:
                        if sum([1 for xx in self.Int_CELL_OPTIONS[rownum] if uu in xx]) == 1:
                            for ct in range(4):
                                co = self.Int_CELL_OPTIONS[rownum][ct]
                                if uu in co:
                                    self.EXPLANATION.SET_EXPLANATION(rownum, ct, uu)
                                    SET_RED(self.MyTextInput_REMAINING_OPTIONS[rownum][ct])
                if len(unique_to_all) == 1:
                    if unique_to_all[0] in kk:
                        if len(kk) == 1:
                            #self.EXPLANATION.SET_EXPLANATION(cell.Arownum, ct, uu)
                            SET_RED(cell)
                            SET_RED(self.NUMBER_IN_ALL)
                        else:
                            SET_COLOR(cell, "palevioletred")
                else:
                    # Number is probably a solution already
                    SET_COLOR(cell, REMAINING_OPTIONS_COLOR)
                    SET_COLOR(self.NUMBER_IN_ALL, NO_FOCUS_COLOR)
            # -----------------------------
        else:
            # -----------------------------
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
                    if self.MyTextInput_REMAINING_OPTIONS[row][colnum].text:
                        self.MyTextInput_REMAINING_OPTIONS[row][colnum].SET_TEXT()
                    continue
                if self.Buttons_ODD_EVEN[row][colnum].MYTEXT == "EVEN":
                    kk, kkstr = self.net_out(row, colnum, even_pot_sols)
                    self.Int_CELL_OPTIONS[row][colnum] = kk
                    self.MyTextInput_REMAINING_OPTIONS[row][colnum].SET_TEXT(kkstr)
                else:
                    kk, kkstr = self.net_out(row, colnum, odd_pot_sols)
                    self.Int_CELL_OPTIONS[row][colnum] = kk
                    self.MyTextInput_REMAINING_OPTIONS[row][colnum].SET_TEXT(kkstr)
                if INIT_IS_DONE and len(unique_to_all) != 1:
                    for uu in unique_to_all:
                        if sum([1 for xx in [xx[colnum] for xx in self.Int_CELL_OPTIONS] if uu in xx]) == 1:
                            for ct in range(4):
                                co = self.Int_CELL_OPTIONS[colnum][ct]
                                if uu in co:
                                    self.EXPLANATION.SET_EXPLANATION(ct, colnum, uu)
                                    SET_RED(self.MyTextInput_REMAINING_OPTIONS[ct][colnum])
                if len(unique_to_all) == 1 and unique_to_all[0] in kk:
                    self.EXPLANATION.SET_EXPLANATION(row, colnum, unique_to_all[0])
                    SET_RED(self.MyTextInput_REMAINING_OPTIONS[row][colnum])
                    SET_RED(self.NUMBER_IN_ALL)
                else:
                    # Number is probably a solution already
                    SET_COLOR(self.MyTextInput_REMAINING_OPTIONS[row][colnum], REMAINING_OPTIONS_COLOR)
                    SET_COLOR(self.NUMBER_IN_ALL, NO_FOCUS_COLOR)
        return False


    def entry_A_SOLUTION(self, instance, value):
        # when I enter something into a solution, it then acts as a 'must have' for that row and col
        if value == "":
            sol = 0
        else:
            sol = int(value)
        row = instance.AROW
        col = instance.ACOL
        #self.Int_MY_SOLUTION[row][col] = sol
        if self.SET_SOLUTION(row, col, sol):
            self.Int_CELL_OPTIONS[row][col] = []
            if INIT_IS_DONE and self.DO_NOT_MEGA_POPULATE is False:
                self.MEGA_POPULATE_OPTIONS(ok=True)  # entry_A_SOLUTION
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
        eliminated_sols.sort()
        good_sols.sort()
        if len(good_sols) == 1:
            _joe = 12  # good_sols = good_sols[0]
        self.POTENTIAL_SOLUTIONS.SET_TEXT(good_sols)
        #
        # eliminated_sols.sort()
        # good_sols.sort()
        return eliminated_sols, good_sols


    def entry_COVER(self, instance, value):
        curstatus = self.SAVE_AN_UNDO_FILE
        self.SAVE_AN_UNDO_FILE = False
        if instance.ANAME == "Sum":
            cur = self.SUM20_INPUT.MYTEXTBOX.text
            if cur != value:
                self.entry_THE_SUM(instance, value)
        elif instance.ANAME == "# Evens":
            cur = self.NUM_EVENS_INPUT.MYTEXTBOX.text
            if cur != value:
                self.entry_NUM_EVENS(instance, value)
        elif instance.ANAME == "Must have":
            cur = self.MUST_HAVE_INPUT.MYTEXTBOX.text
            if cur != value:
                self.entry_MUST_HAVE(instance, value)
        else:
            _joe = 12  # ??
        self.SAVE_AN_UNDO_FILE = curstatus
        #instance.text = f"Undo_engine ({self.LAST_UNDO_FILE_NUM})"
        return


    def entry_COVER_NEW(self, instance, value):
        thesum = self.SUM20_INPUT.MYTEXTBOX.text
        numevens = self.NUM_EVENS_INPUT.MYTEXTBOX.text
        musthave = self.MUST_HAVE_INPUT.MYTEXTBOX.text
        #
        if thesum and numevens:
            curstatus = self.SAVE_AN_UNDO_FILE
            self.SAVE_AN_UNDO_FILE = False
            self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
            if INIT_IS_DONE and self.DO_NOT_MEGA_POPULATE is False:
                self.MEGA_POPULATE_OPTIONS(ok=True)  # entry_NUM_EVENS
            self.SAVE_AN_UNDO_FILE = curstatus
        return

    # def entry_THE_SUM(self, instance, value):
    #     # this is the one at the very top of the GUI
    #     thesum = value
    #     numevens = self.NUM_EVENS_INPUT.MYTEXTBOX.text
    #     musthave = self.MUST_HAVE_INPUT.MYTEXTBOX.text
    #     if thesum and numevens:
    #         self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
    #         if INIT_IS_DONE and self.DO_NOT_MEGA_POPULATE is False:
    #             self.MEGA_POPULATE_OPTIONS(ok=True)  # entry_THE_SUM
    #     return
    #
    # def entry_NUM_EVENS(self, instance, value):
    #     thesum = self.SUM20_INPUT.MYTEXTBOX.text
    #     numevens = value
    #     musthave = self.MUST_HAVE_INPUT.MYTEXTBOX.text
    #     if thesum and numevens:
    #         self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
    #         if INIT_IS_DONE and self.DO_NOT_MEGA_POPULATE is False:
    #             self.MEGA_POPULATE_OPTIONS(ok=True)  # entry_NUM_EVENS
    #     return
    #
    # def entry_MUST_HAVE(self, instance, value):
    #     thesum = self.SUM20_INPUT.MYTEXTBOX.text
    #     numevens = self.NUM_EVENS_INPUT.MYTEXTBOX.text
    #     musthave = value
    #     if thesum and numevens:
    #         self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
    #         if INIT_IS_DONE and self.DO_NOT_MEGA_POPULATE is False:
    #             self.MEGA_POPULATE_OPTIONS(ok=True)  # entry_MUST_HAVE
    #     return


    def SavePuzzle(self, instance=None, filename=""):
        # pfilename = f"saved_puzzle.p"
        # pickle.dump(self, open(pfilename, "wb"))
        if not filename:
            filename = f"saved_puzzle.txt"
        with open(filename, "w") as file:
            # Odd/even:
            for row in range(4):
                for col in range(4):
                    file.write(f"{self.Buttons_ODD_EVEN[row][col].MYTEXT}\n")
            # Row sums:
            for xx in range(4):
                val1 = self.Int_ROW_SUMS[xx] or 0
                file.write(f"{val1}\n")
            # Col sums:
            for xx in range(4):
                val2 = self.Int_COL_SUMS[xx] or 0
                file.write(f"{val2}\n")
            # My solution:
            for row in range(4):
                for col in range(4):
                    file.write(f"{self.Int_MY_SOLUTION[row][col]}\n")
        return

    def btn_LoadSavedPuzzle(self, instance=None):
        self.LoadSavedPuzzle(instance)
        self.SAVE_AN_UNDO_FILE = True
        self.Save_Undo_Level()
        return


    def LoadSavedPuzzle(self, instance=None, filename="", from_undo=False):
        global INIT_IS_DONE  # need this
        if INIT_IS_DONE:
            self.CLEAR()

        if not filename:
            filename = f"saved_puzzle.txt"
        with open(filename, "r") as file:
            onebigline = file.read()
        all_lines = onebigline.split()

        ct = -1
        # Odd/Even buttons:
        for row in range(4):
            for col in range(4):
                ct += 1
                res2 = all_lines[ct]
                if res2.lower() == "even":
                    self.Buttons_ODD_EVEN[row][col].state = "down"
        # Row sums:
        for xx in range(4):
            ct += 1
            res0 = int(all_lines[ct])
            self.Int_ROW_SUMS[xx] = res0
            if res0 == 0:
                self.MyTextInput_ROW_SUMS[xx].SET_TEXT()
            else:
                self.MyTextInput_ROW_SUMS[xx].SET_TEXT(res0)
        # Col sums:
        for xx in range(4):
            ct += 1
            res1 = int(all_lines[ct])
            self.Int_COL_SUMS[xx] = res1
            if res1 == 0:
                self.MyTextInput_COL_SUMS[xx].SET_TEXT()
            else:
                self.MyTextInput_COL_SUMS[xx].SET_TEXT(res1)
        # My solution so far:
        for row in range(4):
            for col in range(4):
                ct += 1
                res3 = int(all_lines[ct])
                if res3 == 0:
                    continue
                if self.Int_MY_SOLUTION[row][col] == 0 and res3 == 0:
                    _joe = 12  # why am I here doing this?
                self.SET_SOLUTION(row, col, res3)
        #
        if not from_undo:
            self.RipItGood()
        self.Save_Undo_Level()
        INIT_IS_DONE = True
        SET_FOCUS(self.SUM20_INPUT.MYTEXTBOX)
        return


    def ChoosePuzzle(self, instance=None):
        tt = APP_MainApp()
        tt.title = "Choose a puzzle!"
        tt.run()
        return

    def LoadPuzzle(self, instance=None):
        cur_dnmp_status = self.DO_NOT_MEGA_POPULATE
        self.DO_NOT_MEGA_POPULATE = True

        global INIT_IS_DONE  # need this
        if INIT_IS_DONE:
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
            self.MyTextInput_ROW_SUMS[row].SET_TEXT(val)
        #
        for arr in apuzzle["colsum"]:
            col, val = arr
            self.MyTextInput_COL_SUMS[col].SET_TEXT(val)
        #
        for row, col, num in apuzzle["solutions"]:
            self.MyTextInput_MY_SOLUTION_CELLS[row][col].SET_TEXT(num)
        #
        #self.RipItGood()
        #
        INIT_IS_DONE = True
        # SET_FOCUS(main_layout.SUM20_INPUT)  # works, 'cls_Label_and_TextInput'
        SET_FOCUS(self.SUM20_INPUT)  # .MYTEXTBOX)
        self.DO_NOT_MEGA_POPULATE = cur_dnmp_status
        return


    def SET_SOLUTION(self, row, col, num):
        if (row, col, num) in self.EXPLANATION.MY_DATA:
            _joe = 12  # remove it, reset box
        num = int(num)
        if INIT_IS_DONE:
            if num not in [0] + self.Int_CELL_OPTIONS[row][col]:
                return False  # do not let this bad # go into this cell   self.Int_CELL_OPTIONS[row][col] = []
        my_sols_copy = deepcopy(self.Int_MY_SOLUTION)
        #self.Int_MY_SOLUTION[p_row][p_col] = num
        my_sols_copy[row][col] = num
        #self.Int_CELL_OPTIONS[p_row][p_col] = []
        if len([True for xx in my_sols_copy[row] if xx != 0]) == 4:
            mysum = sum([xx for xx in my_sols_copy[row] if xx != 0])
            if mysum != self.Int_ROW_SUMS[row]:
                _joe = 12  #
        if len([True for xx in my_sols_copy if xx[col] != 0]) == 4:
            mysum = sum([xx[col] for xx in my_sols_copy if xx[col] != 0])
            if mysum != self.Int_COL_SUMS[col]:
                _joe = 12
        #
        self.Int_MY_SOLUTION[row][col] = num
        #self.MyTextInput_MY_SOLUTION_CELLS[row][col].SET_TEXT(num)  # this triggers recursion
        if num == 0:
            self.MyTextInput_MY_SOLUTION_CELLS[row][col].text = ""
        else:
            self.MyTextInput_MY_SOLUTION_CELLS[row][col].text = str(num)
        self.Int_CELL_OPTIONS[row][col] = []
        self.MyTextInput_REMAINING_OPTIONS[row][col].SET_TEXT()
        if all([yy!=0 for xx in self.Int_MY_SOLUTION for yy in xx]):
            for row in range(4):
                for col in range(4):
                    SET_FOCUS(self.MyTextInput_MY_SOLUTION_CELLS[row][col], False)
                    SET_RED(self.MyTextInput_MY_SOLUTION_CELLS[row][col])
            SET_FOCUS(self.SUM20_INPUT.MYTEXTBOX)
        #else:
        #    self.RipItGood()
        return True


    def RipItGood(self, instance=None):
        cur_dnmp_status = self.DO_NOT_MEGA_POPULATE
        self.DO_NOT_MEGA_POPULATE = True
        self.reset_top_boxes(colors_only=False)
        try:
            for row in range(4):
                SET_FOCUS(self.MyTextInput_ROW_SUMS[row])     # this does checking and work
                self.MyTextInput_ROW_SUMS[row].focus = False  # this doesn't
            for col in range(4):
                SET_FOCUS(self.MyTextInput_COL_SUMS[col])     # this does checking and work
                self.MyTextInput_COL_SUMS[col].focus = False  # this doesn't
        except EXIT_RIP_IT:
            _joe = 12  # just go on to the below
            pass
        except:
            raise
        else:
            # Only if successful
            cur_sauf_status = self.SAVE_AN_UNDO_FILE
            self.SAVE_AN_UNDO_FILE = False
            self.MEGA_POPULATE_OPTIONS()
            self.SAVE_AN_UNDO_FILE = cur_sauf_status
            #
            self.SUM20_INPUT.focus = True  # this doesn't do work
        finally:
            # ALWAYS
            self.DO_NOT_MEGA_POPULATE = cur_dnmp_status
        return
# ----- class myInputs - END   --------------------------------------------------------------------------------------


# ----- class AskQuestion - START -----------------------------------------------------------------------------------
class AskQuestion(App):
    """ Do this via a 'Screen Manager':
        https://kivy.org/doc/stable/api-kivy.uix.screenmanager.html?highlight=multiple%20windows
    """
    def __init__(self):
        super().__init__()

    def build(self):  # AskQuestion
        questionlayout = GridLayout()
        questionlayout.cols = 1
        questionlayout.add_widget(cls_Label_and_TextInput(app=self, GUI=questionlayout, name="Choose Puzzle"))
        return questionlayout
# ----- class AskQuestion - END   -----------------------------------------------------------------------------------



# ----- class APP_MainApp - START ---------------------------------------------------------------------------------------
class APP_MainApp(App):
    def __init__(self):
        super().__init__()

    def build(self):  # APP_MainApp
        delete_undo_files()
        main_layout = myInputs(which)
        machine = os.environ.get("MACHINE")
        if machine == "PC":
            create_loggers()
        SET_FOCUS(main_layout.SUM20_INPUT)  # works, 'cls_Label_and_TextInput'
        # widget = who_has_the_focus(main_layout)
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
