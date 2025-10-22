_A='html.parser'
import requests
from bs4 import BeautifulSoup
import html2text
from typing import Dict,Optional
from.sitemap import Sitemap
from vnstock_news.config.const import DEFAULT_HEADERS
from vnstock_news.utils.logger import setup_logger
class News(Sitemap):
	def __init__(A,url:str,config:Dict,show_log:bool=False):super().__init__(url);A.config=config;A.logger=setup_logger(__name__,show_log)
	def extract_detail(A,url:str)->Dict:
		C=url
		try:A.logger.debug(f"Fetching article: {C}");D=requests.get(C,timeout=10,headers=DEFAULT_HEADERS);D.raise_for_status();B=BeautifulSoup(D.text,_A);E={'title':A._get_text(B,A.config.get('title_selector')),'short_description':A._get_text(B,A.config.get('short_desc_selector')),'publish_time':A._get_text(B,A.config.get('publish_time_selector')),'author':A._get_text(B,A.config.get('author_selector')),'url':C};A.logger.debug(f"Article details extracted successfully: {E}");return E
		except Exception as F:A.logger.error(f"Failed to fetch or parse article: {F}");return{'error':f"Failed to fetch or parse article: {F}"}
	def article_to_markdown(A,url:str,retain_links=True,retain_images=True)->str:
		try:
			A.logger.debug(f"Converting article to Markdown: {url}");D=requests.get(url,timeout=10,headers=DEFAULT_HEADERS);D.raise_for_status();G=BeautifulSoup(D.text,_A);B=A.config.get('content_selector')
			if not B:raise ValueError("Missing 'content_selector' in configuration.")
			E=G.find(B['tag'],class_=B['class'])
			if not E:raise ValueError('Content not found with the given selector.')
			C=html2text.HTML2Text();C.ignore_links=not retain_links;C.ignore_images=not retain_images;H=C.handle(str(E));A.logger.debug('Article converted to Markdown successfully.');return H
		except Exception as F:A.logger.error(f"Error converting article to Markdown: {F}");return f"Error converting article to Markdown: {F}"
	@staticmethod
	def _get_text(soup:BeautifulSoup,selector:Optional[Dict])->Optional[str]:
		A=selector
		if not A:return
		B=soup.find(A.get('tag'),class_=A.get('class'));return B.get_text(strip=True)if B else None