from saral.error import ParseError
from saral.lexer.token import Token
from saral.lexer.token_type import TokenType
from saral.parser.ast import *
from typing import cast

# Type keywords that may open a declaration.
_TYPE_KEYWORDS = (
    TokenType.KW_INT,
    TokenType.KW_FLOAT,
    TokenType.KW_STRING,
    TokenType.BOOL,
)

_COMPARISON_OPERATORS = (
    TokenType.EQ,
    TokenType.NEQ,
    TokenType.LT,
    TokenType.LE,
    TokenType.GT,
    TokenType.GE,
)


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        """<program> ::= <stmt-list>"""
        statements = []
        while not self.at_end():
            statements.append(self.statement())
        return Program(statements=statements)

    # ------------------------------ statements ------------------------------

    def statement(self) -> Stmt:
        """<stmt> ::= <assignment> | <show-stmt> | <if-stmt> | <while-stmt>
        | <func-stmt> | <func-call-stmt> | <return-stmt>
        """
        if self.check_any(*_TYPE_KEYWORDS):
            return self.declaration()
        if self.match(TokenType.SHOW):
            return self.show_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.check(TokenType.IDENTIFIER):
            # An identifier starts either a call statement or a reassignment;
            # the token after it tells us which.
            if self.check_next(TokenType.LPAREN):
                return self.function_call_statement()
            return self.reassignment()

        raise self.error(
            self.peek(), f"Unexpected {self.describe(self.peek())} at start of statement"
        )

    def declaration(self) -> Stmt:
        """<assignment> ::= <type> <identifier> = <initializer>;

        Also handles <func-stmt>, which begins with the same two tokens.
        """
        type_token = self.advance()
        name = self.consume(TokenType.IDENTIFIER, "Expected a variable name after the type")

        if self.check(TokenType.LPAREN):
            return self.function_statement(type_token, name)

        self.consume(TokenType.ASSIGN, "Expected '=' after the variable name")
        value = self.initializer()
        self.consume(TokenType.SEMICOLON, "Expected ';' after the assignment")
        return AssignmentStmt(var_type=type_token.lexeme, name=name.lexeme, value=value)

    def reassignment(self) -> AssignmentStmt:
        name = self.consume(TokenType.IDENTIFIER, "Expected a variable name")
        self.consume(TokenType.ASSIGN, "Expected '=' after the variable name")
        value = self.initializer()
        self.consume(TokenType.SEMICOLON, "Expected ';' after the assignment")
        return AssignmentStmt(var_type=None, name=name.lexeme, value=value)

    def show_statement(self) -> ShowStmt:
        self.consume(TokenType.LPAREN, "Expected '(' after 'show'")
        expr = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after the expression")
        self.consume(TokenType.SEMICOLON, "Expected ';' after the show statement")
        return ShowStmt(expression=expr)

    def if_statement(self) -> IfStmt:
        """<if-stmt> ::= if(<comp-exp>) <block> [else <block>]"""
        self.consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after the condition")

        then_branch = self.block()
        else_branch = self.block() if self.match(TokenType.ELSE) else None
        return IfStmt(condition=condition, then_branch=then_branch, else_branch=else_branch)

    def while_statement(self) -> WhileStmt:
        self.consume(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after the condition")
        return WhileStmt(condition=condition, body=self.block())

    def return_statement(self) -> ReturnStmt:
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.initializer()
        self.consume(TokenType.SEMICOLON, "Expected ';' after the return statement")
        return ReturnStmt(value=value)

    def function_statement(self, type_token: Token, name: Token) -> FunctionStmt:
        self.consume(TokenType.LPAREN, "Expected '(' after the function name")
        parameters = []
        if not self.check(TokenType.RPAREN):
            parameters.append(self.parameter())
            while self.match(TokenType.COMMA):
                parameters.append(self.parameter())
        self.consume(TokenType.RPAREN, "Expected ')' after the parameters")
        return FunctionStmt(
            return_type=type_token.lexeme,
            name=name.lexeme,
            parameters=parameters,
            body=self.block(),
        )

    def function_call_statement(self) -> FunctionCall:
        name = self.consume(TokenType.IDENTIFIER, "Expected a function name")
        call = self.finish_call(name)
        self.consume(TokenType.SEMICOLON, "Expected ';' after the function call")
        return call

    def block(self) -> BlockStmt:
        self.consume(TokenType.LBRACE, "Expected '{' to open the block")
        statements = []
        while not self.check(TokenType.RBRACE) and not self.at_end():
            statements.append(self.statement())
        self.consume(TokenType.RBRACE, "Expected '}' to close the block")
        return BlockStmt(statements=statements)

    def parameter(self) -> Parameter:
        """<param-list> ::= <type> <identifier> { , <type> <identifier> }"""
        type_token = self.consume_type()
        name = self.consume(TokenType.IDENTIFIER, "Expected a parameter name")
        return Parameter(param_type=type_token.lexeme, name=name.lexeme)

    def argument(self) -> Argument:
        """<arg-list> ::= <exp> { , <exp> }"""
        return Argument(value=self.expression())

    # ------------------------------ expressions -----------------------------
    def initializer(self) -> Expr:
        if self.match(TokenType.LBRACKET):
            elements = []
            if not self.check(TokenType.RBRACKET):
                elements.append(self.initializer())
                while self.match(TokenType.COMMA):
                    elements.append(self.initializer())
            self.consume(TokenType.RBRACKET, "Expected ']' after the array initializer")
            return ArrayStmt(elements=elements)
        return self.expression()

    def expression(self) -> Expr:
      return self.comparison()

    def comparison(self) -> Expr:
        """<comp-exp> ::= <arith-exp> [ <comp-op> <arith-exp> ]"""
        expr = self.arithmetic()
        if self.match(*_COMPARISON_OPERATORS):
            operator = self.previous()
            expr = Binary(left=expr, operator=operator.lexeme, right=self.arithmetic())
        return expr

    def arithmetic(self) -> Expr:
        """<arith-exp> ::= <arith-exp> + <term> | <arith-exp> - <term> | <term>"""
        expr = self.term()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            expr = Binary(left=expr, operator=operator.lexeme, right=self.term())
        return expr

    def term(self) -> Expr:
      expr = self.factor()
      while self.match(TokenType.MUL, TokenType.DIV, TokenType.MOD):
          operator = self.previous()
          expr = Binary(left=expr, operator=operator.lexeme, right=self.factor())
      return expr

    def factor(self) -> Expr:
        if self.match(TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL):
            return NumberNode(value=self.previous().literal)

        if self.match(TokenType.STRING_LITERAL):
            return StringNode(value=self.previous().literal)

        if self.match(TokenType.KW_TRUE, TokenType.KW_FALSE):
            return BoolNode(value=self.previous().literal)

        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after the expression")
            return expr

        if self.match(TokenType.IDENTIFIER):
            name = self.previous()
            if self.check(TokenType.LPAREN):
              return cast(Expr, self.finish_call(name))
            return Variable(name=name.lexeme)

        raise self.error(
            self.peek(), f"Expected an expression but found {self.describe(self.peek())}"
        )

    def finish_call(self, name_token: Token) -> FunctionCall:
        self.consume(TokenType.LPAREN, "Expected '(' after the function name")
        arguments = []
        if not self.check(TokenType.RPAREN):
            arguments.append(self.argument())
            while self.match(TokenType.COMMA):
                arguments.append(self.argument())
        self.consume(TokenType.RPAREN, "Expected ')' after the arguments")
        return FunctionCall(name=name_token.lexeme, arguments=arguments)

    # ---------------------------- support methods ---------------------------
    def peek(self) -> Token:
        return self.tokens[self.current]

    def peek_next(self) -> Token:
        if self.current + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.current + 1]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def advance(self) -> Token:
        if not self.at_end():
            self.current += 1
        return self.previous()

    def check(self, type_: TokenType) -> bool:
        return not self.at_end() and self.peek().type == type_

    def check_any(self, *types: TokenType) -> bool:
        return any(self.check(type_) for type_ in types)

    def check_next(self, type_: TokenType) -> bool:
        return self.peek_next().type == type_

    def match(self, *types: TokenType) -> bool:
        if self.check_any(*types):
            self.advance()
            return True
        return False

    def consume(self, type_: TokenType, message: str) -> Token:
        if self.check(type_):
            return self.advance()
        raise self.error(self.peek(), message)

    def consume_type(self) -> Token:
        if self.match(*_TYPE_KEYWORDS):
            return self.previous()
        raise self.error(self.peek(), "Expected a type keyword (int, float, string or bool)")

    def at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def error(self, token: Token, message: str) -> ParseError:
      """Build a ParseError pointing at the offending token."""
      return ParseError(message, token.line, token.column)

    @staticmethod
    def describe(token: Token) -> str:
      """Human-readable name for a token, used in error messages."""
      if token.type == TokenType.EOF:
        return "end of file"
      return repr(token.lexeme)
