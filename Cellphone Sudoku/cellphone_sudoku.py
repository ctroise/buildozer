from numpy import asarray, fromfile
from itertools import product
import shutil


class Norvig:
    def __init__(self):
        self.nor_digits = "123456789"
        self.nor_rows = "012345678"
        self.nor_cols = "012345678"
        self.nor_squares = self.cross(self.nor_rows, self.nor_cols)
        self.nor_unitlist = ([self.cross(self.nor_rows, c) for c in self.nor_cols] +
                             [self.cross(r, self.nor_cols) for r in self.nor_rows] +
                             [self.cross(rs, cs) for rs in ('012', '345', '678') for cs in
                              ('012', '345', '678')])
        self.nor_units = dict((s, [u for u in self.nor_unitlist if s in u])
                              for s in self.nor_squares)
        # Peers: Basically, the unit list minus the cell itself, and duplications
        self.nor_peers = dict((s, set(sum(self.nor_units[s], [])) - set([s]))
                              for s in self.nor_squares)
        self.sorted_peers = self.create_sorted_peers_matrix()
        self.nor_bigbox = ([self.cross(rs, cs) for rs in ('012', '345', '678') for cs in ('012', '345', '678')])
        self.norvig_answers = {}


    def create_sorted_peers_matrix(self):
        res_arr = [[0] * 9] * 9
        for row, col in product(range(9), repeat=2):
            peers = self.get_peers_sorted((row, col))
            res_arr[row][col] = peers
        return res_arr


    def cross(self, aa, bb):
        return [A+B for A in aa for B in bb]


    def get_peers_sorted(self, cell):
        if len(cell) == 2:
            if isinstance(cell[0], str):
                return sorted(self.nor_peers[cell])
            if isinstance(cell[0], int):
                return sorted(self.nor_peers[str(cell[0]) + str(cell[1])])
        else:
            print(f"What did you pass me? [{cell}]")
            raise KeyError


    def solved(self, values):
        """ A puzzle is solved if each unit is a permutation of the digits 1 to 9. """
        def unitsolved(unit): return set(values[s] for s in unit) == set(self.nor_digits)
        return values is not False and all(unitsolved(unit) for unit in self.nor_unitlist)


    def solve(self, grid, display):
        res = self.parse_grid(grid)
        search_res = self.search(res)
        if search_res is False:
            return False
        if display is True:
            print("\nThe Brute Force Answer:\n")
            self.display(search_res)
        self.norvig_answers = search_res


    def parse_grid(self, grid):
        # Convert grid to a dict of possible values, {square: digits}, or
        # return False if a contradiction is detected.
        # To start, every square can be any digit; then assign values from the grid.
        values = dict((s, self.nor_digits) for s in self.nor_squares)
        for s, d in self.grid_values(grid).items():
            if d in self.nor_digits and not self.assign(values, s, d):
                return False  # (Fail if we can't assign d to square s.)
        return values


    def search(self, values):  # values is a dict
        # Using depth-first search and propagation, try all possible values.
        if values is False:
            return False
        if all(len(values[ss]) == 1 for ss in self.nor_squares):
            return values
        # Chose the unfilled square s with the fewest possibilities
        nn, ss = min((len(values[ss]), ss) for ss in self.nor_squares if len(values[ss]) > 1)
        return self.some(self.search(self.assign(values.copy(), ss, dd)) for dd in values[ss])


    def display(self, values):
        # Display these values as a 2-D grid.
        width = 1+max(len(values[s]) for s in self.nor_squares)
        line = '+'.join(['-'*(width*3)]*3)
        for r in self.nor_rows:
            print(''.join(values[r+c].center(width)+('|' if c in '25' else '')
                           for c in self.nor_cols))
            if r in '25': print(line)
        print()

    def some(self, seq):
        """ Return some element of seq that is true. """
        for ee in seq:
            if ee:
                return ee
        return False


    def assign(self, values, ss, dd):
        # Eliminate all the other values (except d) from values[s] and propagate.
        # Return values, except return False if a contradiction is detected.
        other_values = values[ss].replace(dd, '')
        if all(self.eliminate(values, ss, d2) for d2 in other_values):
            return values  # a dict
        else:
            return False


    def eliminate(self, values, ss, dd):
        # Eliminate d from values[s]; propagate when values or places <= 2.
        # Return values, except return False if a contradiction is detected.
        if dd not in values[ss]:
            return values  # Already eliminated     a dict
        values[ss] = values[ss].replace(dd, '')
        # (1) If a square ss is reduced to one value d2, then eliminate d2 from the peers.
        if len(values[ss]) == 0:
            return False  # Contradiction: removed last value
        elif len(values[ss]) == 1:
            d2 = values[ss]
            if not all(self.eliminate(values, s2, d2) for s2 in self.nor_peers[ss]):
                return False
        # (2) If a unit uu is reduced to only one place for a value dd, then put it there.
        for uu in self.nor_units[ss]:
            dplaces = [ss for ss in uu if dd in values[ss]]
            if len(dplaces) == 0:
                return False  # Contradiction: no place for this value
            elif len(dplaces) == 1:
                # dd can only be in one place in unit; assign it there
                if not self.assign(values, dplaces[0], dd):
                    return False
        return values  # a dict


    def grid_values(self, grid):
        """ Convert grid into a dict of {square: char} with '0' or '.' for empties. """
        chars = [xx for xx in grid if xx in self.nor_digits or xx in '0.']
        return dict(zip(self.nor_squares, chars))


class CellphonePuzzle(Norvig):
    def __init__(self):
        Norvig.__init__(self)
        self.puz_rows = None
        self.puz_cols = None
        self.opt_rows = None
        self.opt_cols = None
        self.the_puzzle_itself = ""


    def norvig_solve(self, line):
        self.solve(line, display=False)
        return

    def puzzle_as_line(self):
        line = ""
        ct = 0
        for row in self.puz_rows:
            for num in row:
                line += str(num)
                if num != 0:
                    ct += 1
        num_to_find = (9*9) - ct
        return line, 81 - num_to_find


    def read_puzzle_file(self):
        filename = "puzzle_out.txt"
        options_file = "options_out.txt"

        with open(filename, "r") as file:
            all_lines = file.read()
            split_lines = all_lines.splitlines()
        if len(split_lines) == 1:
            # From actual excel
            rows = fromfile(filename, dtype=int, count=81, sep=" ").reshape((9, 9))
            cols = rows.T
            # Read the 27x27 puzzle box into "opt_rows" and then create "opt_cols"
        else:
            # Typed in from cellphone
            jj = all_lines.replace("\n", "")
            kk = list(map(int, jj))
            rows = asarray(kk).reshape((9, 9))
            cols = rows.T
            # Now use the default option grid with all #s still good:
            shutil.copyfile("cellphone_options_out.txt", options_file)
        opt_rows = fromfile(options_file, dtype=int, count=729, sep=" ").reshape((9, 9, 9))
        opt_cols = opt_rows.swapaxes(0, 1)  # Transpose a 3 dimensional array

        return rows, cols, opt_rows, opt_cols


    def run_cellphone_cover(self):
        # Read the excel file(s) in
        res = self.read_puzzle_file()
        self.puz_rows = res[0]
        self.puz_cols = res[1]
        self.opt_rows = res[2]
        self.opt_cols = res[3]

        res = self.puzzle_as_line()
        self.the_puzzle_itself = res[0]
        self.norvig_solve(self.the_puzzle_itself)
        # print the answer then exit
        print()
        self.display(self.norvig_answers)
        return


# --------------------------------------------------
# Global variables
# --------------------------------------------------

if __name__ == "__main__":
    cellphone_puz = CellphonePuzzle()
    cellphone_puz.run_cellphone_cover()
