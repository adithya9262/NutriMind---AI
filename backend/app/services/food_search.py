from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from decimal import Decimal

import httpx

USDA_API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
OPENFOODFACTS_API_URL = "https://world.openfoodfacts.org/cgi/search.pl"


@dataclass(frozen=True, slots=True)
class FoodSearchItem:
    fdc_id: str
    food_name: str
    brand_name: str | None
    calories_kcal: Decimal
    protein_g: Decimal
    carbohydrate_g: Decimal
    fat_g: Decimal
    fiber_g: Decimal
    sugar_g: Decimal
    serving_size_g: Decimal | None
    serving_description: str | None
    source: str


@dataclass(frozen=True, slots=True)
class FoodSearchResult:
    query: str
    total_results: int
    foods: tuple[FoodSearchItem, ...]
    source: str


class SearchCache:
    def __init__(self, maxsize: int = 100, ttl: int = 300):
        self._cache: OrderedDict[str, tuple[float, FoodSearchResult]] = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl

    def get(self, key: str) -> FoodSearchResult | None:
        if key not in self._cache:
            return None
        timestamp, result = self._cache[key]
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return result

    def set(self, key: str, result: FoodSearchResult) -> None:
        self._cache[key] = (time.time(), result)
        self._cache.move_to_end(key)
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)


_cache = SearchCache()


class FoodSearchService:
    def __init__(self, usda_api_key: str = "") -> None:
        self._usda_api_key = usda_api_key

    async def search(self, query: str, max_results: int = 25) -> FoodSearchResult:
        cache_key = f"{query.lower().strip()}:{max_results}"
        cached = _cache.get(cache_key)
        if cached:
            return cached

        if self._usda_api_key:
            try:
                result = await self._search_usda(query, max_results)
                _cache.set(cache_key, result)
                return result
            except Exception:
                pass

        result = await self._search_openfoodfacts(query, max_results)
        _cache.set(cache_key, result)
        return result

    async def _search_usda(self, query: str, max_results: int) -> FoodSearchResult:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                USDA_API_URL,
                params={"api_key": self._usda_api_key, "query": query, "pageSize": max_results, "dataType": "Foundation,SR Legacy"},
            )
            resp.raise_for_status()
            data = resp.json()

        foods = []
        for item in data.get("foods", [])[:max_results]:
            nutrients = {n.get("nutrientName", ""): n.get("value", 0) for n in item.get("foodNutrients", [])}
            serving_size = item.get("servingSize")
            serving_unit = item.get("servingSizeUnit", "g")
            if serving_size:
                serving_description = f"{int(serving_size)} {serving_unit}" if isinstance(serving_size, (int, float)) else f"{serving_size} {serving_unit}"
            else:
                serving_description = "100 g"
            food = FoodSearchItem(
                fdc_id=str(item.get("fdcId", "")),
                food_name=item.get("description", "Unknown"),
                brand_name=item.get("brandName"),
                calories_kcal=Decimal(str(nutrients.get("Energy", 0) or 0)),
                protein_g=Decimal(str(nutrients.get("Protein", 0) or 0)),
                carbohydrate_g=Decimal(str(nutrients.get("Carbohydrate, by difference", 0) or 0)),
                fat_g=Decimal(str(nutrients.get("Total lipid (fat)", 0) or 0)),
                fiber_g=Decimal(str(nutrients.get("Fiber, total dietary", 0) or 0)),
                sugar_g=Decimal(str(nutrients.get("Sugars, total including NLEA", 0) or 0)),
                serving_size_g=Decimal(str(serving_size)) if serving_size else None,
                serving_description=serving_description,
                source="usda",
            )
            foods.append(food)
        return FoodSearchResult(query=query, total_results=len(foods), foods=tuple(foods), source="usda")

    async def _search_openfoodfacts(self, query: str, max_results: int) -> FoodSearchResult:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                OPENFOODFACTS_API_URL,
                params={"search_terms": query, "page_size": max_results, "json": 1},
            )
            resp.raise_for_status()
            data = resp.json()

        foods = []
        for product in data.get("products", [])[:max_results]:
            nut = product.get("nutriments", {})
            food = FoodSearchItem(
                fdc_id=product.get("code", str(hash(product.get("product_name", "")))),
                food_name=product.get("product_name", "Unknown"),
                brand_name=product.get("brands"),
                calories_kcal=Decimal(str(nut.get("energy-kcal_100g", 0) or 0)),
                protein_g=Decimal(str(nut.get("proteins_100g", 0) or 0)),
                carbohydrate_g=Decimal(str(nut.get("carbohydrates_100g", 0) or 0)),
                fat_g=Decimal(str(nut.get("fat_100g", 0) or 0)),
                fiber_g=Decimal(str(nut.get("fiber_100g", 0) or 0)),
                sugar_g=Decimal(str(nut.get("sugars_100g", 0) or 0)),
                serving_size_g=Decimal(str(product.get("product_quantity", 100))) if product.get("product_quantity") else Decimal("100"),
                serving_description="100 g",
                source="open_food_facts",
            )
            foods.append(food)
        return FoodSearchResult(query=query, total_results=len(foods), foods=tuple(foods), source="open_food_facts")


_user_favorites: dict[str, list[dict]] = {}
_recent_searches: dict[str, list[str]] = {}


def add_favorite(user_id: str, food: dict) -> None:
    if user_id not in _user_favorites:
        _user_favorites[user_id] = []
    existing = [f for f in _user_favorites[user_id] if f.get("fdc_id") == food.get("fdc_id")]
    if not existing:
        _user_favorites[user_id].append(food)


def remove_favorite(user_id: str, fdc_id: str) -> None:
    if user_id in _user_favorites:
        _user_favorites[user_id] = [f for f in _user_favorites[user_id] if f.get("fdc_id") != fdc_id]


def get_favorites(user_id: str) -> list[dict]:
    return _user_favorites.get(user_id, [])


def add_recent_search(user_id: str, query: str) -> None:
    if user_id not in _recent_searches:
        _recent_searches[user_id] = []
    q = query.lower().strip()
    if q in _recent_searches[user_id]:
        _recent_searches[user_id].remove(q)
    _recent_searches[user_id].insert(0, q)
    _recent_searches[user_id] = _recent_searches[user_id][:20]


def get_recent_searches(user_id: str) -> list[str]:
    return _recent_searches.get(user_id, [])
