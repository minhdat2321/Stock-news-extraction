import requests,pandas as pd
from functools import wraps
from typing import Dict,Any,Callable
from vnstock_news.utils.logger import setup_logger
logger=setup_logger('vnstock_news.utils.helpers')
def retry_request(max_retries=3):
	A=max_retries
	def B(func):
		@wraps(func)
		def B(*C,**D):
			for B in range(A):
				try:return func(*C,**D)
				except Exception as E:
					logger.warning(f"Attempt {B+1} failed: {E}")
					if B==A-1:raise
			raise Exception('Max retries reached.')
		return B
	return B
@retry_request()
def fetch_url_content(url:str,headers:Dict=None,timeout:int=10)->bytes:A=requests.get(url,headers=headers,timeout=timeout);A.raise_for_status();logger.info(f"Successfully fetched content from {url}");return A.content
def standardize_columns(df:pd.DataFrame,mapping:Dict[str,Any])->pd.DataFrame:A={A:B for(B,C)in mapping.items()for A in C if A in df.columns};return df.rename(columns=A)