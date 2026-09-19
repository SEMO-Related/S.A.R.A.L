# S.A.R.A.L

Simple And Readable Arithmetic Language is a very simple staticly typed scripting language designed and implemented as the final project for `CS609` course at `SEMO`.

### BNF/EBNF Grammar

You can find the grammar for `saral` in here [Grammar](https://github.com/SEMO-Related/S.A.R.A.L/blob/main/grammar/grammar.ebnf)

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

### Getting Started

To get started with the development of the Saral language, you can follow the steps below.

#### Clone the repo

```bash
git clone https://github.com/SEMO-Related/S.A.R.A.L.git
```

#### Create a python virtual environment

```bash
python -m venv .venv
```

#### Start the virtual environment

`Windows`

```bash title="In bash"
.venv/Scripts/activate
```

`Powershell`

```powershell title="In Powershell"
.\venv\Scripts\Activate.ps1
```

`Mac`

```bash
source .venv/bin/activate
```

#### Install all the requirements

```bash
pip install -r requirements.txt
```

#### Install the saral lexer cli

```bash
pip install -e .
```

#### Run the test file

```bash
python -m saral.cli tokenize <path-to-sample-file>
```

```bash
python -m saral.cli parse <path-to-sample-file>
```

Or hit `F5` in VSCode to run lexer on sample file

### Testing

To test the lexer you can simply run the command `pytest`. It will run all the test cases written inside `tests/lexer/test_lexer.py`
