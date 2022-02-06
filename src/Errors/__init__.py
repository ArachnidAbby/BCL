#Colors [Linux Only :(]

Error_Red = '\u001b[31m'
Reset = '\u001b[0m'
seperator="\u001b[38;5;174m"

#classes

class Error:
    def __init__(self, lineNum, ErrorText):
        #self.line = line
        self.lineNum = lineNum
        self.ErrorText = ErrorText
    
    def raise_error(self):
        try: 
            raise Exception(f"""{seperator}{"}"}----- {Error_Red}
| An Error has Occured on line: {self.lineNum}
| Error Details:
|    {self.ErrorText}
\-------------------------------------------------{Reset}""")
        except Exception as e:
            print(e)

    # Error Types

    def Unknown(lineNum):
        error = Error(lineNum, "An Unknown Comiler Error has Occured.").raise_error()
        raise ValueError('')
    def Unknown_Function(lineNum):
        error = Error(lineNum, "An Unknown Function Spotted.").raise_error()
        quit()
    
    def Invalid_Arguement_Count(lineNum,args, expected):
        error = Error(lineNum, f"There are an invalid Number of arguements. {args} arguement(s) passed. {expected} arguement(s) expected").raise_error()
        quit()
    
    def Unclosed_Parenth(lineNum):
        error = Error(lineNum, f"Unclosed parenthese on line {lineNum}").raise_error()
        quit()
