web: python -c "import os; not os.path.exists('chimei.db') and __import__('seed').seed()" && uvicorn main:app --host 0.0.0.0 --port $PORT
