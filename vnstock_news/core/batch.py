_I='lastmod'
_H='feed_time'
_G='feed_source'
_F='sitemap'
_E='rss'
_D='publish_time'
_C=False
_B='link'
_A=None
import os,requests,pandas as pd
from datetime import datetime,timedelta,timezone
from time import sleep
from tqdm import tqdm
from .crawler import Crawler
from .rss import RSS
from .sitemap import Sitemap
from vnstock_news.utils import setup_logger
from typing import List,Union
class BatchCrawler:
	def __init__(A,site_name:str=_A,custom_config:dict=_A,debug:bool=_C,request_delay:float=1.,temp_file:str='temp_articles.csv',output_path:str=_A):C=debug;B=site_name;A.logger=setup_logger(A.__class__.__name__,C);A.logger.debug('Initializing BatchCrawler...');A.use_predefined_config=bool(B);A.site_name=B;A.custom_config=custom_config;A.request_delay=request_delay;A.temp_file=temp_file;A.output_path=output_path;A.crawler=Crawler(B,debug=C)if A.use_predefined_config else _A
	def _detect_source_type(E,url:str)->str:
		A=url
		if A.endswith('.rss'):return _E
		elif A.endswith('.xml'):return _F
		else:
			try:
				C=requests.get(A,timeout=10);C.raise_for_status();B=C.content.decode('utf-8').strip()
				if'<rss'in B or'<channel>'in B:return _E
				elif'<urlset'in B:return _F
			except Exception as D:E.logger.error(f"Failed to detect source type for {A}: {D}");raise ValueError(f"Failed to detect source type for {A}: {D}")
			raise ValueError('Unknown source format.')
	def prepare_feeder(A,sources:List[str],top_n_per_feed:int=_A)->pd.DataFrame:
		E=top_n_per_feed;D=[]
		for B in sources:
			try:
				A.logger.info(f"Checking source: {B}");F=A._detect_source_type(B)
				if F==_E:A.logger.info(f"Parsing RSS feed: {B}");G=RSS(rss_url=B);C=G.fetch_feeds()
				elif F==_F:A.logger.info(f"Parsing XML sitemap: {B}");H=Sitemap(B);C=H.data
				C[_G]=B;C[_H]=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
				if not C.empty:
					if E:C=C.head(E)
					D.append(C)
				else:A.logger.warning(f"No articles found for {B}.")
			except Exception as I:A.logger.error(f"Error processing {B}: {I}")
		if D:A.feed_df=pd.concat(D,ignore_index=True);return A.feed_df
		else:A.logger.warning('No valid data fetched from the provided sources.');return pd.DataFrame(columns=[_B,_D,'title','description'])
	def filter_feeder(D,feeder:pd.DataFrame,top_n:int=_A,within:str=_A,sort_order:str='desc')->pd.DataFrame:
		E=within;C=top_n;A=feeder.copy();F=[_D,_I,'pubDate'];B=next((B for B in F if B in A.columns),_A)
		if not B:D.logger.warning('No valid time column found (publish_time, lastmod, pubDate). Skipping sorting/filtering by time.');return A.head(C)if C else A
		A[B]=pd.to_datetime(A[B],errors='coerce').dt.tz_localize(_A)
		if E:G=datetime.now(timezone.utc).replace(tzinfo=_A);H=D._parse_time_frame(E);I=G-H;A=A[A[B]>=I]
		J=sort_order=='asc';A=A.sort_values(by=B,ascending=J)
		if C:A=A.head(C)
		return A
	def _parse_time_frame(D,time_str:str)->timedelta:
		C=time_str;A=C[-1];B=int(C[:-1])
		if A=='h':return timedelta(hours=B)
		elif A=='d':return timedelta(days=B)
		elif A=='m':return timedelta(minutes=B)
		else:raise ValueError("Invalid time frame format. Use 'h' for hours, 'd' for days, or 'm' for minutes.")
	def _save_temp_data(A,data:pd.DataFrame):
		try:data.to_csv(A.temp_file,index=_C);A.logger.info(f"Intermediate data saved to {A.temp_file}")
		except Exception as B:A.logger.error(f"Failed to save intermediate data: {B}")
	def _load_temp_data(A)->pd.DataFrame:
		if os.path.exists(A.temp_file):
			try:A.logger.info(f"Loading intermediate data from {A.temp_file}");return pd.read_csv(A.temp_file)
			except Exception as B:A.logger.error(f"Failed to load intermediate data: {B}")
		return pd.DataFrame()
	def fetch_articles(A,sources:Union[List[str],str],top_n:int=10,top_n_per_feed:int=_A,within:str=_A,sort_order:str='desc',save_to_file:bool=_C)->pd.DataFrame:
		D=sources
		if isinstance(D,str):D=[D]
		C=A.prepare_feeder(D,top_n_per_feed=top_n_per_feed);C.columns=[A.lower()for A in C.columns];C=C.rename(columns={'url':_B,'loc':_B,'pubdate':_D,_I:_D});F=A.filter_feeder(C,top_n=top_n,within=within,sort_order=sort_order)
		if not A.crawler:A.crawler=Crawler(use_predefined_config=_C,custom_config=A.custom_config)
		E=[];J=A._load_temp_data();A.logger.info(f"Fetching details for {len(F)} articles...")
		for(L,B)in tqdm(F.iterrows(),total=len(F),desc='Fetching Articles'):
			if B[_B]in J.get(_B,[]):A.logger.info(f"Skipping already fetched article: {B[_B]}");continue
			try:
				G=A.crawler.get_article_details(B[_B]);G[_G]=B[_G];G[_H]=B[_H];E.append(G);sleep(A.request_delay)
				if len(E)%10==0:K=pd.DataFrame(E);A._save_temp_data(K)
			except Exception as H:A.logger.error(f"Failed to process {B[_B]}: {H}")
		I=pd.DataFrame(E)
		if save_to_file and A.output_path:
			try:I.to_csv(A.output_path,index=_C);A.logger.info(f"Final data saved to {A.output_path}")
			except Exception as H:A.logger.error(f"Failed to save final data: {H}")
		A._save_temp_data(I);return I