_D='coerce'
_C='url'
_B=None
_A='lastmod'
import requests,pandas as pd
from datetime import datetime
from io import StringIO
from vnstock_news.config.const import DEFAULT_HEADERS
from vnstock_news.utils.logger import setup_logger
class Sitemap:
	def __init__(A,url:str,show_log:bool=False):A.logger=setup_logger(__name__,show_log);A.url=url;A.data=A._load(url)
	def _load(A,url:str)->pd.DataFrame:
		C=url
		try:A.logger.info(f"Attempting to load sitemap directly from {C}");B=pd.read_xml(C);B=A._clean_dataframe(B);A.logger.info('Sitemap loaded successfully using direct parsing.');return B
		except Exception as F:
			A.logger.warning(f"Direct loading failed: {F}. Trying with headers...")
			try:
				D=requests.get(C,headers=DEFAULT_HEADERS,timeout=10);D.raise_for_status()
				if not D.text.strip():raise ValueError('Fetched sitemap content is empty.')
				B=pd.read_xml(StringIO(D.text));B=A._clean_dataframe(B);A.logger.info('Sitemap loaded successfully using fallback method.');return B
			except Exception as E:A.logger.error(f"Failed to load sitemap: {E}");raise ValueError(f"Failed to load sitemap after fallback: {E}")
	@staticmethod
	def _clean_dataframe(df:pd.DataFrame)->pd.DataFrame:
		B='loc';A=df
		if B in A.columns:A.rename(columns={B:_C},inplace=True)
		if _A in A.columns:A[_A]=pd.to_datetime(A[_A],errors=_D)
		return A
	def filter_by_date(D,start:datetime=_B,end:datetime=_B)->pd.DataFrame:
		C=end;B=start;A=D.data
		if _A not in A.columns or A[_A].isnull().all():return A[[_C]]
		A[_A]=pd.to_datetime(A[_A],errors=_D).dt.tz_localize(_B)
		if B:B=pd.Timestamp(B).tz_localize(_B);A=A[A[_A]>=B]
		if C:C=pd.Timestamp(C).tz_localize(_B);A=A[A[_A]<=C]
		return A[[_C,_A]]