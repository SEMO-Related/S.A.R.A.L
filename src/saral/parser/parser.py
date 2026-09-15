from saral.lexer.token import Token
from saral.lexer.token_type import TokenType

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        statements = []

        while not self.at_end():
            statements.append(self.statement())

        return Program(statements)
        pass
    # -------------Grammar Rules-------------
    def statement(self):
        if self.is_assign():
            return self.assign_type()
        elif self.match(TokenType.SHOW):
            return self.show_statement()
        elif self.match(TokenType.IF):
            return self.if_statement()
        elif self.match(TokenType.WHILE):
            return self.while_statement()
        elif self.match(TokenType.RETURN):
            return self.return_statement()
        elif self.match(TokenType.IDENTIFIER):
            return self.function_call_statement()
        else:
            raise Exception("Unexpected token: " + self.peek().lexeme) # Replace with a proper error handling

    def initializer(self):
        if self.match(TokenType.LBRACKET):
            elements = []
            if not self.check(TokenType.RBRACKET):
                elements.append(self.expression())
                while self.match(TokenType.COMMA):
                    elements.append(self.expression())
            self.consume(TokenType.RBRACKET, "Expected ']' after array initializer")
            return {"type": "array_initializer", "elements": elements}
        return self.expression()
    
    def expression(self):
        self.consume
        pass

    def term(self):
        # Implement the term parsing logic here
        pass

    def factor(self):
        # Implement the factor parsing logic here
        pass

    def parameter(self):
        # Implement the parameter parsing logic here
        pass

    def argument(self):
        # Implement the argument parsing logic here
        pass

    def block(self):
        statements = []
        self.consume(TokenType.LBRACE, "Expected '{' before block")
        while not self.check(TokenType.RBRACE) and not self.at_end():
            statements.append(self.statement())
        self.consume(TokenType.RBRACE, "Expected '}' after block")
        return statements
        

    def show_statement(self):
        self.consume(TokenType.LPAREN, "Expected '(' after 'show'")
        expr = self.initializer()
        self.consume(TokenType.RPAREN, "Expected ')' after expression")
        self.consume(TokenType.SEMICOLON, "Expected ';' after show statement")
        return {"type": 
                "show", 
                "expression": expr}

    def if_statement(self):
        self.consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self.initializer()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")

        then_branch = self.block()

        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.block()

        return {"type": "if", 
                "condition": condition, 
                "then": then_branch, 
                "else": else_branch}

    def while_statement(self):
        self.consume(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self.initializer()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")
        body = self.block()
        return {"type": "while", 
                "condition": condition, 
                "body": body}

    def return_statement(self):
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.initializer()
        self.consume(TokenType.SEMICOLON, "Expected ';' after return statement")
        return {"type": "return", 
                "value": value}

    def function_call_statement(self):
        name = self.consume(TokenType.IDENTIFIER, "Expected function name")
        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        arguments = []
        if not self.check(TokenType.RPAREN):
            arguments.append(self.initializer())
            while self.match(TokenType.COMMA):
                arguments.append(self.initializer())
        self.consume(TokenType.RPAREN, "Expected ')' after arguments")
        self.consume(TokenType.SEMICOLON, "Expected ';' after function call")
        return {"type": "function_call", 
                "name": name.lexeme, 
                "arguments": arguments}

    def function_statement(self, type_token, name):
        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        parameters = []
        if not self.check(TokenType.RPAREN):
            parameters.append(self.consume_type().lexeme)
            parameters.append(self.consume(TokenType.IDENTIFIER, "Expected parameter name").lexeme)
            while self.match(TokenType.COMMA):
                parameters.append(self.consume_type().lexeme)
                parameters.append(self.consume(TokenType.IDENTIFIER, "Expected parameter name").lexeme)
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")
        self.consume(TokenType.LBRACE, "Expected '{' before function body")
        body = self.block()
        return {"type": "function", 
                "return_type": type_token.lexeme, 
                "name": name.lexeme, 
                "parameters": parameters, 
                "body": body}

    def assignment(self, type_token, name):
        self.consume(TokenType.ASSIGN, "Expected '=' after variable name")
        value = self.initializer()
        self.consume(TokenType.SEMICOLON, "Expected ';' after assignment")
        return {"type": "assignment", 
                "return_type": type_token.lexeme, 
                "name": name.lexeme, 
                "value": value}

    
    # -------------Support Methods-------------
    def is_assign(self) -> bool:
        return (self.check(TokenType.KW_INT)
                or self.check(TokenType.KW_FLOAT) 
                or self.check(TokenType.KW_STRING) 
                or self.check(TokenType.BOOL))

    def assign_type(self):
        type_token = self.advance()
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name after type")
        if self.check(TokenType.LPAREN):
            return self.function_statement(type_token, name)
        return self.assignment(type_token, name)
    
    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def advance(self) -> Token:
        if not self.at_end():
            self.current += 1
        return self.previous()

    def check(self, type_: TokenType) -> bool:
        return self.peek().type == type_

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

