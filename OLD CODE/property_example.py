"""
bob = Data("Bob Smith")
print(bob.value)
bob.value = "Robert Smith"
print(bob.value)
del bob.value

print("-"*20)
sue = Data("Sue Jones")
print(sue.value)
print(Data.value.__doc__)
"""


class myData:
    # Page 1268 "Learning Python" books
    def __init__(self, value):
        self._value = value
        
    @property
    def value(self):
        " value property doc "
        # print("fetch..")
        return self._value
    
    @value.setter
    def value(self, value):
        #print("Change..")
        assert isinstance(value, (int, float))
        self._value = value
        return
        
    @value.deleter
    def value(self):
        # print("remove..")
        del self._value

class myNumber(myData):
    def __init__(self, value):
        assert isinstance(value, (int, float))
        super().__init__(value)

class myString(myData):
    def __init__(self, value):
        if not isinstance(value, str):
            value = str(value)
        super().__init__(value)


#_joe = myData("hi there")
mary = myNumber(12)
print(mary.value)
mary = myString("13")
print(mary.value)

