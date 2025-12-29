from concurrent.futures import ThreadPoolExecutor, Future
from typing import Union, Dict, Any, Optional

from scraper.Retriever import Retriever
from scraper.EvidenceFileHandler import EvidenceFileHandler

class EvidenceRetrieveHandler():
    """
    Manages asynchronous retrieval tasks using a thread pool.
    Acts as the controller between the request, the retriever, and the file storage.
    """

    BASIC = Retriever.BASIC
    ADVANCED = Retriever.ADVANCED

    def __init__(self, max_search_requests: int = 5):
        """
        Args:
            max_search_requests (int): Max concurrent API requests.
        """
        self.__executor = ThreadPoolExecutor(max_workers=max_search_requests)
        self.__retriever = Retriever()

    def query(
            self, 
            query: dict, 
            *, 
            use_local_TF: bool = False, 
            chunk_count: int =3, 
            result_count: int = 3, 
            level: str = BASIC
            ) -> Union[Future, EvidenceFileHandler, None]:
        """
        Initiates a search query.

        Args:
            query (dict): Must contain "query" key.
            use_local_TF (bool): If True, checks local storage first.
            result_count (int): Max results to fetch from API.
            level (str): 'basic' or 'advanced'.

        Returns:
            Future: If a new API request is started.
            EvidenceFileHandler: If found in local cache.
            None: If query is invalid.
        """
        if "query" not in query or not query["query"]:
            return None
        
        # 1. Check Local Cache (Index Search)
        if use_local_TF:
            cached_handler = EvidenceFileHandler.find_query(query["query"])
            if cached_handler:
                print(f"✅ Found in cache: {query['query']}")
                return cached_handler

        # 2. Prepare API Args
        args = query.copy()
        args["level"] = level
        args["result_count"] = result_count
        args["chunk_count"] = chunk_count

        # 3. Submit to Thread Pool
        future = self.__executor.submit(self.__retrieve_and_store, args)

        return future
    
    def __retrieve_and_store(self, args: dict) -> dict:
        """
        Worker function: retrieves data and saves to file.
        """
        response = self.__retriever.retrieve(args)
        
        if response:
            file_handler = EvidenceFileHandler.store(response)
            response["file_id"] = file_handler.get_filename()
            file_handler.close()
            
        return response
    
    def shutdown(self, wait: bool = True, cancel_futures: bool = True):
        """Shuts down the executor."""
        self.__executor.shutdown(wait=wait, cancel_futures=cancel_futures)
