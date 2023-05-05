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
from utils import NORMAL_COLOR, NO_FOCUS_COLOR, HIGHLIGHT_COLOR, ALL_POTENTIAL_SOLUTIONS
from utils import static_vars, get_sql_today


res = get_sql_today()
TODAY = res[0]
HOUR = int(res[1])


# -------------------------------------------------------------------------------------------------------------------
def flatten_list(alist):
    # only works for one level deep
    res = [item for xx in alist for item in xx]
    return res



# ----- class myTextInput - START -----------------------------------------------------------------------------------
class myTextInput(TextInput):
    def __init__(self, *args, **kwargs):
        self.AROW = args[0]
        self.ACOL = args[1]
        kwargs["halign"] = "center"
        super().__init__(**kwargs)

    def on_focus(self, instance, value, *largs):
        self.reset_top_boxes()
        self.reset_sum_colors()
        instance.background_color = HIGHLIGHT_COLOR
        if instance.ANAME == "rowsum":
            row = instance.ANUM
            self.hightlight_row_col(p_row=row)
            rowsum = self.ROW_SUMS[row]
            self.THE_SUM_INPUT.text = str(rowsum)
            numevens = self.NUM_EVENS_BY_ROW[row]
            self.NUM_EVENS_INPUT.text = str(numevens)
            must_have = [xx for xx in self.MY_SOLUTION[row] if xx != 0]
            if must_have:
                self.MUST_HAVE_INPUT.text = ", ".join(map(str, must_have))
            pot_sols = self.populate_potential_solutions_box(thesum=rowsum, numevens=numevens, must_have=must_have)
            if pot_sols:
                self.find_unique_to_all(pot_sols)
        elif instance.ANAME == "colsum":
            col = instance.ANUM
            self.hightlight_row_col(p_col=col)
            colsum = self.COL_SUMS[col]
            self.THE_SUM_INPUT.text = str(colsum)
            numevens = self.NUM_EVENS_BY_COL[col]
            self.NUM_EVENS_INPUT.text = str(numevens)
            # must_have = [yy for xx in self.MY_SOLUTION for yy in xx if yy != 0]
            must_have = [xx[col] for xx in self.MY_SOLUTION if xx[col] != 0]
            if must_have:
                self.MUST_HAVE_INPUT.text = ", ".join(map(str, must_have))
            pot_sols = self.populate_potential_solutions_box(thesum=colsum, numevens=numevens, must_have=must_have)
            if pot_sols:
                self.find_unique_to_all(pot_sols)
        return
# ----- class myTextInput - END   -----------------------------------------------------------------------------------



# ----- class myNumbersOnlyInput - START ----------------------------------------------------------------------------
class myNumbersOnlyInput(TextInput):
    TAB_NUM = -1
    TAB_ORDER = {}
    TAB_NEXT = None

    def __init__(self, *args, **kwargs):
        self.MYAPP = args[0]
        self.ANAME = args[1]
        self.ANUM = kwargs.get("num", None)
        readonly = kwargs.get("readonly", False)
        kwargs["halign"] = "center"
        kwargs.pop("num", None)
        self.PATTERN = re.compile('[^0-9]')  # To only allow floats (0 - 9 and a single period):
        #
        super().__init__(**kwargs)
        #
        if not readonly:
            myNumbersOnlyInput.TAB_NUM += 1
            self.TAB_NUM = myNumbersOnlyInput.TAB_NUM
            myNumbersOnlyInput.TAB_ORDER[self.TAB_NUM] = self
        else:
            self.TAB_NUM = None
            self.background_color = NO_FOCUS_COLOR
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
            self.text = ""
        elif keycode[1] == "tab":
            # to make this smarter: https://kivy.org/doc/stable/api-kivy.uix.behaviors.focus.html
            INC = 1
            if "shift" in modifiers:
                INC = -1
            which = self.TAB_NUM
            next = (which + INC) % (myNumbersOnlyInput.TAB_NUM+1)
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
            self.text = "even"
            self.MYTEXT = "even"
        else:
            #self.source = 'atlas://data/images/defaulttheme/checkbox_off'
            self.text = "odd"
            self.MYTEXT = "odd"
        self.resum_numevens()
        return

    def resum_numevens(self):
        for row in range(4):
            numevens = sum([1 for xx in self.MYAPP.ODD_EVEN_CELLS[row] if xx.MYTEXT == 'even'])
            self.MYAPP.NUM_EVENS_BY_ROW[row] = numevens
        for col in range(4):
            numevens = 0
            for row in range(4):
                if self.MYAPP.ODD_EVEN_CELLS[row][col].MYTEXT == 'even':
                    numevens += 1
            self.MYAPP.NUM_EVENS_BY_COL[col] = numevens
        return

    def on_release(self):
        for row in range(4):
            numevens = sum([1 for xx in self.MYAPP.ODD_EVEN_CELLS[row] if xx.MYTEXT == 'even'])
            self.MYAPP.NUM_EVENS_BY_ROW[row] = numevens
        for col in range(4):
            numevens = 0
            for row in range(4):
                if self.MYAPP.ODD_EVEN_CELLS[row][col].MYTEXT == 'even':
                    numevens += 1
            self.MYAPP.NUM_EVENS_BY_COL[col] = numevens
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
        #
        self.potential_solutions = None
        self.CELL_OPTIONS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        self.ODD_EVEN_CELLS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        self.POT_SOL_CELLS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        self.MY_SOLUTION_CELLS = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        self.THE_SOLUTION = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        self.MY_SOLUTION = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

        self.NUM_EVENS_BY_ROW = [None, None, None, None]
        self.NUM_EVENS_BY_COL = [None, None, None, None]

        self.ROW_SUMS = [None, None, None, None]
        self.COL_SUMS = [None, None, None, None]
        self.ROW_SUMS_TEXT_INPUTS = [None, None, None, None]
        self.COL_SUMS_TEXT_INPUTS = [None, None, None, None]
        self.ROW_POT_SOLS = [None, None, None, None]
        self.ROW_POT_SOLS_TEXT_INPUTS = [None, None, None, None]


class myInputs(myVariables, GridLayout):
    def __init__(self, **kwargs):
        myVariables.__init__(self)
        GridLayout.__init__(self, **kwargs)
        self.cols = 1
        #
        self.CREATE_THE_GUI()
        #
        if HOUR > 14:
            self.cycle_me(self.canvas)
        return


    def CREATE_THE_GUI(self):
        #
        self.add_widget(self.MAKE_Top_Section(size_hint=(0.5, 1)))
        #
        self.add_widget(self.MAKE_Odd_Even_Cells())
        #
        self.add_widget(self.MAKE_Remaining_Options())
        #
        self.add_widget(self.MAKE_Solutions())
        #
        return

    def entry_TEXT(self, instance, value):
        if instance.ANAME == "rowsum":
            thesum = int(value)
            if thesum < 13:
                return
            therow = instance.ANUM
            self.ROW_SUMS[therow] = int(value)
            numevens = sum([1 for xx in self.ODD_EVEN_CELLS[instance.ANUM] if xx.MYTEXT == 'even'])
            musthave = [xx for xx in self.MY_SOLUTION[3] if xx != 0]
            pot_sols = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave)
            if pot_sols:
                self.populate_remaining_options(pot_sols, rownum=therow)
            self.MEGA_POPULATE_OPTIONS()
        elif instance.ANAME == "colsum":
            thesum = int(value)
            if thesum < 13:
                return
            thecol = instance.ANUM
            self.COL_SUMS[thecol] = int(value)
            self.MEGA_POPULATE_OPTIONS(ok=True)
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


    def send_keystrokes(self):
        # The row sums:
        self.ROW_SUMS_TEXT_INPUTS[0].text = "27"
        self.ROW_SUMS_TEXT_INPUTS[1].text = "13"
        self.ROW_SUMS_TEXT_INPUTS[2].text = "13"
        self.ROW_SUMS_TEXT_INPUTS[3].text = "25"  # unique to all: 6, 8
        # The column sums:
        self.COL_SUMS_TEXT_INPUTS[0].text = "16"
        self.COL_SUMS_TEXT_INPUTS[1].text = "14"
        self.COL_SUMS_TEXT_INPUTS[2].text = "25"
        self.COL_SUMS_TEXT_INPUTS[3].text = "23"        #
        # The odd/even buttons:
        for cell in [(0,3), (1,1), (2,3), (3,1), (3,2), (3,3)]:
            row, col = cell
            self.ODD_EVEN_CELLS[row][col].state = "down"
        # The solutions I know already:
        for row, col, num in [(3, 0, 7), (0, 2, 9)]:
            self.MY_SOLUTION_CELLS[row][col].text = str(num)
        #self.MEGA_POPULATE_OPTIONS()
        self.INIT_IS_DONE = True
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



    def MAKE_Remaining_Options(self):
        OPTIONS = GridLayout()
        OPTIONS.cols = 1
        OPTIONS.add_widget(Label(text="REMAINING OPTIONS:"))
        for row in range(4):
            row_layout = BoxLayout()
            for col in range(4):
                box = myTextInput(row, col, multiline=True, readonly=True, is_focusable=False)
                self.POT_SOL_CELLS[row][col] = box
                row_layout.add_widget(box)
            OPTIONS.add_widget(row_layout)
        return OPTIONS


    def MAKE_Solutions(self):
        SOLUTIONS = GridLayout()
        SOLUTIONS.cols = 1
        #
        SOLUTIONS.add_widget(Label(text="MY SOLUTION:"))
        #
        for row in range(4):
            row_layout = BoxLayout()
            for col in range(4):
                box = myTextInput(row, col, multiline=True)
                self.MY_SOLUTION_CELLS[row][col] = box
                box.bind(text=self.entry_A_SOLUTION)
                box.bind(focus=self.on_focus)
                row_layout.add_widget(box)
            SOLUTIONS.add_widget(row_layout)
        return SOLUTIONS


    def MAKE_Odd_Even_Cells(self):
        # The 4x4 of odd/even cells
        CELLS = GridLayout()
        CELLS.cols = 1
        #
        left = .125
        middle = .647
        right = 1 - left - middle
        for row in range(4):
            AROW = BoxLayout()

            # left side ('0'/'1'/'2'/'3')
            AROW.add_widget(Label(text=str(row), size_hint=(left, 1)))

            # MIDDLE:  (this is the main chunk of this section)
            arow_middle = BoxLayout(size_hint=(middle, 1))
            #
            for col in range(4):
                acell = myButton(app=self, text='odd', group=f"oe{row}{col}", row=row, col=col)         # odd/even
                self.ODD_EVEN_CELLS[row][col] = acell
                arow_middle.add_widget(acell)
            AROW.add_widget(arow_middle)

            # right R SUM:
            arow_right_r_sum = BoxLayout(size_hint=(right, 1))
            #
            arow_right_r_sum.add_widget(Label(text="r sum:"))
            arow_right1_txt = myNumbersOnlyInput(self, "rowsum", num=row)
            arow_right1_txt.bind(text=self.entry_TEXT)  # entry_R_SUM)                                  # 'r sum'
            arow_right1_txt.bind(focus=self.on_focus)
            arow_right_r_sum.add_widget(arow_right1_txt)
            AROW.add_widget(arow_right_r_sum)
            self.ROW_SUMS_TEXT_INPUTS[row] = arow_right1_txt
            #
            # add the row to the main GUI:
            CELLS.add_widget(AROW)
        #                                                                                                 'col sums'
        CELLS.add_widget(self.MAKE_C_Sums_Row())
        #
        return CELLS

    def reset_sum_colors(self):
        for cell in self.ROW_SUMS_TEXT_INPUTS:
            cell.background_color = NORMAL_COLOR
        for cell in self.COL_SUMS_TEXT_INPUTS:
            cell.background_color = NORMAL_COLOR
        return

    def hightlight_row_col(self, p_row=None, p_col=None):
        assert p_row is not None or p_col is not None
        # Reset all the colors:
        for rr in range(4):
            for cc in range(4):
                self.POT_SOL_CELLS[rr][cc].background_color = NO_FOCUS_COLOR
        # Now highlight:
        if p_row is not None:
            for cell in self.POT_SOL_CELLS[p_row]:
                cell.background_color = HIGHLIGHT_COLOR
        else:
            for row in self.POT_SOL_CELLS:
                row[p_col].background_color = HIGHLIGHT_COLOR
        return


    def on_focus(self, instance, value, *largs):
        """ self.NUM_EVENS_BY_ROW = [None, None, None, None]
            self.NUM_EVENS_BY_COL = [None, None, None, None]
        self.SUM20_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Sum (20):", textbindfn=self.entry_THE_SUM, )
        self.NUM_EVENS_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="# Evens (2):", textbindfn=self.entry_NUM_EVENS)
        self.MUST_HAVE_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Must have:", textbindfn=self.entry_MUST_HAVE)
        """
        self.reset_top_boxes()
        self.reset_sum_colors()
        # if instance in self.THE_TOP_THREE:
        #     # It's one of the top 3 input boxes
        #     if instance.focused:
        #         instance.background_color = HIGHLIGHT_COLOR
        instance.background_color = HIGHLIGHT_COLOR
        if instance.ANAME == "rowsum":
            row = instance.ANUM
            self.hightlight_row_col(p_row=row)
            rowsum = self.ROW_SUMS[row]
            self.SUM20_INPUT.text = str(rowsum)
            numevens = self.NUM_EVENS_BY_ROW[row]
            self.NUM_EVENS_INPUT.text = str(numevens)
            must_have = [xx for xx in self.MY_SOLUTION[row] if xx != 0]
            if must_have:
                self.MUST_HAVE_INPUT.text = ", ".join(map(str, must_have))
            pot_sols = self.populate_potential_solutions_box(thesum=rowsum, numevens=numevens, must_have=must_have)
            if pot_sols:
                self.find_unique_to_all(pot_sols)
        elif instance.ANAME == "colsum":
            col = instance.ANUM
            self.hightlight_row_col(p_col=col)
            colsum = self.COL_SUMS[col]
            self.SUM20_INPUT.text = str(colsum)
            numevens = self.NUM_EVENS_BY_COL[col]
            self.NUM_EVENS_INPUT.text = str(numevens)
            #must_have = [yy for xx in self.MY_SOLUTION for yy in xx if yy != 0]
            must_have = [xx[col] for xx in self.MY_SOLUTION if xx[col] != 0]
            if must_have:
                self.MUST_HAVE_INPUT.text = ", ".join(map(str, must_have))
            pot_sols = self.populate_potential_solutions_box(thesum=colsum, numevens=numevens, must_have=must_have)
            if pot_sols:
                self.find_unique_to_all(pot_sols)
        return



    def MAKE_C_Sums_Row(self):
        left = .125
        middle = .647
        right = 1 - left - middle
        BOTTOM_ROW = BoxLayout()
        #
        # LEFT SIDE:
        bottom_left = Label(text="c sums:", size_hint=(left, 1))
        BOTTOM_ROW.add_widget(bottom_left)

        # MIDDLE:
        bottom_middle = BoxLayout(size_hint=(middle, 1))
        for col in range(4):
            txt = myNumbersOnlyInput(self, "colsum", num=col, size_hint=(.8, 1))
            txt.bind(text=self.entry_TEXT)  # entry_C_SUM)
            txt.bind(focus=self.on_focus)
            bottom_middle.add_widget(txt)
            self.COL_SUMS_TEXT_INPUTS[col] = txt
        BOTTOM_ROW.add_widget(bottom_middle)

        # RIGHT SIDE (just a blank)
        bottom_right = Label(text="", size_hint=(right, 1))
        #hlayout.add_widget(Label(text="", size_hint=(right, 1)))
        BOTTOM_ROW.add_widget(bottom_right)
        #
        return BOTTOM_ROW



    def labelled_input(self, GUI_ADD_TO, label:str, textbindfn:Callable=None, readonly=False):
        #
        this_layout = BoxLayout()
        this_layout.add_widget(Label(text=label))
        #
        text_box = myNumbersOnlyInput(self, label, readonly=readonly)
        text_box.font = "RobotoMono-Regular.ttf"
        #text_box.font = "Courier New"  # - Regular.ttf
        if callable(textbindfn):
            text_box.bind(text=textbindfn)
        text_box.bind(focus=self.on_focus)
        this_layout.add_widget(text_box)
        GUI_ADD_TO.add_widget(this_layout)
        return text_box


    def MAKE_Top_Section(self, size_hint):
        TOP_SECTION = GridLayout(size_hint=size_hint)  # (0.5, 1))
        TOP_SECTION.cols = 1

        # Accepts input:
        self.SUM20_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Sum (20):", textbindfn=self.entry_THE_SUM)
        self.NUM_EVENS_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="# Evens (2):", textbindfn=self.entry_NUM_EVENS)
        self.MUST_HAVE_INPUT = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Must have:", textbindfn=self.entry_MUST_HAVE)

        self.THE_TOP_THREE = [self.SUM20_INPUT, self.NUM_EVENS_INPUT, self.MUST_HAVE_INPUT]

        # Readonly:
        self.UNIQUE_TO_ALL = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="# Unique to all:", readonly=True)
        self.POTENTIAL_SOLUTIONS = self.labelled_input(GUI_ADD_TO=TOP_SECTION, label="Potential Solutions:", readonly=True)
        #
        return TOP_SECTION


    def entry_R_POT_SOLS(self, instance, value):
        thesum = int(value)
        if thesum < 13:
            return
        therow = instance.ANUM
        self.ROW_SUMS[therow] = int(value)
        numevens = sum([1 for xx in self.ODD_EVEN_CELLS[instance.ANUM] if xx.MYTEXT == 'even'])
        musthave = [xx for xx in self.MY_SOLUTION[3] if xx != 0]
        pot_sols = self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave)
        if pot_sols:
            self.populate_remaining_options(pot_sols, rownum=therow)
        self.MEGA_POPULATE_OPTIONS()
        return

    """
    def entry_R_SUM(self, instance, value):
        thesum = int(value)
        if thesum < 13:
            return
        therow = instance.ANUM
        self.ROW_SUMS[therow] = int(value)
        numevens = sum([1 for xx in self.ODD_EVEN_CELLS[instance.ANUM] if xx.MYTEXT == 'even'])
        musthave = [xx for xx in self.MY_SOLUTION[3] if xx != 0]
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
        self.COL_SUMS[thecol] = int(value)
        self.MEGA_POPULATE_OPTIONS(ok=True)
        return
    """

    def reset_top_boxes(self):
        self.NUM_EVENS_INPUT.text = ""
        self.MUST_HAVE_INPUT.text = ""
        self.SUM20_INPUT.text = ""
        self.UNIQUE_TO_ALL.text = ""
        self.UNIQUE_TO_ALL.background_color = NO_FOCUS_COLOR
        self.POTENTIAL_SOLUTIONS.text = ""
        #
        self.SUM20_INPUT.background_color = NORMAL_COLOR
        self.NUM_EVENS_INPUT.background_color = NORMAL_COLOR
        self.MUST_HAVE_INPUT.background_color = NORMAL_COLOR
        #
        return


    def MEGA_POPULATE_OPTIONS(self, ok=False):
        #self.reset_top_boxes()
        for row in range(4):
            rowsum = self.ROW_SUMS[row]
            if not rowsum:
                continue
            numevens = sum([1 for xx in self.ODD_EVEN_CELLS[row] if xx.MYTEXT == 'even'])
            must_have = [xx for xx in self.MY_SOLUTION[row] if xx != 0]
            pot_sols = self.populate_potential_solutions_box(thesum=rowsum, numevens=numevens, must_have=must_have)
            if pot_sols:
                self.populate_remaining_options(pot_sols, rownum=row, ok=ok)
            _joe = 12
        #
        for col in range(4):
            colsum = self.COL_SUMS[col]
            if not colsum:
                continue
            numevens = sum([1 for xx in self.ODD_EVEN_CELLS for yy in xx if yy.MYTEXT=='even'])
            must_have = [yy for xx in self.MY_SOLUTION for yy in xx if yy != 0]
            pot_sols = self.populate_potential_solutions_box(thesum=colsum, numevens=numevens, must_have=must_have)
            if pot_sols:
                self.populate_remaining_options(pot_sols, colnum=col, ok=ok)
        #
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
            return
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
            self.UNIQUE_TO_ALL.text = unique_str
            if len(res) == 1:
                self.UNIQUE_TO_ALL.background_color = "red"
        else:
            self.UNIQUE_TO_ALL.text = ""
            self.UNIQUE_TO_ALL.background_color = NO_FOCUS_COLOR
        return res


    def populate_remaining_options(self, pot_sols, rownum=None, colnum=None, ok=False):
        # -----------------------------------------------------------------------
        def net_out(aa, bb):
            opts = None
            if not aa:
                opts = bb
            else:
                opts = [xx for xx in aa if xx in bb]
            res = ", ".join([str(xx) for xx in opts])
            return opts, res
        # -----------------------------------------------------------------------
        assert rownum is not None or colnum is not None
        unique_to_all = self.find_unique_to_all(pot_sols, ok=ok)
        # unique_str = ""
        # if unique_to_all:
        #     unique_str = ", ".join([str(xx) for xx in unique_to_all])
        # self.UNIQUE_TO_ALL.text = unique_str
        pot_sols = list(set(flatten_list(pot_sols)))
        if not rownum is None:
            the_cells = self.POT_SOL_CELLS
            the_row = the_cells[rownum]
            odd_evens = self.ODD_EVEN_CELLS[rownum]
            for col in range(4):
                sol = self.MY_SOLUTION[rownum][col]
                if sol and sol in pot_sols:
                    pot_sols.remove(sol)
            even_pot_sols = [xx for xx in pot_sols if xx in [2, 4, 6, 8]]
            odd_pot_sols = [xx for xx in pot_sols if xx not in [2, 4, 6, 8]]
            for col, cell in enumerate(the_row):
                if self.MY_SOLUTION[rownum][col] != 0:
                    # A solved cell has no remaining options
                    cell.text = ""
                    continue
                cur_opts = self.CELL_OPTIONS[rownum][col]  # cell.text
                if odd_evens[col].MYTEXT == "even":
                    kk, kkstr = net_out(cur_opts, even_pot_sols)
                    self.CELL_OPTIONS[rownum][col] = kk
                    cell.text = kkstr
                else:
                    kk, kkstr = net_out(cur_opts, odd_pot_sols)
                    self.CELL_OPTIONS[rownum][col] = kk
                    cell.text = kkstr
        else:
            for row in range(4):
                sol = self.MY_SOLUTION[row][colnum]
                if sol and sol in pot_sols:
                    pot_sols.remove(sol)
            even_pot_sols = [xx for xx in pot_sols if xx in [2, 4, 6, 8]]
            odd_pot_sols = [xx for xx in pot_sols if xx not in [2, 4, 6, 8]]
            for row in range(4):
                if self.MY_SOLUTION[row][colnum] != 0:
                    # A solved cell has no remaining options
                    self.POT_SOL_CELLS[row][colnum].text = ""
                    continue
                cur_opts = self.CELL_OPTIONS[row][colnum]
                if self.ODD_EVEN_CELLS[row][colnum].MYTEXT == "even":
                    kk, kkstr = net_out(cur_opts, even_pot_sols)
                    self.CELL_OPTIONS[row][colnum] = kk
                    self.POT_SOL_CELLS[row][colnum].text = kkstr
                else:
                    kk, kkstr = net_out(cur_opts, odd_pot_sols)
                    self.CELL_OPTIONS[row][colnum] = kk
                    self.POT_SOL_CELLS[row][colnum].text = kkstr
        return



    def entry_A_SOLUTION(self, instance, value):
        # when I enter something into a solution, it then acts as a 'must have' for that row and col
        sol = int(value)
        row = instance.AROW
        col = instance.ACOL
        self.MY_SOLUTION[row][col] = sol
        self.MEGA_POPULATE_OPTIONS(ok=True)
        return



    def populate_potential_solutions_box(self, *, thesum, numevens, must_have=''):
        if thesum == "" or numevens == "" or thesum is None or numevens is None:
            return
        thesum = int(thesum)
        if thesum < 13:
            return
        numevens = int(numevens)
        pot_sols = None
        self.POTENTIAL_SOLUTIONS.text = ""
        if thesum in ALL_POTENTIAL_SOLUTIONS:
            if numevens in ALL_POTENTIAL_SOLUTIONS[thesum]:
                pot_sols = ALL_POTENTIAL_SOLUTIONS[thesum][numevens]
                self.potential_solutions = pot_sols
                #self.POTENTIAL_SOLUTIONS.text = ""
                for xx in pot_sols:
                    if must_have:
                        if isinstance(must_have, str):
                            must_have = list(map(int, must_have.replace(",", "").split()))
                        res = all([yy in xx for yy in must_have])
                        if res:
                            solstr = ", ".join(map(str, xx))
                            self.POTENTIAL_SOLUTIONS.text += f"[{solstr}]\t"
                    else:
                        solstr = ", ".join(map(str, xx))
                        self.POTENTIAL_SOLUTIONS.text += f"[{solstr}]\t"
        return pot_sols

    def entry_THE_SUM(self, instance, value):
        # this is the one at the very top of the GUI
        thesum = value
        numevens = self.NUM_EVENS_INPUT.text
        musthave = self.MUST_HAVE_INPUT.text
        self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave)
        return

    def entry_NUM_EVENS(self, instance, value):
        thesum = self.SUM20_INPUT.text
        numevens = value
        musthave = self.MUST_HAVE_INPUT.text
        self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave)
        _joe = 12  # refresh option cells  self.MEGA_POPULATE_OPTIONS()
        return

    def entry_MUST_HAVE(self, instance, value):
        thesum = self.SUM20_INPUT.text
        numevens = self.NUM_EVENS_INPUT.text
        musthave = value
        self.populate_potential_solutions_box(thesum=thesum, numevens=numevens, must_have=musthave)
        _joe = 12  # refresh option cells  self.MEGA_POPULATE_OPTIONS()
        return
# ----- class LoginScreen - END   -----------------------------------------------------------------------------------


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
