# S.A.R.A.L

Simple And Readable Arithmetic Language is a very simple staticly typed scripting language designed and implemented as the final project for `CS609` course at `SEMO`.

### Initial BNF/EBNF

```
<program> ::= <stmt-list>

<stmt-list> ::= <stmt> | <stmt> <stmt-list>

<stmt> ::= <assignment>
          | <show-stmt>
          | <if-stmt>
          | <while-stmt>
          | <func-stmt>
          | <func-call-stmt>
          | <return-stmt>

<show-stmt> ::= show(<string>); | show(<exp>);
<string> ::= "<word>"

<func-stmt> ::= <return-type> <identifier>(<param-list>) <block>
<param-list> ::= epsilon
                | <type> <identifier>
                | <type> <identifier>, <param-list>
<func-call> ::= <identifier>(<arg-list>)
<func-call-stmt> ::= <func-call>;
<arg-list> ::= epsilon
              | <exp>
              | <exp>, <arg-list>

<return-stmt> ::= return <exp>;

<while-stmt> ::= while(<comp-exp>) <block>

<if-stmt> ::= if(<comp-exp>) <block> [else <block>]

<comp-exp> ::= <exp> <comp-op> <exp>
<comp-op> ::=  !=
              | ==
              | <
              | >
              | <=
              | >=

<block> ::= { <stmt-list> }

<assignment> ::= <type> <identifier> = <exp>;
                  | <identifier> = <exp>;

<exp> ::= <exp> + <term>
          | <exp> - <term>
          | <term>

<term> ::= <term> % <factor>
            | <term> / <factor>
            | <term> * <factor>
            | <factor>

<factor> ::= (<exp>)
            | <number>
            | <identifier>
            | <func-call>

<identifier> ::= <letter>
                | <letter><number>
                | <letter><identifier>

<number> ::= <digit>
            | <digit><number>

<word> ::= <chars>
          | <chars><word>
<chars> ::= " "
            | <letter>
            | <digit>
            | <printable-chars>

<printable-chars> ::= @ | ! | # | $
                      | % | ^ | &
                      | * | ( | )
                      | : | ? | ,
                      | _ | \ | /
                      | .

<digit> ::= 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9

<letter> ::= a | b | ... | z | A | B | ..... | Z

<type> ::= int | float | string | bool

<return-type> ::= int | float | string | bool
```

### Sample programs

```title="Odd or Even"
int num = 4;

if (num % 2 == 0) {
  show("Even");
} else {
  show("Odd");
}
```

```title="While loop"
int n = 0;

while (n < 5) {
  show(n);
  n = n+1;
}
```

```title="Function call"
bool isMeme(int num) {
  if (num == 67) {
    show("SIX SEVEN");
    return true;
  }

  return false;
}
```
