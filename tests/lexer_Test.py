import os
import sys

p = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{p}/../src')

import unittest
import lexer

class LexerTests(unittest.TestCase):
    def test(self):
        self.test_tokens()

    def test_tokens(self):
        test_code = """
            ( ) { } [ ] ; ::< :: : -> , ... .. . += *= /= -= + ** *
            / - % == != >= <= << >> ^ | ~ > < & =
        """
        toks = lexer.Lexer().get_lexer().lex(test_code)

        assert self.tok_seq(toks, [
            "OPEN_PAREN", "CLOSE_PAREN", "OPEN_CURLY", "CLOSE_CURLY",
            "OPEN_SQUARE", "CLOSE_SQUARE", "SEMI_COLON", "OPEN_TYPEPARAM",
            "NAMEINDEX", "COLON", "RIGHT_ARROW", "COMMA", "ELLIPSIS",
            "DOUBLE_DOT", "DOT", "ISUM", "IMUL", "IDIV", "ISUB", "SUM",
            "POW", "MUL", "DIV", "SUB", "MOD", "EQ", "NEQ", "GEQ", "LEQ",
            "LSHIFT", "RSHIFT", "BXOR", "BOR", "BNOT", "GR", "LE", "AMP",
            "SET_VALUE"
        ])

    def tok_seq(self, toks, seq: list[str]) -> bool:
        i = 0

        for c, t in enumerate(toks):
            if t.name != seq[c]:
                print("expected %s got %s" % (seq[c], t.name))
                return False
            else:
                i += 1

        if i != len(seq):
            print("got %d tokens but %d are expected" % (i, len(seq)))
            return False
        
        return True

LexerTests().test()
            


