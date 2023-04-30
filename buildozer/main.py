from kivy.app import App
#from kivy.uix.image import Image
#from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
import re

ALL_POTENTIAL_SOLUTIONS = {
  10: {2: [[1,2,3,4]]},

  11: {1: [[1,2,3,5]]},

  12: {2: [[1,2,3,6], [61,2,4,5]]},

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

# ----- class myTextInput - START -----------------------------------------------------------------------------------
class myTextInput(TextInput):
    def __init__(self, row:int, col:int, multiline:bool):
        super().__init__(multiline=multiline)
        self.AROW = row
        self.ACOL = col

    def _on_focus(self, instance, value, *largs):
        WHITE = [1, 1, 1, 1]
        BLACK = [1, 1, 1, 0]
        ib = instance.background_color
        if value:
            if instance.background_color == WHITE:
                instance.background_color = BLACK
            else:
                instance.background_color = WHITE
        else:
            if instance.background_color == WHITE:
                instance.background_color = BLACK
            else:
                instance.background_color = WHITE


    def my_box_press(self, instance):
        #current = self.solution.text
        ODD = [1, 1, 1, 1]
        EVEN = [1, 1, 1, 0]
        if instance.background_color == EVEN:
            instance.background_color = ODD
        else:
            instance.background_color = EVEN
# ----- class myTextInput - END   -----------------------------------------------------------------------------------


# ----- class myTextInput_NEW - START -----------------------------------------------------------------------------------
class myTextInput_NEW(TextInput):
    def __init__(self, row:int, col:int, multiline:bool):
        super().__init__(multiline=multiline)
        self.AROW = row
        self.ACOL = col
# ----- class myTextInput_NEW - END   -----------------------------------------------------------------------------------



# ----- class myNumbersOnlyInput - START ----------------------------------------------------------------------------
class myNumbersOnlyInput(TextInput):
    # To only allow floats (0 - 9 and a single period):
    pat = re.compile('[^0-9]')

    def __init__(self, num=None, multiline=False, halign="center", size_hint=None):
        if size_hint:
            super().__init__(multiline=multiline, halign=halign, size_hint=size_hint)
        else:
            super().__init__(multiline=multiline, halign=halign)

        self.ANUM = num

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            # To allow a period as well:  s = '.'.join(...same as below)
            s = ''.join(re.sub(pat, '', s) for s in substring.split('.', 1))
        return super().insert_text(s, from_undo=from_undo)
# ----- class myNumbersOnlyInput - END   ----------------------------------------------------------------------------





# ----- class myButton - START --------------------------------------------------------------------------------------
class myButton(ToggleButton):
    def __init__(self, **kwargs):
        super(myButton, self).__init__(**kwargs)
        self.source = 'atlas://data/images/defaulttheme/checkbox_off'


    def on_state(self, widget, value):
        text = self.text
        if value == "down":
            #self.source = 'atlas://data/images/defaulttheme/checkbox_on'
            self.text = "even"
        else:
            #self.source = 'atlas://data/images/defaulttheme/checkbox_off'
            self.text = "odd"
# ----- class MyButton - END   --------------------------------------------------------------------------------------




# ----- class LoginScreen - START -----------------------------------------------------------------------------------
class myInputs(GridLayout):
    def __init__(self, **kwargs):
        self.potential_solutions = None

        super().__init__(**kwargs)
        self.cols = 1  # Set columns for main layout

        # self.NUM_EVENS_INPUT = TextInput(multiline=False)

        self.inside = GridLayout()
        self.inside.cols = 2  # Set columns for the new grid layout

        # THE SUM:
        self.inside.add_widget(Label(text="Sum (20):"))
        self.THE_SUM_INPUT = myNumbersOnlyInput()
        self.THE_SUM_INPUT.bind(text=self.THE_SUM_entry)
        self.inside.add_widget(self.THE_SUM_INPUT)

        # THE # OF EVENS:
        self.inside.add_widget(Label(text="# Evens (2):"))
        self.NUM_EVENS_INPUT = myNumbersOnlyInput()
        self.NUM_EVENS_INPUT.bind(text=self.NUM_EVENS_entry)
        self.inside.add_widget(self.NUM_EVENS_INPUT)

        # 'MUST HAVE' numbers
        self.inside.add_widget(Label(text="Must have:"))
        self.MUST_HAVE_INPUT = myNumbersOnlyInput()  # TextInput(multiline=False)
        self.MUST_HAVE_INPUT.bind(text=self.MUST_HAVE_entry)
        self.inside.add_widget(self.MUST_HAVE_INPUT)

        # # Add the above GridLayout to the main layout:
        self.add_widget(self.inside)

        # THE POTENTIAL SOLUTIONS:
        potsol_layout = BoxLayout()
        potsol_layout.add_widget(Label(text="Potential Solutions:"))
        self.POTENTIAL_SOLUTIONS = TextInput(multiline=True)
        potsol_layout.add_widget(self.POTENTIAL_SOLUTIONS)
        self.add_widget(potsol_layout)

        # Add the 4x4 of odd/even
        for row in range(4):
            rowlayout = BoxLayout()
            rowlayout.add_widget(Label(text=str(row), size_hint=(.77, 1)))  # "0", "1", "2", "3"
            for col in range(4):
                button = myButton(text='odd', group=f"oe{row}{col}")  # , size=(100, 100))
                rowlayout.add_widget(button)
            rowlayout.add_widget(Label(text="r sum:", size_hint=(.4, 1)))  # pos_hint={"center_x": 0.5, "center_y": 0.5}))
            txt = TextInput(halign="center")
            rowlayout.add_widget(txt)
            self.add_widget(rowlayout)

        # Add the column sums:
        left = .125
        middle = .647
        right = 1 - left - middle
        BOTTOM_ROW = BoxLayout()
        #
        # LEFT SIDE:
        bottom_left = Label(text="c sums:", size_hint=(left, 1))  # <------      BOTTOM COL SUM BOX
        BOTTOM_ROW.add_widget(bottom_left)

        # MIDDLE:
        bottom_middle = BoxLayout(size_hint=((middle), 1))
        for col in range(4):
            txt = myNumbersOnlyInput(num=col, multiline=False, halign="center", size_hint=(.8, 1))
            txt.bind(text=self.COL_SUM_entry)
            bottom_middle.add_widget(txt)
        BOTTOM_ROW.add_widget(bottom_middle)

        # RIGHT SIDE:
        bottom_right = Label(text="", size_hint=(right, 1))
        #hlayout.add_widget(Label(text="", size_hint=(right, 1)))
        BOTTOM_ROW.add_widget(bottom_right)
        #
        self.add_widget(BOTTOM_ROW)

        # -----------------------------------------------------------------------
        self.operators = ["/", "*", "+", "-"]
        self.last_was_operator = None
        self.last_button = None
        #main_layout = BoxLayout(orientation="vertical")
        #self.solution = TextInput(multiline=False, readonly=True, halign="right", font_size=55)
        #main_layout.add_widget(self.solution)
        """
        for row in range(4):
            row_layout = BoxLayout()
            for col in range(4):
                box = myTextInput(row, col, multiline=False)
                box.bind(text=self.A_BOX_entry)
                box.bind(on_press=self.my_box_press)
                row_layout.add_widget(box)
            self.add_widget(row_layout)
        """
        """
        buttons = [
            ["", "", "", ""],
            ["", "", "", ""],
            ["", "", "", ""],
            ["", "", "", ""],
        ]
        for row in buttons:
            h_layout = BoxLayout()
            for label in row:
                button = Button(text=label, pos_hint={"center_x": 0.5, "center_y": 0.5})
                button.border = (1, 1, 1, 1)
                button.bind(on_press=self.my_button_press)
                h_layout.add_widget(button)
            self.add_widget(h_layout)
        #
        equals_button = Button(text="=", pos_hint={"center_x": 0.5, "center_y": 0.5})
        #equals_button.bind(on_press=self.on_solution)
        self.add_widget(equals_button)
        """
        return
    # -----------------------------------------------------------------------
    def COL_SUM_entry(self, instance, value):
        _joe = 12


    def my_box_press(self, instance):
        #current = self.solution.text
        ODD = [1, 1, 1, 1]
        EVEN = [1, 1, 1, 0]
        if instance.background_color == EVEN:
            instance.background_color = ODD
        else:
            instance.background_color = EVEN

    def my_button_press(self, instance):
        #current = self.solution.text
        button_text = instance.text
        ODD = [1, 1, 1, 1]
        EVEN = [1, 1, 1, 0]
        if not button_text:
            instance.text = "even"
            instance.background_color = EVEN
            instance.border = ODD

        elif button_text == "even":
            instance.text = "odd"
            instance.background_color = ODD
            instance.border = EVEN

        else:
            instance.text = "even"
            instance.background_color = EVEN
            instance.border = ODD

        # if button_text == "C":
        #     # Clear the solution widget
        #     self.solution.text = ""
        # else:
        #     if current and (self.last_was_operator and button_text in self.operators):
        #         # Don't add two operators right after each other
        #         return
        #     elif current == "" and button_text in self.operators:
        #         # First character cannot be an operator
        #         return
        #     else:
        #         new_text = current + button_text
        #         self.solution.text = new_text
        # self.last_button = button_text
        # self.last_was_operator = self.last_button in self.operators
        # #
        return


    def A_BOX_entry(self, instance, value):
        boxtext = instance.text
        row = instance.AROW
        col = instance.ACOL
        joe = 12
        # thesum = value
        # numevens = self.NUM_EVENS_INPUT.text
        # musthave = self.MUST_HAVE_INPUT.text
        # self.popuplate_potential_solutions_box(thesum, numevens, musthave)
        return


    def popuplate_potential_solutions_box(self, thesum:int, numevens:int, must_have=''):
        if not thesum or not numevens:
            return
        thesum = int(thesum)
        numevens = int(numevens)
        if thesum in ALL_POTENTIAL_SOLUTIONS:
            if numevens in ALL_POTENTIAL_SOLUTIONS[thesum]:
                pot_sols = ALL_POTENTIAL_SOLUTIONS[thesum][numevens]
                self.potential_solutions = pot_sols
                self.POTENTIAL_SOLUTIONS.text = ""
                for xx in pot_sols:
                    if must_have:
                        if isinstance(must_have, str):
                            must_have = list(map(int, must_have.split()))
                        res = all([yy in xx for yy in must_have])
                        if res:
                            solstr = ", ".join(map(str, xx))
                            self.POTENTIAL_SOLUTIONS.text += f"[{solstr}]\t"
                    else:
                        solstr = ", ".join(map(str, xx))
                        self.POTENTIAL_SOLUTIONS.text += f"[{solstr}]\t"
        return

    def THE_SUM_entry(self, instance, value):
        thesum = value
        numevens = self.NUM_EVENS_INPUT.text
        musthave = self.MUST_HAVE_INPUT.text
        self.popuplate_potential_solutions_box(thesum, numevens, musthave)
        return

    def NUM_EVENS_entry(self, instance, value):
        thesum = self.THE_SUM_INPUT.text
        numevens = value
        musthave = self.MUST_HAVE_INPUT.text
        self.popuplate_potential_solutions_box(thesum, numevens, musthave)
        return

    def MUST_HAVE_entry(self, instance, value):
        thesum = self.THE_SUM_INPUT.text
        numevens = self.NUM_EVENS_INPUT.text
        musthave = value
        self.popuplate_potential_solutions_box(thesum, numevens, musthave)
        return

# ----- class LoginScreen - END   -----------------------------------------------------------------------------------


# -----------------------------------------------------------------------

# ----- class MainApp - START ---------------------------------------------------------------------------------------
class MainApp(App):
    def __init__(self):
        super().__init__()
        self.cols = None
        self.inside = None
        self.THE_SUM_INPUT = None
        self.NUM_EVENS_INPUT = None
        self.MUST_HAVE_INPUT = None
        self.POTENTIAL_SOLUTIONS = None
        # -----------------------------------------------------------------------
        self.operators = None
        self.last_was_operator = None
        self.last_button = None
        self.solution =  None


    def build(self):
        if (2+2)/4 == 1 :       # MY CODE
            main_layout = myInputs()
            #return main_layout
        else:                   # example code
            self.operators = ["/", "*", "+", "-"]
            self.last_was_operator = None
            self.last_button = None
            main_layout = BoxLayout(orientation="vertical")

            self.solution = TextInput(multiline=False, readonly=True, halign="right", font_size=55)
            main_layout.add_widget(self.solution)
            buttons = [
                ["7", "8", "9", "/"],
                ["4", "5", "6", "*"],
                ["1", "2", "3", "-"],
                [".", "0", "C", "+"],
            ]
            for row in buttons:
                h_layout = BoxLayout()
                for label in row:
                    button = Button(text=label, pos_hint={"center_x": 0.5, "center_y": 0.5})
                    button.bind(on_press=self.on_button_press)
                    h_layout.add_widget(button)
                main_layout.add_widget(h_layout)
            #
            equals_button = Button(text="=", pos_hint={"center_x": 0.5, "center_y": 0.5})
            equals_button.bind(on_press=self.on_solution)
            main_layout.add_widget(equals_button)
            #
        return main_layout



    def on_button_press(self, instance):
        current = self.solution.text
        button_text = instance.text

        if button_text == "C":
            # Clear the solution widget
            self.solution.text = ""
        else:
            if current and (self.last_was_operator and button_text in self.operators):
                # Don't add two operators right after each other
                return
            elif current == "" and button_text in self.operators:
                # First character cannot be an operator
                return
            else:
                new_text = current + button_text
                self.solution.text = new_text
        self.last_button = button_text
        self.last_was_operator = self.last_button in self.operators
        #
        return


    def on_solution(self, instance):
        text = self.solution.text
        if text:
            solution = str(eval(self.solution.text))
            self.solution.text = solution
# ----- class MainApp - END   ---------------------------------------------------------------------------------------


if __name__ == "__main__":
    app = MainApp()
    app.run()
