RED = "\u001b[31m"
RESET = "\u001b[0m"
YELLOW = "\u001b[33;1m"
GREEN = "\u001b[32m"
ORANGE = "\u001b[38;5;209;1m"


def error(text: str, line = (-1,-1,-1)):
    
    largest = max(
        [len(x) for x in f"| {text}".split('\n')]+
        [len(f"|    Line: {line[0]}")]
    )
    print(f'{RED}#{"-"*(largest//4)}')
    print(f'| {text}')
    print(f'|    Line: {line[0]}')
    print(f'\\{"-"*(largest-1)}/{RESET}')
    print("\n\n\n\n")
    quit()
