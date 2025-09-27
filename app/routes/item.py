from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["Items"])

@router.get("/")
async def get_items():
    return {"message": "Hello, World!"}


# @router.post("/")
# async def create_item(item: Item):
#     return {"message": "Item created!"}

