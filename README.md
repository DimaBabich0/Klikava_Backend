# Klikava Backend

## Install and launch

1. Create virtual environment:
   ```
   python -m venv .venv
   ```

2. Activate virtual environment:
   ```
   .venv\Scripts\activate.bat
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create ".env" file and write all required variables from ".env.example":

5. Launch server FastAPI:
   ```
   python -m uvicorn app.main:app --reload
   ```


## Launch tests
Command for tests:
```
pytest -q
```