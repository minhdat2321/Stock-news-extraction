import logging
def setup_logger(name:str,debug:bool=False)->logging.Logger:
	C=logging.DEBUG if debug else logging.INFO;A=logging.getLogger(name);A.setLevel(C)
	if not A.handlers:B=logging.StreamHandler();B.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'));A.addHandler(B)
	return A