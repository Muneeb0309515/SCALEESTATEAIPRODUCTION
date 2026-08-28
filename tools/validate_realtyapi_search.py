import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.providers.realtyapi import RealtyApiAdapter, RealtySearchCriteria

async def main():
    response = await RealtyApiAdapter().search(RealtySearchCriteria(location="Austin, TX", page=1, limit=3))
    print({"provider": response.provider, "total": response.total, "returned": len(response.results), "has_next_page": response.has_next_page, "sources": sorted({item.source for item in response.results}), "fields_present": sorted({field for item in response.results for field, value in item.model_dump().items() if value is not None})})

if __name__ == "__main__":
    asyncio.run(main())
