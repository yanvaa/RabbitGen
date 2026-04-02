from fastapi import FastAPI, HTTPException
from rabbit import Rabbit, RabbitHelper
from family_tree import EnhancedFamilyTreeArtist
from ascii import AsciiToImageConverter
from pydantic import BaseModel
from typing import List, Union
import random
import os
import base64
import io
from PIL import Image, ImageDraw
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "Gen"),
    debug=os.getenv("APP_DEBUG", "True").lower() == "true"
)
rabbit_helper = RabbitHelper()

class CreateRabbitRequest(BaseModel):
    nickname: str
    genom: Union[List[int], None]
    parents: Union[List[int], None]

class BreedRequest(BaseModel):
    mother_id: int
    father_id: int

def image_to_base64(img: Image.Image) -> str:
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

@app.post("/rabbits/", 
          summary="Создать нового кролика",
          response_description="Информация о созданном кролике")
async def create_rabbit(request: CreateRabbitRequest):
    if request.genom is None:
        request.genom = [random.randint(0, 9) for _ in range(4)]
    
    rabbit = Rabbit(request.nickname, request.genom, request.parents or [])
    return rabbit.to_json()

@app.get("/rabbits/{rabbit_id}", 
         summary="Получить информацию о кролике")
async def get_rabbit(rabbit_id: int):
    try:
        rabbit = Rabbit.from_db(rabbit_id)
        return rabbit.to_json()
    except ValueError:
        raise HTTPException(status_code=404, detail="Rabbit not found")

@app.post("/rabbits/breed/", 
          summary="Скрестить двух кроликов",
          response_description="Список созданных детенышей")
async def breed_rabbits(request: BreedRequest):
    try:
        mother = Rabbit.from_db(request.mother_id)
        father = Rabbit.from_db(request.father_id)
        
        if mother.gender != "female":
            raise HTTPException(
                status_code=400, 
                detail="Mother must be female rabbit"
            )
        
        children = mother.breed(father)
        return [child.to_json() for child in children]
    except ValueError:
        raise HTTPException(status_code=404, detail="Rabbit not found")

@app.get("/rabbits/{rabbit_id}/family-tree", 
         summary="Получить семейное древо кролика")
async def get_family_tree(
    rabbit_id: int, 
    depth: int = 3
):
    try:
        rabbit = Rabbit.from_db(rabbit_id)
        tree_data = rabbit.get_family_tree(depth)
        
        return {"tree_data": tree_data}
    except ValueError:
        raise HTTPException(status_code=404, detail="Rabbit not found")

@app.get("/rabbits/{rabbit_id}/family-tree-png", 
         summary="Получить семейное древо кролика")
async def get_family_tree(
    rabbit_id: int, 
    depth: int = 3
):
    try:
        rabbit = Rabbit.from_db(rabbit_id)
        tree_data = rabbit.get_family_tree(depth)
        
        artist = EnhancedFamilyTreeArtist()
        tree_text = artist.draw_tree(tree_data)
        
        converter = AsciiToImageConverter()
        
        lines = tree_text.split('\n')
        width = max(len(line) for line in lines) * converter.char_width
        height = len(lines) * converter.char_height
        
        img = Image.new('RGB', (width, height), "#1a1b26")
        draw = ImageDraw.Draw(img)
        
        y = 30
        for line in lines:
            draw.text((0, y), line, fill="#c0caf5", font=converter.font)
            y += converter.char_height
        
        return {"image_base64": image_to_base64(img)}
    except ValueError:
        raise HTTPException(status_code=404, detail="Rabbit not found")

@app.get("/rabbits/{rabbit_id}/image/", 
         summary="Получить изображение кролика")
async def get_rabbit_image(rabbit_id: int):
    try:
        rabbit = Rabbit.from_db(rabbit_id)
        converter = AsciiToImageConverter()
        
        img = converter.convert_rabbit(rabbit)
        
        return {"image_base64": image_to_base64(img)}
    except ValueError:
        raise HTTPException(status_code=404, detail="Rabbit not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("APP_HOST", "0.0.0.0"), port=int(os.getenv("APP_PORT", "8000")))