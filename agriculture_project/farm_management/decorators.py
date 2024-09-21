from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from .models import Farm
import logging

def farm_owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        logging.debug(f"farm_owner_required called with request.user: {request.user}")

        farm_id = kwargs.get('farm_id')
        logging.debug(f"Extracted farm_id from kwargs: {farm_id}")
        
        if not farm_id:
            raise ValueError("farm_id must be provided in URL kwargs")
        
        farm = get_object_or_404(Farm, id=farm_id)
        logging.debug(f"Farm found: {farm}, owned by {farm.user}")

        if farm.user != request.user:  # Check ownership
            logging.debug(f"Permission denied. Farm owner: {farm.owner}, request.user: {request.user}")
            raise PermissionDenied("You are not the owner of this farm.")
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
