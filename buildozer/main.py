from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
import re

POTENTIAL_SOLUTIONS = {
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


# ----- class FloatInput - START ------------------------------------------------------------------------------------
class myNumbersOnlyInput(TextInput):
    # To only allow floats (0 - 9 and a single period):
    pat = re.compile('[^0-9]')
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            # To allow a period as well:  s = '.'.join(...same as below)
            s = ''.join(re.sub(pat, '', s) for s in substring.split('.', 1))
        return super().insert_text(s, from_undo=from_undo)
# ----- class FloatInput - END   ------------------------------------------------------------------------------------


# ----- class LoginScreen - START -----------------------------------------------------------------------------------
class myInputs(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1  # Set columns for main layout

        # self.NUM_EVENS_INPUT = TextInput(multiline=False)

        self.inside = GridLayout()
        self.inside.cols = 2  # Set columns for the new grid layout

        # THE SUM:
        self.inside.add_widget(Label(text="Sum:"))
        self.THE_SUM_INPUT = myNumbersOnlyInput(multiline=False)
        self.THE_SUM_INPUT.bind(text=self.THE_SUM_entry)
        self.inside.add_widget(self.THE_SUM_INPUT)

        # THE # OF EVENS:
        self.inside.add_widget(Label(text="# Evens:"))
        self.NUM_EVENS_INPUT = myNumbersOnlyInput(multiline=False)
        self.NUM_EVENS_INPUT.bind(text=self.NUM_EVENS_entry)
        self.inside.add_widget(self.NUM_EVENS_INPUT)

        # 'MUST HAVE' numbers
        self.inside.add_widget(Label(text="Must have:"))
        self.MUST_HAVE_INPUT = TextInput(multiline=False)
        self.MUST_HAVE_INPUT.bind(text=self.MUST_HAVE_entry)
        self.inside.add_widget(self.MUST_HAVE_INPUT)

        # THE POTENTIAL SOLUTIONS:
        self.inside.add_widget(Label(text="Potential Solutions:"))
        self.POTENTIAL_SOLUTIONS = TextInput(multiline=True)
        self.inside.add_widget(self.POTENTIAL_SOLUTIONS)

        # # Add the above GridLayout to the main layout:
        self.add_widget(self.inside)
        #
        # # Create and add a button to the main layout:
        # self.submit = Button(text="Submit", font_size=40)
        # self.add_widget(self.submit)

        #return
    # -----------------------------------------------------------------------

    def popuplate_potential_solutions_box(self, thesum:int, numevens:int, must_have=''):
        if not thesum or not numevens:
            return
        thesum = int(thesum)
        numevens = int(numevens)
        if thesum in POTENTIAL_SOLUTIONS:
            if numevens in POTENTIAL_SOLUTIONS[thesum]:
                pot_sols = POTENTIAL_SOLUTIONS[thesum][numevens]
                self.POTENTIAL_SOLUTIONS.text = ""
                for xx in pot_sols:
                    if must_have:
                        if isinstance(must_have, str):
                            must_have = list(map(int, must_have.split()))
                        res = all([yy in xx for yy in must_have])
                        if res:
                            solstr = ", ".join(map(str, xx))
                            self.POTENTIAL_SOLUTIONS.text += f"{solstr}\n"
                    else:
                        solstr = ", ".join(map(str, xx))
                        self.POTENTIAL_SOLUTIONS.text += f"{solstr}\n"
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
        self.operators = ["/", "*", "+", "-"]
        self.last_was_operator = None
        self.last_button = None
        #main_layout = BoxLayout(orientation="vertical")
        main_layout = myInputs()
        #return main_layout

        #self.solution = TextInput(multiline=False, readonly=True, halign="right", font_size=55)
        #main_layout.add_widget(self.solution)
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
