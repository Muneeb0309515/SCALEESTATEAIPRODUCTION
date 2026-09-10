import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.data.schemas import PropertyRecord, PropertySearchCriteria, PaginatedPropertyResults

class RealtyApiAdapter:
    """
    Adapter for the official RealtyAPI.io Realtor US API.
    Maps RealtyAPI.io's /search/bylocation and /details/byaddress endpoints
    to the canonical SCALEESTATE AI property schema.
    """
    
    def __init__(self):
        self.base_url = settings.PROPERTY_DATA_BASE_URL or "https://realtor.realtyapi.io"
        self.api_key = settings.PROPERTY_DATA_API_KEY
        self.headers = {"x-realtyapi-key": self.api_key} if self.api_key else {}
        
    async def search_properties(self, criteria: PropertySearchCriteria) -> PaginatedPropertyResults:
        if not self.api_key:
            return PaginatedPropertyResults(results=[], total=0, next_token=None)
            
        # Map canonical criteria to RealtyAPI.io /search/bylocation parameters
        params = {}
        if criteria.location:
            params["location"] = criteria.location
        if criteria.min_price is not None:
            params["price_min"] = criteria.min_price
        if criteria.max_price is not None:
            params["price_max"] = criteria.max_price
        if criteria.min_beds is not None:
            params["beds_min"] = criteria.min_beds
        if criteria.min_baths is not None:
            params["baths_min"] = criteria.min_baths
        if criteria.property_type:
            # Basic mapping; RealtyAPI supports specific type slugs
            params["type"] = criteria.property_type.lower()
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/bylocation",
                headers=self.headers,
                params=params,
                timeout=30.0
            )
            
            if response.status_code != 200:
                return PaginatedPropertyResults(results=[], total=0, next_token=None)
                
            data = response.json()
            results = []
            
            # Map RealtyAPI.io search results to canonical PropertyRecord
            for item in data.get("data", {}).get("results", []):
                record = self._map_to_canonical(item)
                if record:
                    results.append(record)
                    
            return PaginatedPropertyResults(
                results=results,
                total=data.get("data", {}).get("total", len(results)),
                next_token=None # RealtyAPI pagination handling would go here
            )
            
    async def get_property_details(self, address: str) -> Optional[PropertyRecord]:
        if not self.api_key:
            return None
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/details/byaddress",
                headers=self.headers,
                params={"address": address},
                timeout=30.0
            )
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            detail = data.get("detail")
            if not detail:
                return None
                
            return self._map_to_canonical(detail)
            
    def _map_to_canonical(self, item: Dict[str, Any]) -> Optional[PropertyRecord]:
        """Map a RealtyAPI.io property object to the canonical PropertyRecord."""
        try:
            address_data = item.get("address", {})
            details_data = item.get("details", {})
            
            # Extract basic fields
            street = address_data.get("line", "")
            city = address_data.get("city", "")
            state = address_data.get("state_code", "")
            zip_code = address_data.get("postal_code", "")
            
            if not street or not city or not state:
                return None
                
            full_address = f"{street}, {city}, {state} {zip_code}".strip()
            
            # Extract price and specs
            price = item.get("list_price") or item.get("last_sold_price") or 0
            beds = details_data.get("beds") or 0
            baths = float(details_data.get("baths") or 0)
            sqft = details_data.get("sqft") or 0
            year_built = details_data.get("year_built")
            property_type = details_data.get("type", "unknown")
            
            # Extract coordinates
            lat = address_data.get("latitude")
            lng = address_data.get("longitude")
            
            # Extract photos
            photos = []
            if "photos" in item:
                for photo in item["photos"]:
                    if isinstance(photo, dict) and "href" in photo:
                        photos.append(photo["href"])
                    elif isinstance(photo, str):
                        photos.append(photo)
                        
            return PropertyRecord(
                id=item.get("property_id", ""),
                address=full_address,
                street=street,
                city=city,
                state=state,
                zip_code=zip_code,
                price=price,
                beds=beds,
                baths=baths,
                sqft=sqft,
                year_built=year_built,
                property_type=property_type,
                latitude=lat,
                longitude=lng,
                status=item.get("status", "unknown"),
                photos=photos,
                source="RealtyAPI.io (Realtor)",
                raw_data=item
            )
        except Exception:
            return None
