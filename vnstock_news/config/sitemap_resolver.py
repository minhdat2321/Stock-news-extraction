import re,requests
from datetime import datetime
from bs4 import BeautifulSoup
from vnstock_news.config.const import DEFAULT_HEADERS
from vnstock_news.utils.logger import setup_logger
from typing import Dict,Optional,List
class DynamicSitemapResolver:
	def __init__(A,debug:bool=False):A.logger=setup_logger(A.__class__.__name__,debug);A.cache={}
	def resolve_sitemap_url(A,site_name:str,base_config:Dict)->str:
		C=site_name;E=f"{C}_sitemap"
		if E in A.cache:
			G,F=A.cache[E]
			if(datetime.now()-G).total_seconds()<3600:A.logger.debug(f"Using cached URL for {C}: {F}");return F
		B=base_config.get('sitemap_url','')
		if not B:A.logger.warning(f"No sitemap URL defined for {C}");return''
		D=B
		if re.search('sitemaps-\\d{4}-\\d{2}\\.xml',B)or re.search('news-\\d{4}-\\d{1,2}\\.xml',B):D=A._resolve_monthly_sitemap(C,B)
		elif re.search('post-sitemap\\d+\\.xml',B):D=A._resolve_incremental_sitemap(C,B)
		if D:A.cache[E]=datetime.now(),D
		return D
	def _resolve_monthly_sitemap(F,site_name:str,pattern_url:str)->str:
		D=pattern_url;C=site_name;E=datetime.now();A=E.month;B=E.year
		if C=='tuoitre':return f"https://tuoitre.vn/StaticSitemaps/sitemaps-{B}-{A:02d}.xml"
		elif C=='plo':return f"https://plo.vn/sitemaps/news-{B}-{A:02d}.xml"
		elif C=='baodautu':return f"https://baodautu.vn/sitemaps/news-{B}-{A}.xml"
		elif re.search('-\\d{4}-0\\d\\.xml',D):return re.sub('-\\d{4}-\\d{2}\\.xml',f"-{B}-{A:02d}.xml",D)
		else:return re.sub('-\\d{4}-\\d{1,2}\\.xml',f"-{B}-{A}.xml",D)
	def _resolve_incremental_sitemap(A,site_name:str,pattern_url:str)->str:
		D=pattern_url
		if site_name=='ktsg':
			try:
				E='https://thesaigontimes.vn/sitemap_index.xml';A.logger.debug(f"Checking sitemap index at {E}");F=requests.get(E,headers=DEFAULT_HEADERS,timeout=10);F.raise_for_status();H=BeautifulSoup(F.content,'xml');I=H.find_all('sitemap');B=[]
				for J in I:
					C=J.find('loc')
					if C and'post-sitemap'in C.text:B.append(C.text)
				if B:G=max(B,key=lambda x:int(re.search('post-sitemap(\\d+)\\.xml',x).group(1)));A.logger.info(f"Found latest KTSG sitemap: {G}");return G
			except Exception as K:A.logger.error(f"Error resolving KTSG sitemap: {K}");return D
		return D