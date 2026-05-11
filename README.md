# Klikava Backend

## Install and launch

1. Activate virtual environment:
   ```
   Scripts\activate.bat
   ```

2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create ".env" file and write all required variables from ".env.example":

4. Launch server FastAPI:
   ```
   python -m uvicorn app.main:app --reload
   ```
