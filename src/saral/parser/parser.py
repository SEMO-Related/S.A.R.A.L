from saral.lexer.token import Token
from saral.lexer.token_type import TokenType
from saral.parser.ast import *
from saral.error import SaralError

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

    def parse(self):
        statements = []

        while not self.at_end():
            statements.append(self.statement())

        return Program(statements=statements)
        
    # -------------Grammar Rules-------------
    def statement(self):
        #print("Current statement token:",self.peek())  # Debugging line
        if self.check_any(*_TYPE_KEYWORDS):
            #print("Parsing assignment statement")  # Debugging line
            return self.declaration()
        elif self.match(TokenType.SHOW):
            #print("Parsing show statement")  # Debugging line
            return self.show_statement()
        elif self.match(TokenType.IF):
            #print("Parsing if statement")  # Debugging line
            return self.if_statement()
        elif self.match(TokenType.WHILE):
            #print("Parsing while statement")  # Debugging line
            return self.while_statement()
        elif self.match(TokenType.RETURN):
            #print("Parsing return statement")  # Debugging line
            return self.return_statement()
        elif self.match(TokenType.IDENTIFIER):
            #print("Matched identifier statement:", self.previous())  # Debugging line
            if self.check_next(TokenType.LPAREN):
                return self.function_call_statement()
            return self.reassignment()

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
    
    def initializer(self) -> Expr:
        if self.match(TokenType.LBRACKET):
            name = self.previous().lexeme
            elements = []
            if not self.check(TokenType.RBRACKET):
                elements.append(self.expression())
                while self.match(TokenType.COMMA):
                    elements.append(self.expression())
            self.consume(TokenType.RBRACKET, "Expected ']' after array initializer")
            return ArrayStmt(elements=elements)
        return self.expression()


    def comparison(self):
        expr = self.arithmetic()
        if self.match(*_COMPARISON_OPERATORS):
            operator = self.previous()
            right = self.expression()
            expr = Binary(left=expr, operator=operator.lexeme, right=right)
        return expr

    def arithmetic(self) -> Expr:
        """<arith-exp> ::= <arith-exp> + <term> | <arith-exp> - <term> | <term>"""
        expr = self.term()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            expr = Binary(left=expr, operator=operator.lexeme, right=self.term())
        return expr

    def expression(self):
        expr = self.term()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.term()
            expr = Binary(left=expr, operator=operator.lexeme, right=right)
        return expr

    def term(self):
        term = self.factor()
        while self.match(TokenType.MUL, TokenType.DIV, TokenType.MOD):
            operator = self.previous()
            right = self.factor()
            term = Binary(left=term, operator=operator.lexeme, right=right)
        return term

    def factor(self):
        print("Current token in factor:", self.peek())  # Debugging line
        if self.match(TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL):
            return NumberNode(value=self.previous().literal)
        
        if self.match(TokenType.STRING_LITERAL):
            return StringNode(value=self.previous().literal)
        
        if self.match(TokenType.KW_TRUE, TokenType.KW_FALSE):
            return BoolNode(value=self.previous().literal)

        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr
        
        if self.match(TokenType.IDENTIFIER):
            if self.check(TokenType.LPAREN):
                return self.finish_call(self.previous())
            return Variable(name=self.previous().lexeme)
        raise Exception("Expected expression, found: " + self.peek().lexeme) # Replace with a proper error handling mechanism

    def parameter(self):
        self.consume_type()
        name = self.consume(TokenType.IDENTIFIER, "Expected parameter name")
        return Parameter(param_type=self.previous().lexeme, name=name.lexeme)

    def argument(self):
        return Argument(value=self.expression())

    def block(self):
        statements = []
        while not self.check(TokenType.RBRACE) and not self.at_end():
            statements.append(self.statement())
        return BlockStmt(statements=statements)

    def assignment(self):
        type_token = self.advance()
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name after type")
        if self.check(TokenType.LPAREN):
                    return self.function_statement(type_token, name)
        if self.check(TokenType.LBRACKET):
            # Handle array initializer
            pass
        self.consume(TokenType.ASSIGN, "Expected '=' after variable name")
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after assignment")

        return AssignmentStmt(var_type=type_token.lexeme, name=name.lexeme, value=value)
    
    def show_statement(self):
        self.consume(TokenType.LPAREN, "Expected '(' after 'show'")
        expr = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after expression")
        self.consume(TokenType.SEMICOLON, "Expected ';' after show statement")
        return ShowStmt(expression=expr)

    def if_statement(self):
        self.consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")

        then_branch = self.block()
        else_branch = None
        if self.match(TokenType.ELSE):
            self.consume(TokenType.LBRACE, "Expected '{' before 'else' block")
            else_branch = self.block()

        return IfStmt(condition=condition, then_branch=then_branch, else_branch=else_branch)

    def while_statement(self):
        self.consume(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self.expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")
        self.consume(TokenType.LBRACE, "Expected '{' before 'while' block")
        body = self.block()
        self.consume(TokenType.RBRACE, "Expected '}' after 'while' block")
        
        return WhileStmt(condition=condition, body=body)

    def return_statement(self):
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.initializer()
        self.consume(TokenType.SEMICOLON, "Expected ';' after return statement")
        return ReturnStmt(value=value)

    def function_call_statement(self) -> FunctionCall:
        name = self.consume(TokenType.IDENTIFIER, "Expected a function name")
        call = self.finish_call(name)
        self.consume(TokenType.SEMICOLON, "Expected ';' after the function call")
        return call


    def function_statement(self, type_token, name):

        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        parameters = []
        if not self.check(TokenType.RPAREN):
            parameters.append(self.parameter())
            while self.match(TokenType.COMMA):
                parameters.append(self.parameter())
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")
        self.consume(TokenType.LBRACE, "Expected '{' before function body")
        body = self.block()
        self.consume(TokenType.RBRACE, "Expected '}' after function body")
        return FunctionStmt(return_type=type_token.lexeme, name=name.lexeme, parameters=parameters, body=body)

    def array_initializer(self,name,elements):
        pass

    def finish_call(self, name_token: Token) -> FunctionCall:
        self.consume(TokenType.LPAREN, "Expected '(' after the function name")
        arguments = []
        if not self.check(TokenType.RPAREN):
            arguments.append(self.argument())
            while self.match(TokenType.COMMA):
                arguments.append(self.argument())
        self.consume(TokenType.RPAREN, "Expected ')' after the arguments")
        return FunctionCall(name=name_token.lexeme, arguments=arguments)

    
    # -------------Support Methods-------------
    def is_assign(self) -> bool:
        return (self.check(TokenType.KW_INT)
                or self.check(TokenType.KW_FLOAT)
                or self.check(TokenType.KW_STRING) 
                or self.check(TokenType.BOOL))
    
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
        if self.at_end():
            return False
        return self.peek().type == type_

    def check_any(self, *types: TokenType) -> bool:
        return any(self.check(type_) for type_ in types)
    
    def check_next(self, type_: TokenType) -> bool:
        return self.peek_next().type == type_

    def match(self, *types: TokenType) -> bool:
        for type_ in types:
            if self.check(type_):
                self.advance()
                return True
        return False

    def consume(self, type_: TokenType, message: str) -> Token:
        if self.check(type_):
            return self.advance()
        raise Exception(message) # Replace with a proper error handling mechanism

    def consume_type(self) -> Token:
        if self.match(TokenType.KW_INT,
                      TokenType.KW_FLOAT,
                      TokenType.KW_STRING,
                      TokenType.BOOL):
            return self.previous()
        raise Exception("Expected parameter type") # Replace with a proper error handling mechanism

    def at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

