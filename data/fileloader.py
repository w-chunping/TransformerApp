# fileloader.py
import pandas as pd

def load_excel_file(filepath: str, sheetname: str) -> pd.DataFrame:
    return pd.read_excel(filepath, sheet_name=sheetname, header=None, engine='xlrd')
