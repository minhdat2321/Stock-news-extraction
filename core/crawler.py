_B='records'
_A=None
from.news import News
from vnstock_news.config.sites import SITES_CONFIG
from vnstock_news.utils import setup_logger
from typing import Dict,Optional
class Crawler:
	def __init__(A,site_name:Optional[str]=_A,use_predefined_config:bool=True,custom_config:Optional[Dict]=_A,debug:bool=False):
		C=use_predefined_config;B=site_name;A.logger=setup_logger(A.__class__.__name__,debug);A.logger.debug('Initializing Crawler...');A.use_predefined_config=C
		if C:
			if not B:raise ValueError("When 'use_predefined_config' is True, 'site_name' must be provided.")
			if B not in SITES_CONFIG:raise ValueError(f"Site '{B}' is not supported. Choose from: {list(SITES_CONFIG.keys())}")
			A.logger.info(f"Using predefined configuration for site: {B}");D=SITES_CONFIG[B];A.sitemap_url=D['sitemap_url'];A.config=D['config']
		else:A.logger.warning('No predefined configuration. Using custom configuration instead.');A.sitemap_url=_A;A.config=custom_config or{}
		A.parser=News(A.sitemap_url,A.config)
	def get_latest_articles(A,limit:int=10)->list:
		B=limit
		if not A.use_predefined_config:raise ValueError('get_latest_articles() requires predefined configuration with a sitemap URL.')
		if not A.sitemap_url:raise ValueError('No sitemap URL is defined for this site.')
		A.logger.info(f"Fetching latest {B} articles from sitemap: {A.sitemap_url}");C=A.parser.filter_by_date();return C.head(B).to_dict(_B)
	def get_article_details(A,url:str,custom_config:Optional[Dict]=_A)->Dict:
		D=custom_config;B=url;A.logger.debug(f"Fetching article details for URL: {B}");C=A.parser
		if not A.use_predefined_config and D:A.logger.info('Using custom configuration for parsing.');C=News(url='',config=D)
		try:E=C.extract_detail(B);E['markdown_content']=C.article_to_markdown(B);A.logger.info(f"Successfully fetched details for {B}");return E
		except Exception as F:A.logger.error(f"Failed to fetch article details for {B}: {F}");return{'error':str(F)}
	def get_articles_from_feed(A,sources:list,limit_per_feed:int=10)->list:C=limit_per_feed;B=sources;from.batch import BatchCrawler as D;A.logger.info(f"Fetching articles from {len(B)} feeds with limit {C} per feed.");E=D(site_name=A.site_name,custom_config=A.config,debug=False);F=E.fetch_articles(sources=B,top_n_per_feed=C,top_n=_A);return F.to_dict(_B)