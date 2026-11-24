"""Minimal IEC 61131-3 Structured Text front-end (subset).

Purpose: W1 feasibility probe for DeltaScope. NOT a conformant compiler.
Supported:
  PROGRAM / FUNCTION_BLOCK, VAR_INPUT / VAR_OUTPUT / VAR blocks,
  assignment, IF / ELSIF / ELSE / END_IF,
  AND OR XOR NOT, = <> < > <= >=, + - * / MOD,
  FB calls with named arguments, member access (fb.Q), TIME literals.
"""

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------- tokens

TOKEN_RE = re.compile(
    r"""
      (?P<WS>\s+)
    | (?P<COMMENT>\(\*.*?\*\)|//[^\n]*)
    | (?P<TIME>T\#[0-9A-Za-z]+|TIME\#[0-9A-Za-z]+)
    | (?P<NUM>\d+\.\d+|\d+)
    | (?P<ID>[A-Za-z_][A-Za-z_0-9]*)
    | (?P<OP>:=|<>|<=|>=|[.;:,()=<>&+\-*/])
    """,
    re.S | re.X,
)

KEYWORDS = {
    "PROGRAM", "FUNCTION_BLOCK", "END_PROGRAM", "END_FUNCTION_BLOCK",
    "VAR", "VAR_INPUT", "VAR_OUTPUT", "VAR_IN_OUT", "END_VAR",
    "IF", "THEN", "ELSIF", "ELSE", "END_IF",
    "AND", "OR", "XOR", "NOT", "MOD",
    "TRUE", "FALSE", "RETURN",
}


@dataclass
class Tok:
    kind: str
    val: str
    line: int


class ParseError(Exception):
    pass


def tokenize(src: str):
    toks = []
    i, line = 0, 1
    while i < len(src):
        m = TOKEN_RE.match(src, i)
        if not m:
            raise ParseError(f"unexpected character {src[i]!r} at line {line}")
        kind = m.lastgroup
        val = m.group()
        if kind == "COMMENT":
            line += val.count("\n")
        elif kind == "WS":
            line += val.count("\n")
        else:
            toks.append(Tok(kind, val, line))
        i = m.end()
    toks.append(Tok("EOF", "", line))
    return toks


def parse_time_ms(text: str) -> int:
    """T#2S -> 2000, T#200MS -> 200, T#1S500MS -> 1500"""
    body = text.split("#", 1)[1].upper()
    total = 0
    for num, unit in re.findall(r"(\d+)(MS|D|H|M|S)", body):
        n = int(num)
        total += n * {"MS": 1, "S": 1000, "M": 60000, "H": 3600000, "D": 86400000}[unit]
    return total


# ---------------------------------------------------------------- AST

@dataclass
class Decl:
    name: str
    type: str
    init: object = None


@dataclass
class Program:
    name: str
    kind: str                       # PROGRAM | FUNCTION_BLOCK
    decls: list = field(default_factory=list)
    body: list = field(default_factory=list)

    def names(self, scope_kind):
        return [d.name for d in self.decls if d.scope == scope_kind]

    @property
    def inputs(self):
        return [d for d in self.decls if d.scope == "VAR_INPUT"]

    @property
    def outputs(self):
        return [d for d in self.decls if d.scope == "VAR_OUTPUT"]


@dataclass
class Decl_(Decl):
    scope: str = "VAR"


# ---------------------------------------------------------------- parser

class Parser:
    def __init__(self, toks):
        self.t = toks
        self.i = 0

    # -- helpers
    def peek(self, k=0):
        return self.t[self.i + k]

    def at(self, kind, val=None):
        tok = self.peek()
        if tok.kind != kind:
            return False
        return val is None or tok.val.upper() == val

    def eat(self, kind=None, val=None):
        tok = self.peek()
        if kind and tok.kind != kind:
            raise ParseError(f"expected {kind}, got {tok.kind}:{tok.val!r} line {tok.line}")
        if val and tok.val.upper() != val:
            raise ParseError(f"expected {val}, got {tok.val!r} line {tok.line}")
        self.i += 1
        return tok

    # -- program
    def parse_program(self):
        if self.at("ID", "PROGRAM"):
            self.eat()
            kind = "PROGRAM"
            end = "END_PROGRAM"
        elif self.at("ID", "FUNCTION_BLOCK"):
            self.eat()
            kind = "FUNCTION_BLOCK"
            end = "END_FUNCTION_BLOCK"
        else:
            raise ParseError("expect PROGRAM or FUNCTION_BLOCK")
        name = self.eat("ID").val
        prog = Program(name=name, kind=kind)

        while self.at("ID") and self.peek().val.upper() in (
            "VAR", "VAR_INPUT", "VAR_OUTPUT", "VAR_IN_OUT"
        ):
            scope = self.eat("ID").val.upper()
            while not self.at("ID", "END_VAR"):
                for d in self.parse_decl(scope):
                    prog.decls.append(d)
            self.eat("ID", "END_VAR")

        while not (self.at("ID") and self.peek().val.upper() == end):
            if self.at("EOF"):
                raise ParseError(f"unterminated block {name}")
            prog.body.append(self.parse_stmt())
        self.eat("ID", end)
        return prog

    def parse_decl(self, scope):
        names = [self.eat("ID").val]
        while self.at("OP", ","):
            self.eat()
            names.append(self.eat("ID").val)
        self.eat("OP", ":")
        tname = self.eat("ID").val
        # ignore ARRAY(...) style suffixes
        while self.at("OP", "("):
            depth = 0
            while True:
                tok = self.eat()
                if tok.val == "(":
                    depth += 1
                elif tok.val == ")":
                    depth -= 1
                    if depth == 0:
                        break
        init = None
        if self.at("OP", ":="):
            self.eat()
            init = self.parse_expr()
        self.eat("OP", ";")
        return [Decl_(name=n, type=tname, init=init, scope=scope) for n in names]

    # -- statements
    def parse_stmt(self):
        if self.at("OP", ";"):
            self.eat()
            return ("nop",)
        if self.at("ID", "IF"):
            return self.parse_if()
        # assignment or FB call
        name = self.eat("ID").val
        target = [name]
        while self.at("OP", "."):
            self.eat()
            target.append(self.eat("ID").val)
        if self.at("OP", "("):
            self.eat()
            args = self.parse_args()
            self.eat("OP", ")")
            self.eat("OP", ";")
            return ("call", target[0], args)
        self.eat("OP", ":=")
        expr = self.parse_expr()
        self.eat("OP", ";")
        return ("assign", target, expr)

    def parse_if(self):
        self.eat("ID", "IF")
        branches = []
        cond = self.parse_expr()
        self.eat("ID", "THEN")
        branches.append((cond, self.parse_block(("ELSIF", "ELSE", "END_IF"))))
        while self.at("ID", "ELSIF"):
            self.eat()
            c = self.parse_expr()
            self.eat("ID", "THEN")
            branches.append((c, self.parse_block(("ELSIF", "ELSE", "END_IF"))))
        els = None
        if self.at("ID", "ELSE"):
            self.eat()
            els = self.parse_block(("END_IF",))
        self.eat("ID", "END_IF")
        if self.at("OP", ";"):
            self.eat()
        return ("if", branches, els)

    def parse_block(self, terminators):
        out = []
        while not (self.at("ID") and self.peek().val.upper() in terminators):
            if self.at("EOF"):
                raise ParseError("unterminated block")
            out.append(self.parse_stmt())
        return out

    def parse_args(self):
        args = []
        while not self.at("OP", ")"):
            if self.at("ID") and self.peek(1).kind == "OP" and self.peek(1).val == ":=":
                pname = self.eat("ID").val
                self.eat("OP", ":=")
                args.append((pname, self.parse_expr()))
            else:
                args.append((None, self.parse_expr()))
            if self.at("OP", ","):
                self.eat()
        return args

    # -- expressions (ST precedence)
    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        node = self.parse_xor()
        while self.at("ID", "OR"):
            self.eat()
            node = ("bin", "OR", node, self.parse_xor())
        return node

    def parse_xor(self):
        node = self.parse_and()
        while self.at("ID", "XOR"):
            self.eat()
            node = ("bin", "XOR", node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_not()
        while self.at("ID", "AND"):
            self.eat()
            node = ("bin", "AND", node, self.parse_not())
        return node

    def parse_not(self):
        if self.at("ID", "NOT"):
            self.eat()
            return ("un", "NOT", self.parse_not())
        return self.parse_cmp()

    def parse_cmp(self):
        node = self.parse_add()
        if self.at("OP") and self.peek().val in ("=", "<>", "<", ">", "<=", ">="):
            op = self.eat().val
            node = ("bin", op, node, self.parse_add())
        return node

    def parse_add(self):
        node = self.parse_mul()
        while self.at("OP") and self.peek().val in ("+", "-"):
            op = self.eat().val
            node = ("bin", op, node, self.parse_mul())
        return node

    def parse_mul(self):
        node = self.parse_unary()
        while (self.at("OP") and self.peek().val in ("*", "/")) or self.at("ID", "MOD"):
            op = self.eat().val.upper()
            node = ("bin", op, node, self.parse_unary())
        return node

    def parse_unary(self):
        if self.at("OP") and self.peek().val in ("+", "-"):
            op = self.eat().val
            return ("un", op, self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
        while self.at("OP", "."):
            self.eat()
            node = ("member", node, self.eat("ID").val)
        if self.at("OP", "("):        # function-style call in expression
            self.eat()
            args = self.parse_args()
            self.eat("OP", ")")
            node = ("fcall", node, args)
        return node

    def parse_primary(self):
        tok = self.peek()
        if tok.kind == "OP" and tok.val == "(":
            self.eat()
            node = self.parse_expr()
            self.eat("OP", ")")
            return node
        if tok.kind == "NUM":
            self.eat()
            return ("const", float(tok.val) if "." in tok.val else int(tok.val))
        if tok.kind == "TIME":
            self.eat()
            return ("const", parse_time_ms(tok.val))
        if tok.kind == "ID":
            up = tok.val.upper()
            if up == "TRUE":
                self.eat()
                return ("const", True)
            if up == "FALSE":
                self.eat()
                return ("const", False)
            self.eat()
            return ("var", tok.val)
        raise ParseError(f"unexpected token {tok.kind}:{tok.val!r} line {tok.line}")


def parse(src: str) -> Program:
    return Parser(tokenize(src)).parse_program()


def parse_expr(src: str):
    """Parse a standalone ST expression (used by contract guards)."""
    toks = tokenize(src)
    return Parser(toks).parse_expr()
