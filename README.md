# Fact-checking AI Agent

> Make sure to create a file named `API_KEY.py`.
> In this file, add the following content:
> ```python
> OLLAMA_API_KEY = "your Ollama API key"
> """ API key for accessing Ollama """
> 
> TAVILY_API_KEY = "your Tavily API key"
> """ API key for accessing Tavily """
> ```
> Then, you can import and use it in your code as follows:
> ```python
> from API_KEY import OLLAMA_API_KEY as API_KEY
> ```
> or
> ```python
> from API_KEY import TAVILY_API_KEY as API_KEY
> ```
> 
> WARNING: Do not share your API key publicly.

---

## Installation & Setup

### 1. Create Virtual Environment
Run the following command to create a virtual environment named `.venv`:
```bash
python -m venv .venv
```

### 2. Activate Virtual Environment
Choose the command corresponding to your operating system:
#### For Windows (CMD):
```Bash
.venv\Scripts\activate.bat
```
#### For Windows (PowerShell / VS Code):
```Bash
.venv\Scripts\Activate.ps1
```
#### For Mac / Linux:
```Bash
source .venv/bin/activate
```

### 3. Install Dependencies
Once the environment is activated (you should see (.venv) in your terminal), install the required packages:
```Bash
pip install -r requirements.txt
```

---

## Development Workflow

### Adding New Modules
If you install any new package during development, please update the requirements file so others can sync:
```Bash
pip freeze > requirements.txt
```
Then commit and push the updated requirements.txt to the repository.

---
