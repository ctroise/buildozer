from sys import exit
from copy import deepcopy
from itertools import combinations, product
from datetime import datetime


def myjoe():
    _joe = 12  #  this line Needs a breakpoint



puz1 = {"rows": {0: ["eoeo", 26], 1: ["eoee", 17], 2: ["oeeo", 24], 3: ["oooo", 24]},
       "cols": {0: ["eeoo", 12], 1: ["ooeo", 29], 2: ["eeeo", 23], 3: ["oeoo", 27]},
       "solution": {0: "6785", 1: "2546", 2: "1869", 3: "3957"}}
puz2 = {"rows": {0: ["eeoe", 15], 1: ["eoee", 27], 2: ["oeoo", 13], 3: ["eooo", 27]},
        "cols": {0: ["eeoe", 15], 1: ["eoeo", 28], 2: ["oeoo", 23], 3: ["eeoo", 16]},
        "solution": {0: "2814", 1: "4986", 2: "3451", 3: "6795"}}
puz3 = {"rows": {0: ["eeoe", 13], 1: ["oooe", 25], 2: ["ooeo", 15], 3: ["eeoe", 25]},
        "cols": {0: ["eooe", 20], 1: ["eooe", 30], 2: ["ooeo", 13], 3: ["eeoe", 15]},
        "solution": {0: "4612", 1: "9736", 2: "1923", 3: "6874"}}



def flatten_list(alist):
    res = [item for xx in alist for item in xx]
    return res

def get_uniques(alist):
    res = list(set(alist))
    res.sort()
    return res



# ----- class Puzzle - START ----------------------------------------------------------------------------------------
class Puzzle:
    def __str__(self):
        return "Puzzle"

    def LOADFILE(self, filename):
        """ eoeo 26
            eoee 17
            oeeo 24
            oooo 24
            12 29 23 27

            A  for xx in needs.keys():
            B      if needs[xx] is True:
            C          if xx.find("ETrade") != -1:
            D              xx
            --> [ D A B C]   [ xx for xx in needs.keys() if needs[xx] is True if xx.find("ETrade") != -1 ]
        """
        self.filename = filename
        with open(filename, "r") as file:
            all_lines = file.read()
            lines = all_lines.splitlines()

        # First four rows are "eeoo" 'total' info:
        for ct in range(4):
            oddevens, total = lines[ct].split()
            self.rows_oddeven[ct] = oddevens
            self.rows_totals.append(int(total))

        # Then comes one line with the column totals:
        self.cols_totals = list(map(int, lines[4].split()))
        # Given the row 'eoeo' info, create the implied col 'eeoo' info:
        for ct in range(4):
            col = ''.join([val[ct] for val in self.rows_oddeven])
            self.cols_oddeven[ct] = col

        # If there are more rows, then they are the solution: (IF not a blank!)
        if len(lines) > 4 and lines[5] != "":
            self.actual_solution = []
            for ct in range(5, 9):
                line = lines[ct]
                line = list(map(int, line))
                self.actual_solution.append(list(map(int, line)))
        #
        return

    def __init__(self):  # , filename=None):
        self.rows_oddeven = [[], [], [], []]
        self.rows_totals = []
        self.cols_oddeven = [[], [], [], []]
        self.cols_totals = []
        self.actual_solution = None
        #self.LOADFILE(filename)
        self.filename = None
        self.solution = None
        self.grid_options = None
        self.ans_dict = {}
        self.numways = {}
        self.ways_dict = {}
        self.debug = False
        #
        self.potential_solutions = {
            "rows": [[], [], [], []],
            "cols": [[], [], [], []]
        }
        self.solution = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        # Note: Done this way, because to make it multiple copies of "cell" then "a_row (of cells)" would lead to reuse of variable space
        self.grid_options = [
            [[1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9]],
            [[1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9]],
            [[1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9]],
            [[1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9]],
        ]
        #self._initialize_()

    def initialize(self):
        # self._check_grid_()
        res = self._create_dicts_()
        self.ans_dict = res[0]
        self.numways = res[1]
        self.ways_dict = res[2]
        self._create_potential_solutions_()
        self.process_odds_evens()
        self.remove_options()
        return

    def brute_force(self):
        """
        puz1 = {"rows": {0: ["eoeo", 26], 1: ["eoee", 17], 2: ["oeeo", 24], 3: ["oooo", 24]},
                "cols": {0: ["eeoo", 12], 1: ["ooeo", 29], 2: ["eeeo", 23], 3: ["oeoo", 27]},
                "solution": {0: "6785", 1: "2546", 2: "1869", 3: "3957"}}
        """
        # Potential Numbers for each cell"
        potnums = [[[], [], [], []],
                [[], [], [], []],
                [[], [], [], []],
                [[], [], [], []]]
        #
        asol = [[[], [], [], []],
                [[], [], [], []],
                [[], [], [], []],
                [[], [], [], []]]
        #
        # Create what nums could go in which cell, based on "ODD"/"EVEN" status for that cell
        for row, (which, total) in self.DATA["rows"].items():
            for col, oddeven in enumerate(which):
                if oddeven.lower() == 'e':
                    potnums[row][col] = [2, 4, 6, 8]
                else:
                    potnums[row][col] = [1, 3, 5, 7, 9]
        #
        # Now cycle through each combination of potential numbers by rote, and see if I find the answer
        for row in range(4):
            for col in range(4):
                cell = asol[row][col]
        joe = 12


    def how_many_ways(self, total, p_lists):
        lists = [xx for xx in p_lists if xx]
        res = []
        for xx in product(*lists):
            if len(set(xx)) != len(xx):
                continue  # oops, a number repeats!
            ss = sum(xx)
            if ss == total:
                res.append(xx)
            joe = 12
        return res

    # -----------------------------------------------------------------------
    def PRINT_ANSWER(self, filehandle=None):
        # 'filehandle' is an open, active, file to write to
        msgs = []
        msgs.append(f"The solution so far:")
        if type(self) == CLONE:
            if self.guess and filehandle:
                (num, row, col) = self.guess
                msgs.append(f"\t(with guess: Row: {row}, Col: {col}, Num: {num})\n")
        #
        msgs.append("	 0 1 2 3")
        msgs.append("    ---------")
        for ct, row in enumerate(self.solution):
            need = self.rows_totals[ct]
            have = sum([x for x in row])
            missing = need - have
            tmp = ' '.join(str(x) for x in row)
            tmp = tmp.replace('0', '-')
            tmp = tmp.replace('0', '-')
            if missing:
                go = self.grid_options[ct]
                hmw = self.how_many_ways(missing, go)
                msgs.append(f" {ct}  [{tmp}]    missing: {missing}    (ways: {hmw})")
            else:
                msgs.append(f" {ct}  [{tmp}]")
        #
        msgs.append("")
        msgs.append("Column missing:")
        for ct in range(4):
            need = self.cols_totals[ct]
            col = self.get_solution_col(ct)
            have = sum([x for x in col])
            missing = need - have
            if missing:
                go = self.get_col_options(ct)
                hmw = self.how_many_ways(missing, go)
                msgs.append(f"col {ct}  missing: {missing:>2}    (ways: {hmw})")
            else:
                msgs.append(f"col {ct}")
        #
        for msg in msgs:
            print(msg)
            if filehandle:
                filehandle.write(f"{msg}\n")
        return
    # -----------------------------------------------------------------------

    def am_I_done(self) -> bool:
        ct = self.num_solved()
        return bool(ct == 16)

    def num_solved(self):
        ct = 0
        for row in self.solution:
            ct += sum([1 for xx in row if xx != 0])
        return ct

    # def _check_grid_(self):
    #     for ct in range(4):
    #         col = ''.join([val[0][ct] for key, val in self.DATA["rows"].items()])
    #         actual_col = self.DATA["cols"][ct][0]
    #         if col != actual_col:
    #             print(f"For {ct=} the rows and col definitions do not tie out! (exiting)")
    #             exit()
    #     if self.debug:
    #         print(f"\nPuzzle grid is good")
    #     return True

    @staticmethod
    def _create_dicts_():
        ans_dict = {}
        numways = {}
        ways_dict = {}
        perms = combinations([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)
        for perm in perms:
            thesum = sum(perm)
            ct = sum([1 for xx in perm if xx in [2, 4, 6, 8]])
            if thesum not in ans_dict:
                ans_dict[thesum] = {}
            if thesum not in numways:
                numways[thesum] = []
            if ct not in ans_dict[thesum]:
                ans_dict[thesum][ct] = []
            ans_dict[thesum][ct].append(list(perm))
            numways[thesum].append(perm)
        #
        for tot in ans_dict.keys():
            ll = len(numways[tot])
            if ll not in ways_dict:
                ways_dict[ll] = []
            ways_dict[ll].append(tot)
        #
        return ans_dict, numways, ways_dict


    def _create_potential_solutions_(self):
        for ct in range(4):
            numevens = sum([1 for xx in self.rows_oddeven[ct] if xx.lower() == 'e'])
            thesum = self.rows_totals[ct]
            ways = len(self.ans_dict[thesum][numevens])
            for xx in self.ans_dict[thesum][numevens]:
                self.potential_solutions["rows"][ct].append(xx)
        for ct in range(4):
            numevens = sum([1 for xx in self.cols_oddeven[ct] if xx.lower() == 'e'])
            thesum = self.cols_totals[ct]
            ways = len(self.ans_dict[thesum][numevens])
            for xx in self.ans_dict[thesum][numevens]:
                self.potential_solutions["cols"][ct].append(xx)
        for row in range(4):
            ll = len(self.potential_solutions["rows"][row])
            if ll == 1:
                print(f".. Row '{row}' has {ll:2} potential solution")
            else:
                print(f".. Row '{row}' has {ll:2} potential solutions")
        print(f"--------------------------------------------------")
        for col in range(4):
            ll = len(self.potential_solutions["cols"][col])
            if ll == 1:
                print(f".. Col '{col}' has {ll:2} potential solution")
            else:
                print(f".. Col '{col}' has {ll:2} potential solutions")
        print(f"--------------------------------------------------")
        return

    def process_odds_evens(self):
        # Remove evens from any cell that cannot contain an even
        EVENS = [2, 4, 6, 8]
        ODDS = [1, 3, 5, 7, 9]
        # print()
        # print(f"[SETTING BOXES AS ODD/EVEN]")
        for row in range(4):
            #print(f"\trow {row} is: ", end='')
            for col in range(4):
                #val = self.DATA["rows"][row][0][col].lower()  # vals[col]
                val = self.rows_oddeven[row][col].lower()
                assert val in ['e', 'o']
                if val == 'e':
                    self.grid_options[row][col] = [2, 4, 6, 8]
                else:
                    self.grid_options[row][col] = [1, 3, 5, 7, 9]
        return
    def createOptions(self):
        # Make a 4x4 matrix that has 1..9 in each box. Much like Sudoku
        self.solution = [[0, 0, 0, 0],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0]]
        self.grid_options = [[[1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9]],
                        [[1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9]],
                        [[1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9]],
                        [[1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 7, 8, 9]],
                        ]
        return

    def get_unique_options(self, numevens, thesum):
        res = []
        ct = 0
        for ct, solution in enumerate(self.ans_dict[thesum][numevens]):
            res += solution
        res = list(set(res))
        res.sort()
        return ct+1, res

    def remove_options(self):
        # Go through the DATA thing and remove options
        for row in range(4):
            numevens = sum([1 for xx in self.rows_oddeven[row] if xx.lower() == 'e'])
            thesum = self.rows_totals[row]
            ct, good_opts = self.get_unique_options(numevens, thesum)
            remaining_options = get_uniques(flatten_list(self.grid_options[row]))
            if good_opts == remaining_options:
                continue
            for num in remaining_options:
                if not num in good_opts:
                    for col in range(4):
                        if num in self.grid_options[row][col]:
                            self.remove_an_option(num, row, col, f"\t({row}, {col})")
        for col in range(4):
            numevens = sum([1 for xx in self.cols_oddeven[col] if xx.lower() == 'e'])
            thesum = self.cols_totals[col]
            ct, good_opts = self.get_unique_options(numevens, thesum)
            remaining_options = get_uniques(flatten_list(self.get_col_options(col)))
            if good_opts == remaining_options:
                continue
            for num in remaining_options:
                if not num in good_opts:
                    for row in range(4):
                        if num in self.grid_options[row][col]:
                            self.remove_an_option(num, row, col, f"\t({row}, {col})")
        return

    def remove_option_from_this_row_and_col(self, num, row, col):
        # As a number was just placed as a solution, remove it as a potential option
        # for all cells in the same row/col
        for ACOL in range(4):
            if num in self.grid_options[row][ACOL]:
                if ACOL != col:
                    print(f"As '{num}' is the solution for ({row}, {col}), I will remove it as an option from cell ({row}, {ACOL}), removing it")
                self.remove_an_option(num, row, ACOL, None)
        for AROW in range(4):
            if num in self.grid_options[AROW][col]:
                if AROW != row:
                    print(f"As '{num}' is the solution for cell ({row}, {col}), I will remove it as an option from cell ({AROW}, {col})")
                self.remove_an_option(num, AROW, col, None)
        return

    def get_actual_solution(self, row, col):
        return False
        if not self.DATA.get("solution", False):
            return False
        res = self.DATA["solution"][row][col]
        return int(res)

    def remove_an_option(self, num, row, col, reason):
        # Do a sanity check:
        if self.solution[row][col] == 0:
            # Cell hasn't been solved yet, so it still needs options
            act = self.get_actual_solution(row, col)
            if num == act:
                print(f"\n****** You're trying to remove '{num}' from cell ({row}, {col}) when it is the solution for that cell!")
                myjoe()

        self.grid_options[row][col].remove(num)
        #if reason:
        #    print(f"\t{reason}     remaining options: {self.grid_options[row][col]}")  # , end='')
        return

    # -----------------------------------------------------------------------
    def SET_SOLUTION(self, num, row, col, reason, debug=True):
        #
        DEBUG = debug
        #
        if type(self) == Puzzle:
            if self.actual_solution:
                actual = self.actual_solution[row][col]
                if num != actual:
                    myjoe()
        #
        if self.solution[row][col]:
            myjoe()  # HUH? Was already set!
        #
        # -----------------------------------------------------------------------
        # Check if placing this number there would violate a row or column total:
        that_row_sol = self.solution[row]
        row_num_done = sum([1 for xx in that_row_sol if xx!=0])
        row_total = self.rows_totals[row]
        if sum(that_row_sol) + num > row_total:
            myjoe()  # Problem!
        if row_num_done == 3 and sum(that_row_sol) + num != row_total:
            print(f"\t### But I can not place '{num}' in cell ({row}, {col}), because it would not make {that_row_sol} sum to '{row_total}' !")
            myjoe()  # Problem!
        #
        that_col_sol = self.get_solution_col(col)
        col_num_done = sum([1 for xx in that_col_sol if xx != 0])
        col_total = self.cols_totals[col]
        if sum(that_col_sol) + num > col_total:
            myjoe()  # Problem!
        if col_num_done == 3 and sum(that_col_sol) + num != col_total:
            print(f"\t### But I can not place '{num}' in cell ({row}, {col}), because it would not make {that_col_sol} sum to '{col_total}' !")
            # Since this doesn't work, go back and do another guess
            return False

        print(f"-------------------------------------------------------------------------------------------")
        # Officially set this solution:
        if reason:
            print(f"\t[{self}] *** {reason}")
        else:
            myjoe()

        # -----------------------------------------------------------------------
        # Set this cell's solution:
        self.solution[row][col] = num
        # Now there are no remaining options for this cell:
        self.grid_options[row][col] = []
        # This num can't go anywhere else in this row or column:
        self.remove_option_from_this_row_and_col(num, row, col)
        if DEBUG:
            self.PRINT_ANSWER()
        # -----------------------------------------------------------------------

        for rowcheck in range(4):
            thisrow = self.solution[rowcheck]
            if sum([1 for xx in thisrow if xx != 0]) == 4:
                joe = 12  # row solved!
                self.potential_solutions["rows"][rowcheck] = []
                joe = 12
        for colcheck in range(4):
            if sum([1 for xx in self.solution if xx[colcheck] != 0]) == 4:
                joe = 12  # solved!
                self.potential_solutions["cols"][colcheck] = []
                joe = 12

        # --------------------------------------------------------------------------------------------------------------------------
        # If 'num' is the answer for row X, col Y, then any potential solution for row X needs to have 'num' in it,
        # and any potential solution for col Y needs to have a '5' in it. If not, remove that solution as an option for that row/col
        # --------------------------------------------------------------------------------------------------------------------------
        # 1) Rows:
        #self.PRINT_REMAINING_THINGS()
        res = []
        for xx in self.potential_solutions["rows"][row]:
            if num in xx:
                res.append(xx)
            else:
                print(f"As '{num}' is a solution in Row '{row}', {xx} can not be a potential Row '{row}' solution any more as it does not contain '{num}', removing it")
                _joe = 12
        self.potential_solutions["rows"][row] = res

        # 2) Cols:
        #self.PRINT_REMAINING_THINGS()
        res = []
        for xx in self.potential_solutions["cols"][col]:
            if num in xx:
                res.append(xx)
            else:
                print(f"As '{num}' is a solution in Col '{col}', {xx} can not be a potential Col '{col}' solution any more as it does not contain '{num}', removing it")
                _joe = 12
        self.potential_solutions["cols"][col] = res
        #
        print(f"-------------------------------------------------------------------------------------------")
        #self.PRINT_REMAINING_THINGS()
        return True
    # -----------------------------------------------------------------------

    def any_single_options_left(self) -> bool:
        res = any([True for row in self.grid_options for col in row if len(col) == 1])
        return res

    def get_col_options(self, col):
        # get column # 'num' out of grid_options
        res = []
        for row in range(4):
            res.append(self.grid_options[row][col])
        return res

    def any_single_solutions_left(self):
        for arow, acol in product(range(4), range(4)):
            if not self.solution[arow][acol]:
                options_left = self.grid_options[arow][acol]
                if len(options_left) == 1:
                    num = options_left[0]
                    msg = f"(A) Setting '{num}' as the answer to cell ({arow}, {acol}) as it is the only option left"
                    print(msg)  # TODO: Print 'clone' here too, or don't print at all!
                    return self.SET_SOLUTION(num, arow, acol, msg)

        # Rows:  TODO: '6' goes into (0, 1)
        for AROW, arr in enumerate(self.potential_solutions["rows"]):
            if len(arr) == 1:
                single_solution = arr[0]
                #print(f"- There is only a single solution for row '{AROW}', which is: {single_solution}")
                # 1) Ok, there is only one solution left for this row, so remove bad numbers from all cells:
                for acol in range(4):
                    cell = self.grid_options[AROW][acol]
                    for num in cell:
                        if num not in single_solution:
                            print(f"\tx12 {single_solution} is the only remaining solution for Row #{AROW}, so I can remove {num} as an option anywhere in this row, ie cell ({AROW}, {acol})")
                            self.remove_an_option(num, AROW, acol, None)
                            _joe = 12

                # 2) Now, for this 'arow', with one solution 'good_nums', can a certain number from good_nums ONLY go into a certain cell in that arow?
                #    That is, this number may not be the only option for a cell, but it may be the only place it can now go in that row?
                for num in single_solution:
                    thatrow = self.grid_options[AROW]
                    ss = sum([1 for xx in thatrow for yy in xx if yy == num])
                    if ss == 1:
                        # 'num' can only go one place in this 'AROW' - where? Set it
                        for acol in range(4):
                            if num in thatrow[acol]:
                                if not self.solution[AROW][acol]:
                                    print(f"Only solution '{single_solution}' works for row '{AROW}', and of that, '{num}' can only go in cell ({AROW}, {acol})")
                                    msg = f"(4) Setting '{num}' as the answer to cell ({AROW}, {acol})"
                                    return self.SET_SOLUTION(num, AROW, acol, msg)

                # 3) Given one solution for this row, any column that intersects it, can only have solutions that contain at least one of
                #    the same remaining options in that arow
                for acol in range(4):
                    pot_sols = self.potential_solutions["cols"][acol]
                    res = []
                    for one_solution in pot_sols:
                        # See if at least one number from 'single_solution' is in each of the potential solutions
                        if not set(single_solution).isdisjoint(one_solution):
                            res.append(one_solution)  # does this get hit? Is 'isdisjoint' being used properly here?
                    if res:
                        self.potential_solutions["cols"][acol] = res
                joe = 12
        #
        # Cols:
        for ACOL, solution_array in enumerate(self.potential_solutions["cols"]):
            solutions_numbers = get_uniques(flatten_list(solution_array))
            colsol = self.get_solution_col(ACOL)
            for num in range(1, 10):
                if num in colsol:
                    continue
                if all([num in xx for xx in solution_array]):
                    # OK, for all the solutions in column 'ACOL', 'num' is in all of them. So it has to go SOMEWHERE
                    # in this column. See if it can only go in one place:
                    thatcol = self.get_col_options(ACOL)
                    # 'ss' is the number of places 'num' can go:
                    ss = sum([1 for xx in thatcol for yy in xx if yy == num])
                    if ss == 1:
                        # 'num' can only go one place in this 'ACOL' - where? Set it
                        for arow in range(4):
                            if num in thatcol[arow]:
                                if not self.solution[arow][ACOL]:
                                    print(f"In column {ACOL}, there are remaining potential solutions of: {solution_array}")
                                    print(f"'{num}' is in all of them")
                                    print(f"Cell ({arow}, {ACOL}) is the only place with '{num}' as an option for it")
                                    msg = f"(1) Setting '{num}' as the answer to cell ({arow}, {ACOL}), as it is the only place it can go in Col '{ACOL}' (remaining Col '{ACOL}' options: {solutions_numbers}"
                                    print(msg)
                                    return self.SET_SOLUTION(num, arow, ACOL, msg)

        if False:
            for ACOL, arr in enumerate(self.potential_solutions["cols"]):
                remaining_options = get_uniques(flatten_list(arr))
                # 1) For this 'ACOL', with these remaining options, can a certain number ONLY go into a certain cell in that ACOL?
                #    (That is, this number may not be the only option for a cell, but it may be the only place it can now go in that col?)
                for num in remaining_options:
                    thatcol = self.get_col_options(ACOL)
                    #
                    ss = sum([1 for xx in thatcol for yy in xx if yy == num])
                    #
                    if ss == 1:
                        # 'num' can only go one place in this 'ACOL' - where? Set it
                        for arow in range(4):
                            if num in thatcol[arow]:
                                if not self.solution[arow][ACOL]:
                                    # FIXME: *IF* a number is in ALL solutions for a row or col, AND that number can only go in one cell,
                                    #        then put it in that one cell
                                    print(f"\t(11) *** Setting '{num}' as the answer to cell ({arow}, {ACOL}), because of the remaining options {remaining_options}, '{num}' can only go there")
                                    _joe = 12
                                    return self.SET_SOLUTION(num, arow, ACOL, None) # Fixme, trying to set '7' where a '5' has already been placed
        # -----------------------------------------------------------------------
        for ACOL, arr in enumerate(self.potential_solutions["cols"]):
            # 1) For this 'ACOL', with these remaining options, can a certain number ONLY go into a certain cell in that ACOL?
            #    (That is, this number may not be the only option for a cell, but it may be the only place it can now go in that col?)
            if len(arr) == 1:
                single_solution = arr[0]
                # 1) Ok, there is only one solution left for this col, so remove bad numbers from all cells:
                for arow in range(4):
                    cell = self.grid_options[arow][ACOL]
                    for xx in cell:
                        if xx not in single_solution:
                            print(f"As {single_solution} is the only solution for Col #{ACOL}, I can remove {xx} as an option anywhere in this col")
                            self.remove_an_option(xx, arow, ACOL, None)
                # 2) Now, for this 'ACOL', with one solution 'good_nums', can a certain number from good_nums ONLY go into a certain cell in that acol?
                #    That is, this number may not be the only option for a cell, but it may be the only place it can now go in that col?
                if False:
                    for num in single_solution:  # TODO: This is wrong:
                        thatcol = self.get_col_options(ACOL)
                        ss = sum([1 for xx in thatcol for yy in xx if yy == num])
                        if ss == 1:
                            # 'num' can only go one place in this 'ACOL' - where? Set it
                            for arow in range(4):
                                if num in thatcol[arow]:
                                    if not self.solution[arow][ACOL]:
                                        print(f"\t(2) *** Setting '{num}' as the answer to cell ({arow}, {ACOL}), because of the remaining options {remaining_options}, '{num}' can only go there")
                                        return self.SET_SOLUTION(num, arow, ACOL, None)
                # 3) Given one solution for this col, any row that intersects it, can only have solutions that contain at least one of
                #    the same remaining options in that acol
                for arow in range(4):
                    pot_sols = self.potential_solutions["rows"][arow]
                    res = []
                    for one_solution in pot_sols:
                        # See if at least one number from 'single_solution' is in each of the potential solutions
                        if not set(single_solution).isdisjoint(one_solution):
                            res.append(one_solution)  # does this get hit? Is 'isdisjoint' being used properly here?
                    if res:
                        self.potential_solutions["rows"][arow] = res
                joe = 12
        return True

    def get_solution_row(self, row):
        res = self.solution[row]
        return res

    def get_solution_col(self, col):
        res = [xx[col] for xx in self.solution]
        return res

    def check_options_versus_solutions(self):
        # If the remaining options for a row or col, can no longer support a potential solution for that row or col, then remove that solution for it
        for AROW in range(4):
            remaining_options = get_uniques(flatten_list(self.grid_options[AROW]))
            solutions_arr = self.potential_solutions["rows"][AROW]
            ll = len(solutions_arr)
            if ll != 1:  # If there's one solution, you got to work with it
                res = []
                for arr in solutions_arr:
                    FLAG = True
                    for num in arr:
                        if num not in remaining_options:
                            #if num not in self.DATA["rows"][AROW]:
                            if num not in self.solution[AROW]:
                                print(f"R) Removing potential solution {arr} from row '{AROW}' as '{num}' is no longer a potential option anywhere in this row")
                                FLAG = False
                                break
                            else:
                                joe = 12  # Could have been an error!
                                break
                    if FLAG:
                        res.append(arr)
                self.potential_solutions["rows"][AROW] = res
                joe = 12
        #
        for ACOL in range(4):
            remaining_options = get_uniques(flatten_list(self.get_col_options(ACOL)))
            solutions_arr = self.potential_solutions["cols"][ACOL]

            ll = len(solutions_arr)
            if ll != 1:  # If there's one solution, you got to work with it
                res = []
                for arr in solutions_arr:
                    FLAG = True
                    for num in arr:
                        if num not in remaining_options:
                            if num not in self.get_solution_col(ACOL):
                                print(f"(C) Removing potential solution {arr} from col '{ACOL}' as '{num}' is no longer a potential option anywhere in this col")
                                FLAG = False
                                break
                            else:
                                joe = 12  # Could have been an error!
                                break
                    if FLAG:
                        res.append(arr)
                self.potential_solutions["cols"][ACOL] = res
                joe = 12
        return

    # -----------------------------------------------------------------------
    def PRINT_REMAINING_THINGS(self):
        # -----------------------------------------------------------------------
        def getmaxlens(gridoptions):
            asstr = []
            mymax = [3, 3, 3, 3]
            for row in gridoptions:
                for ct, col in enumerate(row):
                    dinge = str(col).replace('[', '').replace(']', '')
                    mymax[ct] = max(mymax[ct], len(dinge))
            return mymax
        # -----------------------------------------------------------------------
        filename = "remaining_things.txt"
        filehandle = open(filename, "w")
        if type(self) == CLONE:
            filehandle.write("CLONE\n")
        dd = datetime.now()
        filehandle.write(f"{dd}\n")

        # Help to carry on doing this puzzle IRL
        for dinge in ["rows", "cols"]:
            filehandle.write("------------------------\n")
            filehandle.write(f"Remaining {dinge.upper()} solutions\n")
            filehandle.write("------------------------\n")
            msg = ''
            for ct, arr in enumerate(self.potential_solutions[dinge]):
                if not arr:
                    filehandle.write(f"{dinge.upper()} #{ct}:  (solved)\n")
                    continue
                for ct2, xx in enumerate(arr):
                    if ct2 == 0:
                        filehandle.write(f"{dinge.upper()} #{ct}:  {xx}\n")
                    else:
                        filehandle.write(f"          {xx}\n")
                # filehandle.write("\n")
            filehandle.write("\n")
        filehandle.write("\n")
        #
        filehandle.write(f"----------------------\n")
        filehandle.write(f"Remaining cell options\n")
        filehandle.write(f"----------------------\n")
        widths = getmaxlens(self.grid_options)
        for row in range(4):
            filehandle.write(f"ROW: {row}:  ")
            msg = ""
            for col in range(4):
                tt = str(self.grid_options[row][col])
                tt = tt.replace('[', '').replace(']', '')
                ww = widths[col]
                msg += f"[{tt:{ww}}]  "
            filehandle.write(f"{msg}")
            filehandle.write("\n")
        filehandle.write("\n")
        filehandle.write("\n")
        self.PRINT_ANSWER(filehandle=filehandle)
        #
        filehandle.close()
        return
    # -----------------------------------------------------------------------
    def SOLVE_IT(self):
        ct = 0
        solvedct = {0: 0}
        res = False
        found_something = True
        while found_something:
            ct += 1
            print(f"\n[{self}]: LOOKING FOR ANY SINGLE SOLUTIONS LEFT [{ct}]")
            if not self.any_single_solutions_left():
                return False
            self.check_options_versus_solutions()
            ns = self.num_solved()
            solvedct[ct] = ns
            if ct > 0:
                found_something = solvedct[ct] != solvedct[ct-1]
            if self.am_I_done():
                return True
        return res
# ----- class Puzzle - END ------------------------------------------------------------------------------------------

# ----- class CLONE - START -----------------------------------------------------------------------------------------
class CLONE(Puzzle):
    def __str__(self):
        return "CLONE"

    def __init__(self, apuzzle):
        self.guess = None
        self.cts = None
        Puzzle().__init__()
        self.orig_puzzle = apuzzle
        self.clonepuzzle(apuzzle)
        self.PRINT_REMAINING_THINGS()
        return

    def clonepuzzle(self, apuzzle):
        self.rows_oddeven = deepcopy(apuzzle.rows_oddeven)
        self.rows_totals = deepcopy(apuzzle.rows_totals)
        self.cols_oddeven = deepcopy(apuzzle.cols_oddeven)
        self.cols_totals = deepcopy(apuzzle.cols_totals)
        self.actual_solution = deepcopy(apuzzle.actual_solution)
        #
        #self.DATA = deepcopy(apuzzle.DATA)
        self.solution = deepcopy(apuzzle.solution)
        self.grid_options = deepcopy(apuzzle.grid_options)
        self.ans_dict = deepcopy(apuzzle.ans_dict)
        self.numways = deepcopy(apuzzle.numways)
        self.ways_dict = deepcopy(apuzzle.ways_dict)
        self.potential_solutions = deepcopy(apuzzle.potential_solutions)
        self.solution = deepcopy(apuzzle.solution)
        self.grid_options = deepcopy(apuzzle.grid_options)
        self.cts = self.count_remaining_cell_options()
        return

    def reset_data(self):
        self.clonepuzzle(self.orig_puzzle)
        self.PRINT_REMAINING_THINGS()
        return

    def remove_an_option(self, num, row, col, reason):
        """ Overwritten function, to remove any sanity checking vs known, correct, answer """
        self.grid_options[row][col].remove(num)
        return

    def count_remaining_cell_options(self):
        cts = {}
        for row, col in product(range(4), range(4)):
            ll = len(self.grid_options[row][col])
            if ll == 0:
                continue
            if ll not in cts:
                cts[ll] = []
            cts[ll].append((row, col))
        octs = {}
        vals = list(cts.keys())
        vals.sort()
        new = {}
        for val in vals:
            new[val] = cts[val]
        return new

    def make_guesses(self):
        for key, cells in self.cts.items():
            for row, col in cells:
                options = self.grid_options[row][col]
                for num in options:
                    #self.PRINT_REMAINING_THINGS()
                    self.guess = (num, row, col)
                    self.SET_SOLUTION(num, row, col, f"Taking a guess '{num}' could work in '({row}, {col})'")
                    # Try to solve this 'new' puzzle:
                    res = self.SOLVE_IT()
                    if self.am_I_done():
                        self.PRINT_REMAINING_THINGS()
                        return True
                    else:
                        self.reset_data()
        return
# ----- class CLONE - END -------------------------------------------------------------------------------------------

def do_evens(p_evens=None, p_sum=None):
    #
    perms = combinations([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)
    EVENS = [2, 4, 6, 8]
    numways = {}
    ways_dict = {}
    ans_dict = {}
    for perm in perms:
        thesum = sum(perm)
        ct = sum([1 for xx in perm if xx in [2, 4, 6, 8]])
        if thesum not in ans_dict:
            ans_dict[thesum] = {}
        if thesum not in numways:
            numways[thesum] = []
        if ct not in ans_dict[thesum]:
            ans_dict[thesum][ct] = []
        ans_dict[thesum][ct].append(perm)
        numways[thesum].append(perm)

    if not (p_evens and p_sum):
        # Create dict:
        for tot in ans_dict.keys():
            ll = len(numways[tot])
            if ll not in ways_dict:
                ways_dict[ll] = []
            ways_dict[ll].append(tot)

        # Print dict:
        printDict(ans_dict)
        exit()

        joe = 12

    else:
        # [2, 4, 6, 8]
        FORMAT = "{0:15} {1:10}"
        print(f"\nSum: {p_sum}: {p_evens} evens, can be formed as follows:")
        lefts = []
        rights = []
        print(FORMAT.format("Evens", "Odds"))
        print("---------------------------")
        for arr in ans_dict[p_sum][p_evens]:
            left = [xx for xx in arr if xx in EVENS]
            lefts += left
            right = [xx for xx in arr if not xx in EVENS]
            rights += right
            msg = f"{left} / {right}"
            # "{0:5}".format(", ".join(map(str, left)))
            ll = ", ".join(map(str, left))
            ll = f"[{ll}]"
            rr = ", ".join(map(str, right))
            msg2 = FORMAT.format(ll, rr)
            #print(msg)
            print(msg2)
        print("---------------------------")
        print(f"Evens: {sorted(list(set(lefts)))}    Odds: {sorted(list(set(rights)))}")
        #print()
    return

def printDict(ans_dict):
    file = open("the_grove.txt", "w")
    file.write(f"TOTAL\tEVENS\t1\t2\t3\t4\t5\t6\t7\t8\t9\n")
    for num, adict in ans_dict.items():
        for evens, arrs in adict.items():
            for arr in arrs:
                msg = f"{num}\t{evens}"
                for xx in range(1, 10):
                    msg += f"\t"
                    if xx in arr:
                        msg += f"{xx}"
                print(msg)
                file.write(f"{msg}\n")
        file.write(f"\n")
    file.close()
    return



if __name__ == '__main__':
    #do_evens()
    #if (2+2)/4 != 1:
    puzzle = Puzzle()
    puzzle.LOADFILE("evens_puzzle.txt")
    puzzle.initialize()
    puzzle_res = puzzle.SOLVE_IT()
    if puzzle_res:
        print("Puzzle was solved!")
        puzzle.PRINT_REMAINING_THINGS()
        exit()

    # Try to solve by making guesses
    clone = CLONE(puzzle)
    clone_res = clone.make_guesses()
    if clone_res:
        print("Puzzle was solved using guesses!")
        clone.PRINT_REMAINING_THINGS()
        exit()
    #
    print("Puzzle was not solved")
