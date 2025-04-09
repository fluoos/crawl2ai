from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DeleteItemsRequest(BaseModel):
    ids: List[int]