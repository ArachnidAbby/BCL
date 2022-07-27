RED = "\u001b[31m"
RESET = "\u001b[0m"


def error(text: str):
    print(f'{RED}{text}{RESET}')
    quit()