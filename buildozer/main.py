import os
import re
from typing import Callable
#
from kivy.app import App
#from kivy.uix.image import Image
#from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
#from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics.instructions import Canvas, CanvasBase
from utils import *  # NORMAL_COLOR, NO_FOCUS_COLOR, HIGHLIGHT_COLOR, ALL_POTENTIAL_SOLUTIONS, static_vars, get_sql_today, flatten_list


res = get_sql_today()
TODAY = res[0]
HOUR = int(res[1])


"""
# ----- class myTextInput - START -----------------------------------------------------------------------------------
class myTextInput(TextInput):
    def __init__(self, *args, **kwargs):
        self.MYAPP = args[0]
        self.ANAME = args[1]
        self.AROW = args[2]
        self.ACOL = args[3]
        kwargs["halign"] = "center"
        super().__init__(**kwargs)
        
    def __str__(self):
        res = f"myTextInput({self.ANAME} ({self.AROW}, {self.ACOL})"
        return res

    def on_focus(self, instance, value, *largs):  # myTextInput
        assert instance.ANAME == "MY_SOLUTION"
        for row in range(4):
            for col in range(4):
                self.MYAPP.myTextInputs_MY_SOLUTION_CELLS[row][col].background_color = NORMAL_COLOR
        # setting to HIGHLIGHT takes place in myInputs for some reason
        return
# ----- class myTextInput - END   -----------------------------------------------------------------------------------
"""


# ----- class myNumbersOnlyInput - START ----------------------------------------------------------------------------
class myNumbersOnlyInput(TextInput):
    TAB_NUM = -1
    TAB_ORDER = {}
    TAB_NEXT = None
    PATTERN = re.compile('[^0-9]')  # To only allow floats (0 - 9 and a single period)

    def __str__(self):
        if not self.ANUM is None:
            res = f"myNumbersOnlyInput('{self.ANAME}') num={self.ANUM}"
        else:
            res = f"myNumbersOnlyInput('{self.ANAME}') -> ({self.AROW}, {self.ACOL})"
        return res


    def __init__(self, *args, **kwargs):
        self.MYAPP = args[0]
        self.ANAME = args[1]
        #
        arow = kwargs.get("row", None)
        acol = kwargs.get("col", None)
        anum = kwargs.get("num", None)
        mycolor = kwargs.get("mycolor", None)
        self.AROW = arow
        self.ACOL = acol
        self.ANUM = anum
        self.MYCOLOR = mycolor
        #
        kwargs["halign"] = "center"

        for arg in ["row", "col", "num", "mycolor"]:
            kwargs.pop(arg, None)
        #
        super().__init__(**kwargs)
        #
        # TABBING?
        if kwargs.get("readonly", False) is True:
            self.TAB_NUM = None
            if not self.MYCOLOR:
                self.background_color = NO_FOCUS_COLOR
            else:
                self.background_color = self.MYCOLOR
        else:
            myNumbersOnlyInput.TAB_NUM += 1
            self.TAB_NUM = myNumbersOnlyInput.TAB_NUM
            myNumbersOnlyInput.TAB_ORDER[self.TAB_NUM] = self

        return

    # def _on_focus(self, instance, value, *largs):
    #     for cell in self.MYAPP.THE_TOP_THREE:
    #         if cell:
    #             cell.background_color = NORMAL_COLOR
    #     instance.background_color = HIGHLIGHT_COLOR


    def insert_text(self, substring, from_undo=False):  # myNumbersOnlyInput(TextInput):
        if '.' in self.text:
            s = re.sub(self.PATTERN, '', substring)
        else:
            # To allow a period as well:  s = '.'.join(...same as below)
            s = ''.join(re.sub(self.PATTERN, '', s) for s in substring.split('.', 1))
        return super().insert_text(s, from_undo=from_undo)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        TextInput.keyboard_on_key_down(self, window, keycode, text, modifiers)
        if keycode[1] == ".":
            _joe = 12
            self.SET_TEXT(self, "")
        elif keycode[1] == "tab":
            # to make this smarter: https://kivy.org/doc/stable/api-kivy.uix.behaviors.focus.html
            INC = 1
            if "shift" in modifiers:
                INC = -1
            which = self.TAB_NUM
            next = (which + INC) % (myNumbersOnlyInput.TAB_NUM + 1)
            # self.TAB_ORDER[next].focus = True  #  tab_order[next].focus = True
            self.TAB_NEXT = next
        #TextInput.keyboard_on_key_down(self, window, keycode, text, modifiers)

    def keyboard_on_key_up(self, window, keycode):
        # Note: After key_up, for tab-shifting, 'on_focus' gets triggered
        if keycode[1] == "tab":
            self.TAB_ORDER[self.TAB_NEXT].focus = True
        return

    def keyboard_on_textinput(self, window, text):
        _joe = 12
        TextInput.keyboard_on_textinput(self, window, text)
        return

# ----- class myNumbersOnlyInput - END   ----------------------------------------------------------------------------





# ----- class myButton - START --------------------------------------------------------------------------------------
class myButton(ToggleButton):
    def __init__(self, app, row=None, col=None, text="", group=""):  # **kwargs):
        self.MYAPP = app
        super(myButton, self).__init__(text=text, group=group)  # **kwargs)
        self.source = 'atlas://data/images/defaulttheme/checkbox_off'
        self.MYROW = row
        self.MYCOL = col
        self.MYGROUP = group
        self.MYTEXT = text


    def on_state(self, widget, value):
        #self.MYAPP.reset_top_boxes()
        if value == "down":
            #self.source = 'atlas://data/images/defaulttheme/checkbox_on'
            self.MYAPP.SET_TEXT(self, "even")
            self.MYTEXT = "even"
        else:
            #self.source = 'atlas://data/images/defaulttheme/checkbox_off'
            self.MYAPP.SET_TEXT(self, "odd")
            self.MYTEXT = "odd"
        self.resum_numevens()
        return

    def resum_numevens(self):
        for row in range(4):
            numevens = sum([1 for xx in self.MYAPP.buttons_ODD_EVEN[row] if xx.MYTEXT == 'even'])
            self.MYAPP.int_NUM_EVENS_BY_ROW[row] = numevens
        for col in range(4):
            numevens = 0
            for row in range(4):
                if self.MYAPP.buttons_ODD_EVEN[row][col].MYTEXT == 'even':
                    numevens += 1
            self.MYAPP.int_NUM_EVENS_BY_COL[col] = numevens
        return

    def on_release(self):
        for row in range(4):
            numevens = sum([1 for xx in self.MYAPP.buttons_ODD_EVEN[row] if xx.MYTEXT == 'even'])
            self.MYAPP.int_NUM_EVENS_BY_ROW[row] = numevens
        for col in range(4):
            numevens = 0
            for row in range(4):
                if self.MYAPP.buttons_ODD_EVEN[row][col].MYTEXT == 'even':
                    numevens += 1
            self.MYAPP.int_NUM_EVENS_BY_COL[col] = numevens
        self.MYAPP.MEGA_POPULATE_OPTIONS()
        return

# ----- class MyButton - END   --------------------------------------------------------------------------------------


# ----- class LoginScreen - START -----------------------------------------------------------------------------------
class myVariables:
    def __init__(self):
        self.INIT_IS_DONE = False
        # TOP STUFF:
        self.SUM20_INPUT = None
        self.NUM_EVENS_INPUT = None
        self.MUST_HAVE_INPUT = None
        self.THE_TOP_THREE = None
        #
        self.UNIQUE_TO_ALL = None
        self.POTENTIAL_SOLUTIONS = None
        self.ORIGINAL_SOLUTIONS = None
        #
        #self.potential_solutions = None
        # These are the actual #s available for a cell:
        self.int_CELL_OPTIONS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]

        self.buttons_ODD_EVEN = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]

        # These are the TEXTINPUTS in the GUI:
        self.myTextInputs_REMAINING_OPTIONS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        self.myTextInputs_MY_SOLUTION_CELLS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        self.int_MY_SOLUTION = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        # self.THE_SOLUTION = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]

        self.int_NUM_EVENS_BY_ROW = [None, None, None, None]
        self.int_NUM_EVENS_BY_COL = [None, None, None, None]

        self.int_ROW_SUMS = [None, None, None, None]
        self.int_COL_SUMS = [None, None, None, None]
        self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS = [None, None, None, None]
        self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS = [None, None, None, None]
        #self.ROW_POT_SOLS = [None, None, None, None]
        #self.ROW_POT_SOLS_TEXT_INPUTS = [None, None, None, None]


class myInputs(myVariables, GridLayout):
    def __init__(self, **kwargs):
        myVariables.__init__(self)
        GridLayout.__init__(self, **kwargs)
        self.cols = 1
        #
        self.CREATE_THE_GUI()
        #
        if HOUR > 20:
            self.cycle_me(self.canvas)
        return


    def CREATE_THE_GUI(self):
        #
        self.add_widget(self.MAKE_Sum20_NumEvens_MustHave(size_hint=(.2, 1)))
        #
        self.add_widget(self.MAKE_Sol_Section(size_hint=(.2, 1)))
        #
        self.add_widget(self.MAKE_Odd_Even_Buttons(size_hint=(.2, 1)))
        #
        self.add_widget(self.MAKE_Remaining_Options(size_hint=(.2, 1)))
        #
        self.add_widget(self.MAKE_Solutions(size_hint=(.2, 1)))
        #
        return

    def get_must_have(self, row=None, col=None):
        assert not (row is None and col is None)
        if row is not None:
            res = [xx for xx in self.int_MY_SOLUTION[row] if xx != 0]
        else:
            res = [xx[col] for xx in self.int_MY_SOLUTION if xx[col] != 0]
        return res

    def entry_TEXT(self, instance, value):
        thesum = -9
        if value:
            thesum = int(value)
        if thesum < 13:
            return
        if instance.ANAME == "rowsum":
            therow = instance.ANUM
            self.int_ROW_SUMS[therow] = int(value)
            numevens = sum([1 for xx in self.buttons_ODD_EVEN[instance.ANUM] if xx.MYTEXT == 'even'])
            musthave = self.get_must_have(row=therow)
            res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
            pot_sols = res[0]
            solstr = res[1]
            if pot_sols:
                self.populate_remaining_options(pot_sols, rownum=therow)
                self.find_unique_to_all(pot_sols)
        elif instance.ANAME == "colsum":
            thecol = instance.ANUM
            self.int_COL_SUMS[thecol] = int(value)
        else:
            _joe = 12  # What am I?
        self.MEGA_POPULATE_OPTIONS()
        return

    def SET_TEXT(self, widget:TextInput, text:str):
        name = ""
        if hasattr(widget, "ANAME"):
            IGNORES = ["rowsum", "colsum", "Potential Solutions", "Sum (20)", "# Evens (2)", "Must have"]
            name = widget.ANAME
        if not isinstance(text, str):
            _joe = 12  # why not?
            text = str(text)
        widget.text = text
        return


    def cycle_me(self, what):
        if what.children:
            for ct, yy in enumerate(what.children):
                if isinstance(yy, Canvas):
                    _joe = 12
                if isinstance(yy, CanvasBase):
                    continue
                else:
                    _joe = 12
        return


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == "\t":
            _joe = 12
        # elif keycode[1] == "backspace":
        #     print("print backspace down", keycode)
        TextInput.keyboard_on_key_down(self, window, keycode, text, modifiers)


    def keyboard_on_key_up(self, window, keycode):  # , text, modifiers):
        if keycode[1] == "tab":
            _joe = 12
        # elif keycode[1] == "backspace":
        #     print("print backspace up", keycode)
        #TextInput.keyboard_on_key_down(self, window, keycode, text, modifiers)
        return



    def MAKE_Remaining_Options(self, size_hint):
        OPTIONS = GridLayout(size_hint=size_hint)
        OPTIONS.cols = 1
        OPTIONS.add_widget(Label(text="REMAINING OPTIONS:"))
        for row in range(4):
            row_layout = BoxLayout()
            for col in range(4):
                # box = myTextInput(self, "REMAINING_OPTIONS", row, col, multiline=True, readonly=True, is_focusable=False)
                box = myNumbersOnlyInput(self, "REMAINING_OPTIONS", row=row, col=col, mycolor="white", multiline=False, readonly=True, is_focusable=False)
                self.myTextInputs_REMAINING_OPTIONS[row][col] = box
                row_layout.add_widget(box)
            OPTIONS.add_widget(row_layout)
        return OPTIONS


    def MAKE_Solutions(self, size_hint):
        SOLUTIONS = GridLayout(size_hint=size_hint)
        SOLUTIONS.cols = 1
        #
        SOLUTIONS.add_widget(Label(text="MY SOLUTION:"))
        #
        for row in range(4):
            row_layout = BoxLayout()
            for col in range(4):
                # box = myTextInput(self, "MY_SOLUTION", row, col, multiline=True)
                box = myNumbersOnlyInput(self, "MY_SOLUTION", row=row, col=col, mycolor="white", multiline=False, readonly=True, is_focusable=False)
                self.myTextInputs_MY_SOLUTION_CELLS[row][col] = box
                box.bind(text=self.entry_A_SOLUTION)
                box.bind(focus=self.on_focus)
                row_layout.add_widget(box)
            SOLUTIONS.add_widget(row_layout)
        return SOLUTIONS


    def MAKE_Odd_Even_Buttons(self, size_hint):
        # The 4x4 of odd/even cells
        CELLS = GridLayout(size_hint=size_hint)
        CELLS.cols = 1
        #
        left = .125
        middle = .647
        right = 1 - left - middle
        for row in range(4):
            AROW = BoxLayout()

            # left side ('0'/'1'/'2'/'3')
            #AROW.add_widget(Label(text=str(row), size_hint=(left, 1)))

            # MIDDLE:  (this is the main chunk of this section)
            arow_middle = BoxLayout(size_hint=(middle, 1))
            #
            for col in range(4):
                acell = myButton(app=self, text='odd', group=f"oe{row}{col}", row=row, col=col)         # odd/even
                self.buttons_ODD_EVEN[row][col] = acell
                arow_middle.add_widget(acell)
            AROW.add_widget(arow_middle)

            # right R SUM:
            arow_right_r_sum = BoxLayout(size_hint=(right, 1))
            #
            #arow_right_r_sum.add_widget(Label(text="r sum:"))
            arow_right1_txt = myNumbersOnlyInput(self, "rowsum", num=row)
            arow_right1_txt.bind(text=self.entry_TEXT)  # entry_R_SUM)                                  # 'r sum'
            arow_right1_txt.bind(focus=self.on_focus)
            arow_right_r_sum.add_widget(arow_right1_txt)
            AROW.add_widget(arow_right_r_sum)
            self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS[row] = arow_right1_txt
            #
            # add the row to the main GUI:
            CELLS.add_widget(AROW)
        #                                                                                                 'col sums'
        CELLS.add_widget(self.MAKE_C_Sums_Row())
        #
        return CELLS

    def MAKE_C_Sums_Row(self):
        left = .125
        middle = .647
        right = 1 - left - middle
        BOTTOM_ROW = BoxLayout()
        #
        # LEFT SIDE:
        #bottom_left = Label(text="c sums:", size_hint=(left, 1))
        #BOTTOM_ROW.add_widget(bottom_left)

        # MIDDLE:
        bottom_middle = BoxLayout(size_hint=(middle, 1))
        for col in range(4):
            txt = myNumbersOnlyInput(self, "colsum", num=col, size_hint=(.8, 1))
            txt.bind(text=self.entry_TEXT)  # entry_C_SUM)
            txt.bind(focus=self.on_focus)
            bottom_middle.add_widget(txt)
            self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS[col] = txt
        BOTTOM_ROW.add_widget(bottom_middle)

        # RIGHT SIDE (just a blank)
        bottom_right = Label(text="", size_hint=(right, 1))
        #hlayout.add_widget(Label(text="", size_hint=(right, 1)))
        BOTTOM_ROW.add_widget(bottom_right)
        #
        return BOTTOM_ROW


    def reset_sum_colors(self):
        for cell in self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS:
            cell.background_color = NORMAL_COLOR
        for cell in self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS:
            cell.background_color = NORMAL_COLOR
        return

    def hightlight_row_col(self, p_row=None, p_col=None):
        assert p_row is not None or p_col is not None
        # Reset all the colors:
        for row in range(4):
            for col in range(4):
                cell = self.myTextInputs_REMAINING_OPTIONS[row][col]
                cur_color = cell.background_color
                if cur_color != MY_RED:  # [1, 0, 0, 1]:  # "red":
                    cell.background_color = "blanchedalmond"  # NO_FOCUS_COLOR
                else:
                    # What should I be?
                    _joe = 12
        # Now highlight:
        if p_row is not None:
            for cell in self.myTextInputs_REMAINING_OPTIONS[p_row]:
                cur_color = cell.background_color
                if cur_color != MY_RED:  #  [1, 0, 0, 1]:  #"red":
                    cell.background_color = "lightpink"  # HIGHLIGHT_COLOR
                else:
                    # What should I be?
                    _joe = 12
        else:
            for row in self.myTextInputs_REMAINING_OPTIONS:
                cell = row[p_col]
                cur_color = cell.background_color
                if cur_color != MY_RED:  # [1, 0, 0, 1]:  # "red"
                    cell.background_color = "lightpink"  # HIGHLIGHT_COLOR
                else:
                    # What should I be?
                    _joe = 12
        return

    def get_one_of_these(self, row=None, col=None):
        assert not (row is None and col is None)
        if row is not None:
            res = [xx for xx in self.int_CELL_OPTIONS[row] if xx]
        else:
            res = [xx[col] for xx in self.int_CELL_OPTIONS if xx[col]]
        res = list(set(flatten_list(res)))
        return res


    def on_focus(self, instance, value, *largs):  # myInputs
        """ self.int_NUM_EVENS_BY_ROW = [None, None, None, None]
            self.int_NUM_EVENS_BY_COL = [None, None, None, None]
        self.SUM20_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Sum (20)", textbindfn=self.entry_THE_SUM, )
        self.NUM_EVENS_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="# Evens (2)", textbindfn=self.entry_NUM_EVENS)
        self.MUST_HAVE_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Must have", textbindfn=self.entry_MUST_HAVE)
        """
        self.reset_top_boxes(colors_only=True)
        self.reset_sum_colors()
        # if instance in self.THE_TOP_THREE:
        #     # It's one of the top 3 input boxes
        #     if instance.focused:
        #         instance.background_color = HIGHLIGHT_COLOR
        #instance.background_color = HIGHLIGHT_COLOR
        if instance.ANAME == "rowsum":
            instance.background_color = HIGHLIGHT_COLOR
            row = instance.ANUM
            self.hightlight_row_col(p_row=row)
            rowsum = self.int_ROW_SUMS[row]
            if isinstance(rowsum, int):
                self.SET_TEXT(self.SUM20_INPUT, str(rowsum))
            #
            numevens = self.int_NUM_EVENS_BY_ROW[row]
            if isinstance(numevens, int):
                self.SET_TEXT(self.NUM_EVENS_INPUT, str(numevens))
            #
            must_have = self.get_must_have(row=row)  # [xx for xx in self.int_MY_SOLUTION[row] if xx != 0]
            if must_have:
                self.SET_TEXT(self.MUST_HAVE_INPUT, ", ".join(map(str, must_have)))
            #
            # "One of these" is when a cell has its options set, like (1, 3, 5), therefore, any potential
            # option must have at least ONE of those numbers
            #one_of_these = [xx[row] for xx in self.int_CELL_OPTIONS if xx[row]]
            one_of_these = self.get_one_of_these(row=row)  # [xx for xx in self.int_CELL_OPTIONS[row] if xx]
            res = self.populate_potential_solutions_box(thesum=rowsum, numevens=numevens, must_have=must_have, one_of_these=one_of_these)
            pot_sols = res[0]
            solstr = res[1]
            if pot_sols:
                self.find_unique_to_all(pot_sols)
                self.SET_TEXT(self.POTENTIAL_SOLUTIONS, solstr)
        elif instance.ANAME == "colsum":
            instance.background_color = HIGHLIGHT_COLOR
            col = instance.ANUM
            self.hightlight_row_col(p_col=col)
            colsum = self.int_COL_SUMS[col]
            if isinstance(colsum, int):
                self.SET_TEXT(self.SUM20_INPUT, str(colsum))
            #
            numevens = self.int_NUM_EVENS_BY_COL[col]
            if isinstance(numevens, int):
                self.SET_TEXT(self.NUM_EVENS_INPUT, str(numevens))
            #
            #must_have = [yy for xx in self.int_MY_SOLUTION for yy in xx if yy != 0]
            must_have = self.get_must_have(col=col)  #  [xx[col] for xx in self.int_MY_SOLUTION if xx[col] != 0]
            if must_have:
                self.SET_TEXT(self.MUST_HAVE_INPUT, ", ".join(map(str, must_have)))
            #
            # "One of these" is when a cell has its options set, like (1, 3, 5), therefore, any potential
            # option must have at least ONE of those numbers
            one_of_these = self.get_one_of_these(col=col)  #  [xx[col] for xx in self.int_CELL_OPTIONS if xx[col]]
            res = self.populate_potential_solutions_box(thesum=colsum, numevens=numevens, must_have=must_have, one_of_these=one_of_these)
            pot_sols = res[0]
            solstr = res[1]
            if pot_sols:
                self.find_unique_to_all(pot_sols)
                self.SET_TEXT(self.POTENTIAL_SOLUTIONS, solstr)
        else:
            if value is True:
                instance.background_color = HIGHLIGHT_COLOR
        #self.MEGA_POPULATE_OPTIONS()
            return



    def labelled_input(self, GUI_ADD_TO, label:str, textbindfn:Callable=None, readonly=False):
        #
        this_layout = BoxLayout()
        this_layout.add_widget(Label(text=label))
        #
        text_box = myNumbersOnlyInput(self, f"{label}:", readonly=readonly)
        text_box.font = "RobotoMono-Regular.ttf"
        #text_box.font = "Courier New"  # - Regular.ttf
        if callable(textbindfn):
            text_box.bind(text=textbindfn)
        text_box.bind(focus=self.on_focus)
        this_layout.add_widget(text_box)
        GUI_ADD_TO.add_widget(this_layout)
        return text_box


    def MAKE_Sum20_NumEvens_MustHave(self, size_hint=(.25, 1)):
        SUM_EV_MUST = GridLayout(size_hint=size_hint)
        SUM_EV_MUST.cols = 1
        # Accepts input:
        self.SUM20_INPUT = self.labelled_input(GUI_ADD_TO=SUM_EV_MUST, label="Sum (20)", textbindfn=self.entry_THE_SUM)
        self.NUM_EVENS_INPUT = self.labelled_input(GUI_ADD_TO=SUM_EV_MUST, label="# Evens (2)", textbindfn=self.entry_NUM_EVENS)
        self.MUST_HAVE_INPUT = self.labelled_input(GUI_ADD_TO=SUM_EV_MUST, label="Must have", textbindfn=self.entry_MUST_HAVE)
        #
        self.THE_TOP_THREE = [self.SUM20_INPUT, self.NUM_EVENS_INPUT, self.MUST_HAVE_INPUT]
        return SUM_EV_MUST

    def MAKE_Sol_Section(self, size_hint):
        TOP_SECTION = GridLayout(size_hint=size_hint)
        TOP_SECTION.cols = 1

        # # Accepts input:
        # self.SUM20_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Sum (20)", textbindfn=self.entry_THE_SUM)
        # self.NUM_EVENS_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="# Evens (2)", textbindfn=self.entry_NUM_EVENS)
        # self.MUST_HAVE_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Must have", textbindfn=self.entry_MUST_HAVE)
        #
        # self.THE_TOP_THREE = [self.SUM20_INPUT, self.NUM_EVENS_INPUT, self.MUST_HAVE_INPUT]

        # Readonly:
        self.UNIQUE_TO_ALL = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Unique to all", readonly=True)
        self.ALL_SOLUTIONS = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="All Solutions", readonly=True)
        self.POTENTIAL_SOLUTIONS = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Potential Solutions", readonly=True)
        #
        return TOP_SECTION


    def entry_R_POT_SOLS(self, instance, value):
        thesum = int(value)
        if thesum < 13:
            return
        therow = instance.ANUM
        self.int_ROW_SUMS[therow] = int(value)
        numevens = sum([1 for xx in self.buttons_ODD_EVEN[instance.ANUM] if xx.MYTEXT == 'even'])
        musthave = self.get_must_have(row=therow)  # [xx for xx in self.int_MY_SOLUTION[therow] if xx != 0]
        res = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave)
        pot_sols = res[0]
        solstr = res[1]
        if pot_sols:
            self.populate_remaining_options(pot_sols, rownum=therow)
            self.find_unique_to_all(pot_sols)
        self.MEGA_POPULATE_OPTIONS()
        return

    """
    def entry_R_SUM(self, instance, value):
        thesum = int(value)
        if thesum < 13:
            return
        therow = instance.ANUM
        self.int_ROW_SUMS[therow] = int(value)
        numevens = sum([1 for xx in self.buttons_ODD_EVEN[instance.ANUM] if xx.MYTEXT == 'even'])
        musthave = [xx for xx in self.int_MY_SOLUTION[3] if xx != 0]
        pot_sols = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave)
        if pot_sols:
            self.populate_remaining_options(pot_sols, rownum=therow)
        self.MEGA_POPULATE_OPTIONS()
        return
    """
    """
    def entry_C_SUM(self, instance, value):
        thesum = int(value)
        if thesum < 13:
            return
        thecol = instance.ANUM
        self.int_COL_SUMS[thecol] = int(value)
        self.MEGA_POPULATE_OPTIONS(ok=True)
        return
    """

    def reset_top_boxes(self, colors_only):
        self.SUM20_INPUT.background_color = NORMAL_COLOR
        self.NUM_EVENS_INPUT.background_color = NORMAL_COLOR
        self.MUST_HAVE_INPUT.background_color = NORMAL_COLOR
        if colors_only:
            return
        self.SET_TEXT(self.NUM_EVENS_INPUT, "")
        self.SET_TEXT(self.MUST_HAVE_INPUT, "")
        self.SET_TEXT(self.SUM20_INPUT, "")
        self.SET_TEXT(self.UNIQUE_TO_ALL, "")
        self.UNIQUE_TO_ALL.background_color = NO_FOCUS_COLOR
        self.SET_TEXT(self.POTENTIAL_SOLUTIONS, "")
        #
        return


    def MEGA_POPULATE_OPTIONS(self, ok=False):
        #self.reset_top_boxes()
        for row in range(4):
            rowsum = self.int_ROW_SUMS[row]
            if not rowsum: continue
            #self.SET_TEXT(self.SUM20_INPUT, str(rowsum))
            numevens = sum([1 for xx in self.buttons_ODD_EVEN[row] if xx.MYTEXT == 'even'])
            #self.SET_TEXT(self.NUM_EVENS_INPUT, str(numevens))
            must_have = self.get_must_have(row=row)
            #self.SET_TEXT(self.MUST_HAVE_INPUT, ", ".join(map(str, must_have)))
            #
            res = self.populate_potential_solutions_box(thesum=rowsum, numevens=numevens, must_have=must_have, one_of_these=[])
            pot_sols = res[0]
            solstr = res[1]
            if pot_sols:
                self.populate_remaining_options(pot_sols, rownum=row, ok=ok)
                #self.find_unique_to_all(pot_sols)
            _joe = 12
        #
        for col in range(4):
            colsum = self.int_COL_SUMS[col]
            if not colsum: continue
            #self.SET_TEXT(self.SUM20_INPUT, str(colsum))
            numevens = sum([1 for xx in self.buttons_ODD_EVEN if xx[col].MYTEXT == 'even'])
            #self.SET_TEXT(self.NUM_EVENS_INPUT, str(numevens))
            must_have = self.get_must_have(col=col)
            #self.SET_TEXT(self.MUST_HAVE_INPUT, ", ".join(map(str, must_have)))
            #
            res = self.populate_potential_solutions_box(thesum=colsum, numevens=numevens, must_have=must_have, one_of_these=[])
            pot_sols = res[0]
            solstr = res[1]
            if pot_sols:
                self.populate_remaining_options(pot_sols, colnum=col, ok=ok)
                #self.find_unique_to_all(pot_sols)
        #
        # See if there is a cell with only one option left:
        for row in range(4):
            for col in range(4):
                if self.int_MY_SOLUTION[row][col] != 0:
                    self.myTextInputs_REMAINING_OPTIONS[row][col].background_color = NORMAL_COLOR
                else:
                    cell = self.int_CELL_OPTIONS[row][col]
                    if self.int_CELL_OPTIONS[row][col]:
                        if len(self.int_CELL_OPTIONS[row][col]) == 1:
                            self.myTextInputs_REMAINING_OPTIONS[row][col].background_color = [1, 0, 0, 1]  #  "red"
                        elif len(self.int_CELL_OPTIONS[row][col]) == 0:
                            self.myTextInputs_REMAINING_OPTIONS[row][col].background_color = NORMAL_COLOR
        #self.reset_top_boxes()
        return


    @static_vars(ct=0)
    def find_unique_to_all(self, pot_sols, ok=False):
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
            # FIXME: The issue is, why does this update, when 'Sum (20)' and '# Evens (2):' isn't being updated?
            self.SET_TEXT(self.UNIQUE_TO_ALL, unique_str)
            if len(res) == 1:
                self.UNIQUE_TO_ALL.background_color = "red"
        else:
            self.SET_TEXT(self.UNIQUE_TO_ALL, "")
            self.UNIQUE_TO_ALL.background_color = NO_FOCUS_COLOR
        return res


    def populate_remaining_options(self, pot_sols, rownum=None, colnum=None, ok=False):
        """ """
        # -----------------------------------------------------------------------
        def net_out(row, col, these_options):
            cur_opts = self.int_CELL_OPTIONS[row][col]
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
        #self.UNIQUE_TO_ALL.text = unique_str
        self.SET_TEXT(self.UNIQUE_TO_ALL, unique_str)
        pot_sols = list(set(flatten_list(pot_sols)))
        if not rownum is None:
            the_cells = self.myTextInputs_REMAINING_OPTIONS
            the_row = the_cells[rownum]
            odd_evens = self.buttons_ODD_EVEN[rownum]
            for col in range(4):
                sol = self.int_MY_SOLUTION[rownum][col]
                if sol and sol in pot_sols:
                    pot_sols.remove(sol)
            even_pot_sols = [xx for xx in pot_sols if xx in [2, 4, 6, 8]]
            even_pot_sols.sort()
            odd_pot_sols = [xx for xx in pot_sols if xx not in [2, 4, 6, 8]]
            odd_pot_sols.sort()
            for col, cell in enumerate(the_row):
                if self.int_MY_SOLUTION[rownum][col] != 0:
                    # A solved cell has no remaining options
                    self.SET_TEXT(cell, "")
                    #self.int_CELL_OPTIONS[rownum][col] = []  ?
                    continue
                #cur_opts = self.int_CELL_OPTIONS[rownum][col]
                if odd_evens[col].MYTEXT == "even":
                    kk, kkstr = net_out(rownum, col, even_pot_sols)
                    self.int_CELL_OPTIONS[rownum][col] = kk
                    self.SET_TEXT(cell, kkstr)
                else:
                    kk, kkstr = net_out(rownum, col, odd_pot_sols)
                    self.int_CELL_OPTIONS[rownum][col] = kk
                    self.SET_TEXT(cell, kkstr)
        else:
            for row in range(4):
                sol = self.int_MY_SOLUTION[row][colnum]
                if sol and sol in pot_sols:
                    pot_sols.remove(sol)
            even_pot_sols = [xx for xx in pot_sols if xx in [2, 4, 6, 8]]
            even_pot_sols.sort()
            odd_pot_sols = [xx for xx in pot_sols if xx not in [2, 4, 6, 8]]
            odd_pot_sols.sort()
            for row in range(4):
                if self.int_MY_SOLUTION[row][colnum] != 0:
                    # A solved cell has no remaining options
                    self.SET_TEXT(self.myTextInputs_REMAINING_OPTIONS[row][colnum], "")
                    continue
                #cur_opts = self.int_CELL_OPTIONS[row][colnum]
                if self.buttons_ODD_EVEN[row][colnum].MYTEXT == "even":
                    kk, kkstr = net_out(row, colnum, even_pot_sols)
                    self.int_CELL_OPTIONS[row][colnum] = kk
                    self.SET_TEXT(self.myTextInputs_REMAINING_OPTIONS[row][colnum], kkstr)
                else:
                    kk, kkstr = net_out(row, colnum, odd_pot_sols)
                    self.int_CELL_OPTIONS[row][colnum] = kk
                    self.SET_TEXT(self.myTextInputs_REMAINING_OPTIONS[row][colnum], kkstr)
        return



    def entry_A_SOLUTION(self, instance, value):
        # when I enter something into a solution, it then acts as a 'must have' for that row and col
        sol = int(value)
        row = instance.AROW
        col = instance.ACOL
        self.int_MY_SOLUTION[row][col] = sol
        if self.INIT_IS_DONE:
            self.MEGA_POPULATE_OPTIONS(ok=True)
        return



    def populate_potential_solutions_box(self, *, thesum, numevens, must_have, one_of_these):
        if thesum == "" or numevens == "":
            return [], ""
        if thesum is None or numevens is None:
            return [], ""
        if thesum == "None" or numevens == "None":
            return [], ""
        thesum = int(thesum)
        if thesum < 13:
            return [], ""

        if isinstance(must_have, str):
            must_have = list(map(int, must_have.replace(",", "").split()))
        numevens = int(numevens)
        self.SET_TEXT(self.POTENTIAL_SOLUTIONS, "")

        pot_sols = []
        good_sols = []

        if not (thesum in ALL_POTENTIAL_SOLUTIONS and numevens in ALL_POTENTIAL_SOLUTIONS[thesum]):
            return [], ""

        pot_sols = ALL_POTENTIAL_SOLUTIONS[thesum][numevens]
        if not must_have and not one_of_these:
            solstr = ", ".join(map(str, pot_sols))
            self.SET_TEXT(self.POTENTIAL_SOLUTIONS, solstr)
            return pot_sols, solstr
        #
        tmp_sols = []
        if not must_have:
            tmp_sols = pot_sols
        else:
            for a_sol in pot_sols:
                res = all([yy in a_sol for yy in must_have])
                if res:
                    assert a_sol not in tmp_sols
                    tmp_sols.append(a_sol)
        #
        if not one_of_these:
            good_sols = tmp_sols
        else:
            for one_sol in tmp_sols:
                res = any([yy in one_sol for yy in one_of_these])
                if res:
                    assert one_sol not in good_sols
                    good_sols.append(one_sol)
        solstr = ", ".join(map(str, good_sols))
        self.SET_TEXT(self.POTENTIAL_SOLUTIONS, solstr)
        #
        return good_sols, solstr


    def entry_THE_SUM(self, instance, value):
        # this is the one at the very top of the GUI
        thesum = value
        numevens = self.NUM_EVENS_INPUT.text
        musthave = self.MUST_HAVE_INPUT.text
        self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
        return

    def entry_NUM_EVENS(self, instance, value):
        thesum = self.SUM20_INPUT.text
        numevens = value
        musthave = self.MUST_HAVE_INPUT.text
        self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
        _joe = 12  # refresh option cells  self.MEGA_POPULATE_OPTIONS()
        return

    def entry_MUST_HAVE(self, instance, value):
        thesum = self.SUM20_INPUT.text
        numevens = self.NUM_EVENS_INPUT.text
        musthave = value
        self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave, one_of_these=[])
        _joe = 12  # refresh option cells  self.MEGA_POPULATE_OPTIONS()
        return


    def send_keystrokes(self):
        # The row sums:
        self.SET_TEXT(self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS[0], "30")
        # self.SET_TEXT(self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS[1], "25")
        self.SET_TEXT(self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS[2], "13")
        self.SET_TEXT(self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS[3], "29")
        # The column sums:
        # self.SET_TEXT(self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS[0], "26")
        # self.SET_TEXT(self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS[1], "20")
        self.SET_TEXT(self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS[2], "28")
        # self.SET_TEXT(self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS[3], "23")
        # The odd/even buttons:
        for cell in [(0,0), (0,3), (1,0), (1,1), (1,2), (2,2), (3,1)]:
            row, col = cell
            self.buttons_ODD_EVEN[row][col].state = "down"
        # The solutions I know already:
        for row, col, num in [(1, 2, 8),
                              (2, 2, 4),
                              (3, 1, 8)]:
            self.SET_TEXT(self.myTextInputs_MY_SOLUTION_CELLS[row][col], str(num))

        # # The row sums:
        # self.SET_TEXT(self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS[0], "27")
        # self.SET_TEXT(self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS[1], "13")
        # self.SET_TEXT(self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS[2], "13")
        # self.SET_TEXT(self.myNumbersOnlyInput_ROW_SUMS_TEXT_INPUTS[3], "25")
        # # The column sums:
        # self.SET_TEXT(self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS[0], "16")
        # self.SET_TEXT(self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS[1], "14")
        # self.SET_TEXT(self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS[2], "25")
        # self.SET_TEXT(self.myNumbersOnlyInput_COL_SUMS_TEXT_INPUTS[3], "23")
        # # The odd/even buttons:
        # for cell in [(0,3), (1,1), (2,3), (3,1), (3,2), (3,3)]:
        #     row, col = cell
        #     self.buttons_ODD_EVEN[row][col].state = "down"
        # # The solutions I know already:
        # for row, col, num in [(3, 0, 7), (0, 2, 9)]:
        #     self.SET_TEXT(self.myTextInputs_MY_SOLUTION_CELLS[row][col], str(num))  # setting the num 7 does it
        self.INIT_IS_DONE = True
        self.MEGA_POPULATE_OPTIONS()
        self.reset_top_boxes(colors_only=False)
        return

# ----- class myInputs - END   -----------------------------------------------------------------------------------


# ----- class MainApp - START ---------------------------------------------------------------------------------------
class MainApp(App):
    def __init__(self):
        super().__init__()

    def build(self):
        main_layout = myInputs()
        machine = os.environ.get("MACHINE")
        if machine == "PC":
            main_layout.send_keystrokes()
        return main_layout
# ----- class MainApp - END   ---------------------------------------------------------------------------------------


if __name__ == "__main__":
    app = MainApp()
    app.run()
