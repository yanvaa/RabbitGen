import requests
import json
from PIL import Image
from io import BytesIO
import base64

BASE_URL = "http://localhost:8000"

def create_rabbit():
    """Создание нового кролика"""

    nickname = input("Имя кролика (Enter для значения по умолчанию): ") or None
    genom = input("Геном [0-9,0-9,0-9,0-9] (Enter чтобы пропустить): ") or None
    parents = input("ID родителей через запятую (Enter чтобы пропустить): ") or None
    
    data = {
        "nickname": nickname,
        "genom": genom,
        "parents": parents
    }
    
    response = requests.post(f"{BASE_URL}/rabbits/", json=data)
    handle_response(response)

def get_rabbit():
    """Получение информации о кролике"""

    rabbit_id = input("Введите ID кролика: ")
    response = requests.get(f"{BASE_URL}/rabbits/{rabbit_id}")
    handle_response(response)

def breed_rabbits():
    """Скрещивание кроликов"""

    mother_id = input("ID кролика-матери: ")
    father_id = input("ID кролика-отца: ")
    response = requests.post(
        f"{BASE_URL}/rabbits/breed/",
        json={'mother_id': mother_id, 'father_id': father_id}
    )
    handle_response(response)

def get_family_tree():
    """Получение семейного древа"""

    rabbit_id = input("Введите ID кролика: ")
    depth = input("Глубина древа [3]: ") or 3
    response = requests.get(
        f"{BASE_URL}/rabbits/{rabbit_id}/family-tree",
        params={'depth': depth}
    )
    handle_response(response)

def get_family_tree_png():
    """Получение древа в формате PNG"""

    rabbit_id = input("Введите ID кролика: ")
    depth = input("Глубина древа [3]: ") or 3
    response = requests.get(
        f"{BASE_URL}/rabbits/{rabbit_id}/family-tree-png",
        params={'depth': depth}
    )
    handle_response(response, is_image=True)

def get_rabbit_image():
    """Получение изображения кролика"""

    rabbit_id = input("Введите ID кролика: ")
    response = requests.get(f"{BASE_URL}/rabbits/{rabbit_id}/image/")
    handle_response(response, is_image=True)

def handle_response(response, is_image=False):
    """Обработка ответа сервера"""
    if response.status_code == 200:
        if is_image:
            print(f"Успешно! Размер данных: {len(response.content)} байт")
            print(f"Base64: {response.json()['image_base64'][:30]}...")
            img = Image.open(BytesIO(base64.b64decode(response.json()['image_base64'])))
            img.save("client-res.png")
        else:
            print("Успешный ответ:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Ошибка: {response.status_code}")
        print(response.text)

def main():
    """Главное меню"""
    
    actions = {
        '1': create_rabbit,
        '2': get_rabbit,
        '3': breed_rabbits,
        '4': get_family_tree,
        '5': get_family_tree_png,
        '6': get_rabbit_image
    }

    menu = """
=== Rabbit API Client ===
1. Создать кролика
2. Получить информацию о кролике
3. Скрестить кроликов
4. Получить семейное древо (текст)
5. Получить семейное древо (PNG)
6. Получить изображение кролика
0. Выход
Выберите действие: """
    
    while True:
        choice = input(menu).strip()
        if choice == '0':
            break
        if choice in actions:
            try:
                actions[choice]()
            except Exception as e:
                print(f"Ошибка: {e}")
        else:
            print("Неверный ввод, попробуйте снова")

if __name__ == "__main__":
    main()