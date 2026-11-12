from dotenv import dotenv_values
import os
vals=dotenv_values('.env')
token=vals.get('TIINGO_API_KEY') or os.environ.get('TIINGO_API_KEY')
print('TIINGO_TOKEN_AVAILABLE', bool(token))
