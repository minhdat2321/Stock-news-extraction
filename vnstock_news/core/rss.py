_C='markdown'
_B='text'
_A=None
import requests,pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser
from io import StringIO
from vnstock_news.config.const import DEFAULT_HEADERS
from vnstock_news.config.sites import SITES_CONFIG,DEFAULT_RSS_MAPPING
import html2text
from vnstock_news.utils.logger import setup_logger
class RSS:
	def __init__(A,site_name:str=_A,description_format:str=_B,rss_url:str=_A,show_log:bool=False):
		E='urls';D=rss_url;B=site_name;A.logger=setup_logger(__name__,show_log);A.description_format=description_format.lower();A.rss_urls=[];A.key_mapping=DEFAULT_RSS_MAPPING
		if A.description_format not in{_B,'html',_C}:raise ValueError("description_format must be 'text', 'html', or 'markdown'.")
		if B:
			F=SITES_CONFIG.get(B,{});C=F.get('rss',_A)
			if not C or E not in C:raise ValueError(f"RSS configuration not found for site '{B}'.")
			A.rss_urls=C[E];A.key_mapping=C.get('mapping',DEFAULT_RSS_MAPPING);A.logger.debug(f"Using predefined RSS URLs for site '{B}': {A.rss_urls}")
		if D:A.rss_urls=[D];A.logger.debug(f"Manual RSS URL provided: {D}")
		if not A.rss_urls:raise ValueError('No RSS feed URLs available. Provide either a site_name or a custom rss_url.')
	def fetch_feeds(A)->pd.DataFrame:
		C=[]
		for B in A.rss_urls:
			try:
				A.logger.info(f"Fetching RSS feed: {B}");E=requests.get(B,headers=DEFAULT_HEADERS,timeout=10);E.raise_for_status();F=BeautifulSoup(E.content,'xml')
				for G in F.find_all('item'):H={B:A._process_field(G,C,B)for(B,C)in A.key_mapping.items()};C.append(H)
			except requests.exceptions.RequestException as D:A.logger.error(f"Error fetching RSS feed {B}: {D}")
			except Exception as D:A.logger.error(f"Unexpected error while processing RSS feed {B}: {D}")
		if not C:A.logger.warning('No articles were parsed from the RSS feeds.');return pd.DataFrame(columns=list(A.key_mapping.keys()))
		return pd.DataFrame(C)
	def _process_field(A,item,rss_key,field_key):
		D=field_key;C=rss_key;B=item
		try:
			if D=='description':
				G=B.find(C)
				if not G:return
				E=G.text.strip()
				if A.description_format==_B:return BeautifulSoup(E,'html.parser').get_text()
				elif A.description_format==_C:H=html2text.HTML2Text();H.ignore_links=False;return H.handle(E)
				else:return E
			elif D=='publish_time':
				I=B.find(C)
				if I:
					try:K=parser.parse(I.text.strip(),fuzzy=True);return K.strftime('%Y-%m-%d %H:%M:%S')
					except Exception as F:A.logger.warning(f"Error parsing publish_time: {F}");return
			J=B.find(C);return J.text.strip()if J else _A
		except Exception as F:A.logger.error(f"Error processing field '{D}': {F}");return