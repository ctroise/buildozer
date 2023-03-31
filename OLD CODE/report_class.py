import datetime
import re
import variables
from needs_no_imports import myjoe


class Report:
    def __str__(self):
        return f"'{self.name}' Report"

    def __add__(self, nextItem):
        self.add(nextItem)

    def __init__(self, name, line="", formatter="", topTitle="", titlebar_formatter=""):
        self.name = name
        self.text = []
        self.block_start = 0
        self.block_end = 9999
        self.blocks = {}
        self.blocksByName = {}
        self.blocksWhere = {}  # Which line in the report Block X should be added/inserted
        self.block_list = {}
        self.header = None
        self.textStart = 0
        self.separators = {}
        self.print_version = ""  # what will ultimately get printed out
        self.max_len = 0
        self.formatter = re_format(formatter)  # Don't touch this with 'expand_a_formatter'
        self.groups = {}
        self.widths = {}
        if topTitle:
            self.makeTopTitle(topTitle)  # The title plus timestamp that goes right up top
        self.addBlock(MakeTODOList(name))
        #
        self.numTitleFields = 0
        self.titlebar_formatter, self.titlebar_formatter2, self.dots_formatted, self.crosses_formatted, self.crossedFormatter = "", "", "", "", ""
        self.process_formatter(formatter=self.formatter, titlebar_formatter=titlebar_formatter)
        #
        if line:
            self.__add__(line)


    def addFootnote(self, line):
        """ Like 'add()', but do not increment max_len
        """
        self.addString(line, noMaxLen=True)


    def checkWidths(self, items, titlebar=False):
        myjoe("")  # does this get hit anymore?       2022-09-23
        badWidths = []
        if len(items) != len(self.widths):
            print(f"\n\t*** You're trying to print #{len(items)} field(s) when the formatter has #{len(self.widths)}!\n")
            raise UserWarning
        for ct in range(len(items)):
            if isinstance(items[ct], str):
                # Check width is ok
                if len(items[ct]) > self.widths[ct]:
                    badWidths.append(f"Column #{ct}: [{items[ct]}], needs a size of: {len(items[ct])}")
                if not titlebar:
                    # Check it's not trying to go into a numeric format
                    if self.groups[ct].find("f") != -1 or self.groups[ct].find("d") != -1:
                        print(f"\n\t*** Field #{ct} is a string: '{items[ct]}' but the format for it is numeric: [{self.groups[ct]}]!\n")
                        raise UserWarning
            if isinstance(items[ct], float) or isinstance(items[ct], int):
                # Check post-format width is ok
                tmp = self.groups[ct].format(items[ct])
                if len(tmp) > self.widths[ct]:
                    badWidths.append(f"Column #{ct}: [{tmp}], needs a size of: {len(tmp)}")
        if badWidths:
            print(f"\nField width problems:")
            for xx in badWidths:
                print(f"\t{xx}")
            print(); myjoe()
            raise UserWarning


    def process_formatter(self, formatter="", titlebar_formatter=""):
        if titlebar_formatter:
            # Title bar format given, use it!
            self.dots_formatted, self.titlebar_formatter = self.dots_and_titlebar_formatters(titlebar_formatter, "both")
        elif formatter:
            self.formatter = re_format(formatter)
            self.dots_formatted, self.titlebar_formatter = self.dots_and_titlebar_formatters(self.formatter, "both")
        myjoe()


    def dots_and_titlebar_formatters(self, formatter, which=None):
        """ - Take a f"" formatter and expand what it will look like when used.
              This way I can see what it will look like when it prints.
            - Also create a f"" format for the "title bar" that will accept all strings as inputs
            - This method is also in utils.py
            - This should not be used with the main, regular, formatting!
        """
        if formatter == '':  # does this get hit anymore? 2022-09-17
            return ''
        if formatter.find("§") != -1:
            formatter = re_format(formatter)

        numbers = [x for x in "1234567890"]
        expanded_formatter = [x for x in formatter]
        group_ct = sum([1 for xx in expanded_formatter if xx == "}"])
        take = True
        need_a_colon = False
        width_str = ""

        # Peel out the individual format groups
        group_ct = 0
        tmp = formatter  # str.rstrip(formatter)
        while tmp:
            while tmp[0] != "{":
                tmp = tmp[1:]
            pos = tmp.find("}")
            # turn the '#:..' into '0':..!
            self.groups[group_ct] = re.sub('{.*:', '{0:', tmp[:pos+1])
            tmp = tmp[pos+1:]
            group_ct += 1
            if tmp.find("}") == -1:
                tmp = ''

        title_formatter = ""
        self.titlebar_formatter2 = ""
        # -------------------------------------------
        # First, just do the title format
        # -------------------------------------------
        # Regular expressions:  https://docs.python.org/3/library/re.html
        #                       https://docs.python.org/3/howto/regex.html#regex-howto
        between_braces = True
        aFormatGroup = re.sub('[.,].*?}', '}', formatter)
        for char in aFormatGroup:
            if char == "{":
                between_braces = True
            if not between_braces:
                title_formatter += " "
                if char == "|":
                    self.titlebar_formatter2 += "|"
                else:
                    self.titlebar_formatter2 += " "
                continue
            if between_braces and char in [".", ","]:
                # Just read from here to the end "}"
                continue
            if between_braces and char in [".", ",", "f", "d", "$", "%"]:
                continue
            else:
                title_formatter += char
                self.titlebar_formatter2 += char
            if char == "}":
                between_braces = False
        if self.name == "Stocks body":
            print(); myjoe()
            print(f"SELF  : {self.formatter}")
            print(f"Title2: {self.titlebar_formatter2}")
            print(); myjoe()
            myjoe()


        # -------------------------------------------
        # Now do the rest:
        # -------------------------------------------
        # Find the individual column widths:
        for char in expanded_formatter:
            if char == "{":
                need_a_colon = True
            if char in ["{", ",", ".", "}"]:
                take = False
            if take and char in numbers:
                width_str += char
            else:
                width_str += " "
            if char == ":":
                need_a_colon = False
                take = True
            if char == "}":
                take = True
                if need_a_colon:
                    print(); myjoe()
                    print(self.formatter)
                    print(f"*** ERROR! You need to supply a width for field #{len(width_str.split())} or else I can't do this!!!")
                    print(); myjoe()
                    raise UserWarning
        _widths = [int(xx) for xx in width_str.split()]
        for ct in range(len(_widths)):
            self.widths[ct] = int(_widths[ct])
        if len(self.widths) != group_ct:
            msg = f"\t*** ERROR! You need to supply widths for every field format, I'm missing {group_ct - len(self.widths)}!!!\n"
            msg += f"\t{self.widths}\n"
            msg += f"\t{self.formatter}"
            print(msg)
        dots = ""
        crosses = ""
        ct = 0
        flag = True
        for char in expanded_formatter:
            if flag:
                if char != "{":
                    dots += char
                    crosses += " "
                else:
                    flag = False
                    width = int(self.widths[ct])  # did you forget a field width somewhere?
                    dots += "." * width
                    crosses += "-" * width
                    ct += 1
            else:
                if char == "}":
                    flag = True

        self.numTitleFields = len(self.widths)  # [xx for xx in range(len(width_nums))]

        # Finalize the 'crosses' string with actual crosses
        if formatter[-1] == "}":
            self.crosses_formatted = self.addCrosses(crosses)
        else:
            self.crosses_formatted = "!NOTHING DONE!"
        if which == "both":  # check out crosses
            return dots, title_formatter
        elif which == "dots":
            return dots
        else:
            return title_formatter


    def addCrosses(self, crosses):
        #crosses = "-------       -----     ---   -----  ------ ----"
        crosses_orig = crosses  # "-------       -----     ---   -----  ------ ----"
        crossed_formatter = ""
        while crosses:
            pos1 = crosses.find(" ")
            if pos1 == -1:
                crossed_formatter += crosses
                crosses = ""
            else:
                crossed_formatter += crosses[:pos1]
                crosses = crosses[pos1:]
                pos2 = crosses.find("-")
                if pos2 != -1:
                    half = int(pos2/2)
                    if int(pos2/2) == (pos2/2):
                        # An even result
                        # Don't do a '+'
                        crossed_formatter += pos2 * "-"
                    else:
                        # Do a '+'
                        crossed_formatter += (half * "-") + "+" + (half * "-")
                    crosses = crosses[pos2:]
                else:
                    print(f"\n{crosses_orig}")
                    print(f"{crossed_formatter}\n")
                    myjoe()
            myjoe()

        return crossed_formatter



    def makeTopTitle(self, topTitle):
        if not topTitle:
            topTitle = self.name

        currentdt = datetime.datetime.now()
        pretty_today = currentdt.strftime("%b %d, %Y")
        the_time = currentdt.strftime("%T")
        self.wrapInSeparators(f"{topTitle} for {pretty_today} - ({the_time}): ")
        self.add("")


    def add(self, nextItem, fmt=None):
        # check for when a title entry is larger than the field width for it, give a warning for that
        if isinstance(nextItem, Report):  # catches 'Blocks' as well
            self.addBlock(nextItem)   # 'Recursive' as it calls add() in turn
            return True
        if not fmt:
            formatter = self.formatter
        else:
            formatter = fmt
        line = ""
        if isinstance(nextItem, tuple):
            if not self.formatter:
                # Make a bruce version of a line
                for ct, xx in enumerate(nextItem):  # Why do I need 'ct'? Can I get rid of 'enumerate'?
                    if line:
                        line += f"\t{xx}"
                    else:
                        line = xx
            else:
                self.checkWidths(nextItem)
                line = formatter.format(*nextItem)
            self.add(line)                               # Recursive -> add()
            #return True
        elif isinstance(nextItem, str):
            self.addString(nextItem)                     # Recursive -> add()
            #return True
        return True


    def addString(self, aString, noMaxLen=False):
        all_lines = aString.split("\n")
        if len(all_lines) > 2 and all_lines[-1] == "":
            all_lines.pop(-1)
        for line in all_lines:
            line = line.rstrip()
            if noMaxLen is False:
                # Do indeed increment the .max_len variable. The alternative is for footnotes, where
                # I want the line at bottom to extend as far as it wants without impacting any "-" separators above it
                if len(line) > self.max_len:
                    self.max_len = len(line)
            #
            self.text.append(line)  # <-----  The one and only place to .append() text to a report <-----
            #
            self.checkIfAddHeader()


    def checkIfAddHeader(self):
        """ If a Report/Block gets too long, I should add the header columns again, to improve readability """
        if not self.header:
            return
        # breakWheres = [50]  # , 120]
        #if (len(self.text) + len(self.header.text)) in breakWheres:
        if (len(self.text) - self.textStart) in variables.HEADER_BREAK_WHERES:
            # Add the header again
            self.reprintHeader()


    def reprintHeader(self):
        self.add("")
        for line in self.header.text:
            self.add(line)
        self.textStart = len(self.text)


    def upTop(self, text):
        all_lines = text.split("\n")
        for ct in range(len(all_lines), 0, -1):
            line = all_lines[ct-1]
            self.text.insert(0, line)
            self.checkIfAddHeader()
        return


    def titleBar(self, inputs, wrap, debug=False, useBarFormatter=False):
        """ inputs            : The data itself
            wrap              : Separators before and after it
            useOtherFormatter : Use the title formatter with things like "|" in it
            nums  : Print the column numbers our, to make it easier to debug the formatter
            dots       : Print out the format as "." dots, to make it easier to debug
            autoExpand : If a title is larger than its column width, cadjust the column width fit the title
            Money2     : ${5:7,.2f}
        """
        def padLine(aline):
            if self.numTitleFields != len(aline):
                padding = (self.numTitleFields - len(aline)) * ['']
                #aline_old = (*aline), (*padding)
                aline = (*aline,), (*padding,)
                #assert aline == aline_old
            return aline

        if useBarFormatter is False:
            formatter = self.titlebar_formatter
        else:
            formatter = self.titlebar_formatter2

        if isinstance(inputs, tuple):
            self.checkWidths(inputs, titlebar=True)
            line = formatter.format(*padLine(inputs))
        else:
            line_arr = []
            for line in inputs:
                line = padLine(line)
                self.checkWidths(line, titlebar=True)
                line = formatter.format(*padLine(line))
                line_arr.append(line)
            line = "\n".join(line_arr)

        # Once I have the title line(s) fully formatted and ready to print:
        if debug:  # nums:
            # lineNums = self.titlebar_formatter.format(*range(self.numTitleFields))
            strNums = formatter.format(*list(map(str, range(self.numTitleFields))))
            line += f"\n{strNums}"  # strNums gets formatted with alignment, otherwise all 'lineNums' are simply right justified
        if debug:  # dots:
            line += f"\n{self.dots_formatted}"
        if debug and not useBarFormatter:
            line += f"\n{self.crosses_formatted}"

        # Now add it!
        if wrap:
            self.wrapInSeparators(line)
        else:
            self.add(line)
        #
        return

    #def addSeparator(self, seperator="-", oneLine=False):
    #    raise UserWarning
    #    row = len(self.text)
    #    if oneLine:
    #        self.separators[row] = (self.block_start, 999999, seperator)
    #    else:
    #        self.separators[row] = (self.block_start, self.block_start, seperator)
    #    self.add("- separator -")


    def addDots(self):
        self + self.dots_formatted


    def addBreaker(self, seper="-"):
        """ Add a line to the report that "breaks it up", like "+-------+---------------+"
            :param seper: "-" or "=" etc
        """
        if not self.dots_formatted:
            raise UserWarning
        res_arr = []
        for xx in self.dots_formatted:
            if xx == "|":
                res_arr.append("+")
            else:
                res_arr.append(seper)
        res_arr[0] = "+"
        res_arr[-1] = "+"
        res = "".join(res_arr)
        self.add(res)


    def getText(self):
        for line in self.text:
            yield line


    def addBlock(self, aBlock, where=9999):
        """ Take a block of text for a report and keep track of it as a block, so it's easier to move it around the report later
            :param aBlock: a Report class object
            :param where: [0=at beginning, 9999=at end]
        """
        # Can't add what's not there (or is empty?):
        if not aBlock:  # does this get hit?
            return

        if isinstance(aBlock, Header):
            # Add a Header Block to the report, this will be repeated for columns as the report grows in length
            self.header = aBlock
            for line in self.header.text:
                self.add(line)
            self.textStart = len(self.text)

            return True

        assert aBlock.name not in self.block_list.values()
        assert aBlock.name.lower().find("header") == -1

        #self.add("")

        # Append/Insertion logic:
        keys = sorted(self.blocks.keys())
        if keys == [] or where >= max(keys):
            # Add to end (default)
            pos = len(self.blocks)
            self.blocks[pos] = aBlock  # len(self.blocks)] = aBlock
            self.blocksWhere[pos] = len(self.text)  # Where in the report this block s/b inserted
            aBlock.where = len(self.text)
            #pos = len(self.blocks) - 1
        else:
            # Insert this block at position 'where', which is in the middle somewhere
            new_dict = {}
            keys = sorted(self.blocks.keys())
            for xx in keys:
                if xx < where:
                    new_dict[xx] = self.blocks[xx]
                else:
                    new_dict[xx] = aBlock
                    # Now loop-add the following blocks after this one
                    for ct in range(xx, len(keys)):
                        new_dict[ct+1] = self.blocks[ct]
                    break
            self.blocks = new_dict
            pos = where  # Keep track of these!
            self.blocksWhere[len(self.blocks)] = 0  # is this the wrong way round?
            aBlock.where = len(self.text)

        for name_ct in self.blocks.keys():
            self.block_list[name_ct] = self.blocks[name_ct].name  # Check that I don't add the same block name twice

        # Add this block by name to the other list: (I use this when finally printing a report out, to get 'header')
        if aBlock.name.lower().find("header") != -1:
            self.blocksByName["header"] = aBlock
        else:
            self.blocksByName[aBlock.name.lower()] = aBlock

        return pos  # check that outside block has the new WHERE set


    def wrapInSeparators(self, line):
        all_lines = line.split("\n")
        mymax = 0
        for xx in all_lines:
            mymax = max(mymax, len(xx))
        separator = "-" * mymax
        self.add(separator)
        for xx in all_lines:
            self.add(xx)
        self.add(separator)


    def preSeparate(self, a_line):
        a_line = a_line.rstrip()  # ignore blanks
        separator = "-" * len(a_line)
        self.add(separator)
        self.add(a_line)


    def AssembleBlocks(self):
        """ For a block/report, take all the Blocks and add them to the main report's self.text.
            (A 'Block' is a Report object)
        """
        keys = sorted(self.blocks.keys())
        for key in keys:
            self.deconstruct_block(key)
            if self.blocks[key].name.lower() != "header":  # Keep the header around, so I can repeat it
                #self.blocks.pop(key)
                self.blocks[key].processed = True


    def deconstruct_block(self, dinge):
        if isinstance(dinge, int):
            aBlock = self.blocks[dinge]
            where = self.blocksWhere[dinge]  # I need the "Block key" here, like 1 or 2 or 3
        elif isinstance(dinge, Report):
            aBlock = dinge
            where = aBlock.where
        elif isinstance(dinge, Block):
            print("\n\t*** A block cannot contain a block! ***\n")
            raise UserWarning
        else:
            raise UserWarning

        #where = self.blocksWhere[dinge]  # I need the "Block key" here, like 1 or 2 or 3
        appendFlag = len(self.text) == where
        new_text = []
        if appendFlag:
            for xx in range(0, where):  # up to where the block should go
                new_text.append(self.text[xx])
            for ct, line in enumerate(aBlock.text):

                if ct in aBlock.separators:
                    sep_char = aBlock.separators[ct][2]
                    line = sep_char * aBlock.max_len

                new_text.append(line)
        else:  # Insert block into middle of text
            for xx in range(0, where):  # up to where the block should go
                new_text.append(self.text[xx])
            for ct, line in enumerate(aBlock.text):    # now insert the block

                if ct in aBlock.separators:
                    sep_char = aBlock.separators[ct][2]
                    line = sep_char * aBlock.max_len

                new_text.append(line)
            for xx in range(where, len(self.text)):  # add the remaining original text
                new_text.append(self.text[xx])

        max_len = 0
        for line in new_text:
            line = line.rstrip()
            if len(line) > max_len:
                max_len = len(line)
        self.text = new_text
        self.max_len = max_len

        # Ok, now that that's done, increment all the other self.blocksWhere[key+1..] by len(aBlock.text)
        for xx in range(dinge+1, len(self.blocks)):
            # I don't update aBlock.where as the block gets popped() and lost
            self.blocksWhere[xx] += len(aBlock.text)
        myjoe()



    def generate_report_old(self):
        """ Generate a report from self.text.  This assumes the lines do not have \n.
            You need to have all blocks added to the report before this
        """
        raise UserWarning  # just seeing if this is ever called anymore
        # First, add all the blocks to the report:
        if self.blocks:  # does this method ever get used anymore?
            self.AssembleBlocks()

        # This has to be a string, because the whole point is I need to print it as boring text, not some class
        final_arr = []

        # Now process
        for line_ct, line in enumerate(self.text):
            if line_ct not in self.separators:
                # Normal line, just add it
                final_arr.append(line)
            else:
                mymax = 0
                from_line, to_line, sepr = self.separators[line_ct]
                for rep_ct in range(from_line, to_line+1):
                    sep_line = self.text[rep_ct]
                    if sep_line:
                        mymax = max(mymax, len(sep_line))
                separator = sepr * self.max_len
                final_arr.append(separator)

        final_report = ""
        for ct, line in enumerate(final_arr):
            final_report += f"{line}\n"

        # Check no blocks are left laying around / not incorporated into the report:
        for key in self.blocks:
            block = self.blocks[key]
            if block.name.lower() != "header" and not block.processed:
                final_report += f"\nBLOCK {block.name} DID NOT MAKE THE REPORT!\n"

        self.print_version = final_report


    def print(self):
        if not self.print_version:
            self.generate_report()
        print(self.print_version)

#---------------------------------------------------------------------------------
class Block(Report):
    def __str__(self):
        return f"'{self.name}' Block"

    def __init__(self, name, line="", formatter="", topTitle="", titlebar_formatter=""):  # todos="",
        super().__init__(name, line, formatter, titlebar_formatter)
        self.where = 0
        self.processed = False  # Whether it was added into another report yet
        if topTitle:
            self.preSeparate(topTitle)


#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
class Header(Report):
    """ A 'Header' block is a totally specified set of rows to print. It is not just column titles """
    def __str__(self):
        #return f"'{self.name}' Header"
        return "Header"

    def __init__(self, name, line="", formatter="", topTitle="", titlebar_formatter=""):  # todos="",
        super().__init__(name, line, formatter, titlebar_formatter)  # todos, topTitle
        self.headerLen = 0
        self.headerText = ""
        self.headerPos = 0

    def __add__(self, line):
        self.headerAdd(line)

    def headerAdd(self, someText):
        all_lines = someText.split("\n")
        if len(all_lines) > 2 and all_lines[-1] == "":
            all_lines.pop(-1)
        for line in all_lines:
            line = line.rstrip()
            if len(line) > self.max_len:
                self.max_len = len(line)
            #
            self.text.append(line)  # <-----  The one and only place to .append() text to a report <-----
            #
        myjoe()

#---------------------------------------------------------------------------------


"""
def MakeTODOList(which):
    raise UserWarning
    todos_dict = {
        "Morning Report": [
            "XLF Calls/Puts",
            "Convertible bonds - https://www.barrons.com/articles/new-convertible-offers-way-to-play-slide-in-viacomcbs-shares-51617105624",
            "Add bond #s so I can see inflation",
            "Add SPX, NDX, IWM return percents to top of report",
            "Preferred stock?",
            "Add news stories? Filter for my positions",
            "get_dividend_income(): DIVIDEND NUMBERS NO LONGER REFLECT CLOSED OUT POSITIONS",
            ],
        "Orders and Trades": ["If I download a new trade, then go back and get account summary information",
                              "Get greeks for any option I have a position, or an order for, even if the order is expired unfilled",
                              "Put more details for option orders (expiry, strike, delta, gamma etc)",
                              ],
        "Stocks Report": [
            "1 - WHAT DO I WANT TO GET RID OF ANYWAY? SELL A CALL ON IT FIRST!",
            "2 - SELL PUTS ON THINGS I'D BE HAPPY TO OWN",
            "3 - SELL PUTS ON OTHER THINGS",
            "Turn 'good_position' off each morning, then back on when a good IB/ETrade position request is done",
            "get_dividend_income(): DIVIDEND NUMBERS NO LONGER REFLECT CLOSED OUT POSITIONS",
            "Missing EU dividends (but I'm closing those positions anyway)",
            "Make a separate 'PERCENT OF PORTFOLIO' report?",
        ],
        "Options Report": ["They're all American - can be exercised at any time",
                           "Order the stocks by ITM, but then do each stock for all its strikes"
                           ],
        "Dividends Report": [
            "Get all 'sources' filled in! (many are blank)",
            "Missing EU dividends",
            "Make a separate 'PERCENT OF PORTFOLIO' report?",
        ],
        "Commissions": ["Need to download IB orders first",
                        "Make 'FEE' a highlighted column"]
    }

    if which not in todos_dict:
        return

    todos = todos_dict[which]
    #if not todos:
    #    return None

    block = Block(f"{which} Todo List")
    if len(todos) == 1:
        block.wrapInSeparators(f"TODO - {todos[0]}")
    else:
        block + f"TODO - {todos[0]}"
    todos.pop(0)
    # Loop over the rest:
    for xx in todos:
        block + f"     - {xx}"
    block + ""
    return block
"""