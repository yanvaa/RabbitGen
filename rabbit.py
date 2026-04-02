import os
import json
import random
from mangodb import RabbitMongoDB
from typing import Dict, List, Union
from family_tree import PopulationGraph
from dotenv import load_dotenv

load_dotenv()

class RabbitHelper:
    def __init__(self, json_path: str = 'rabbit_data.json'):
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.health_states = self.data['health_states']
        self.fertilities = self.data['fertilities']
        self.name_parts = self.data['name_parts']
        self.longevity = self.data['longevity']
    
    def get_fertility_by_id(self, fertility_id: int) -> Dict:
        for fert in self.fertilities:
            if fert['id'] == fertility_id:
                return fert
        return self.fertilities[0]
    
    def get_random_fertility(self) -> Dict:
        return random.choice(self.fertilities)
    
    def get_fertility_description(self, fertility_id: int, gender: str) -> str:
        fert = self.get_fertility_by_id(fertility_id)
        return fert['description'].get(gender, fert['description']['male'])
    
    def generate_name(self, genom: List[int]) -> str:
        parts = [
            self.name_parts['prefix'][genom[0] % len(self.name_parts['prefix'])],
            self.name_parts['suffix'][genom[1] % len(self.name_parts['suffix'])],
            self.name_parts['nickname'][genom[2] % len(self.name_parts['nickname'])],
            self.name_parts['surname'][genom[3] % len(self.name_parts['surname'])]
        ]
        return f"{parts[0]}{parts[1]} {parts[2]} {parts[3]}"
    
    def calculate_offspring(self, parent1_fert: Dict, parent2_fert: Dict) -> Union[int, None]:
        if random.random() > (parent1_fert['stats']['value'] + parent2_fert['stats']['value']) / 2:
            return 0
        
        min_kits = min(parent1_fert['stats']['min_kits'], parent2_fert['stats']['min_kits'])
        max_kits = max(parent1_fert['stats']['max_kits'], parent2_fert['stats']['max_kits'])
        return random.randint(min_kits, max_kits)

    def get_health_state(self, hpid: int) -> Dict:
        for state in self.health_states:
            if state['id'] == hpid:
                return state
        return self.health_states[-1]

    def get_health_description(self, hp: int, is_sick: bool = False) -> str:
        state = self.get_health_state(hp)
        key = "sick" if is_sick else "healthy"
        return state['descriptions'].get(key, "Неизвестное состояние")

    def simulate_health_change(self, current_hp: int) -> int:
        state = self.get_health_state(current_hp)
        if random.random() < state['recovery_chance']:
            return min(100, current_hp + random.randint(1, 10))
        return max(1, current_hp - random.randint(1, 15))

    def generate_health_report(self, rabbit: Dict) -> str:
        is_sick = random.random() > 0.5 
        description = self.get_health_description(rabbit['hp'], is_sick)
        
        return (
            f"Состояние здоровья: {description}\n"
            f"HP: {rabbit['hp']}/100\n"
            f"Рекомендации: {'Требуется лечение' if is_sick else 'Всё в порядке'}"
        )
    
    def get_longevity_by_id(self, longevity_id: int) -> Dict:
        for group in self.longevity:
            if group['id'] == longevity_id:
                return group
        return self.longevity[1]

class Rabbit:
    db = RabbitMongoDB(uri=os.getenv("DATABASE_URL"))

    ears_options = [
        " _ _\n  ||_||",
        "(\\__/)",
        "|\\_/|",
        " °°",
        " ᴥᴥ",
        "/\\__/\\" 
    ]
    head_options = [
        "( -.-)",
        "( •.•)",
        "( > <)",
        "( ^.^)",
        "( o.o)"
    ]
    body_options = [
        "( _ _)~  ",
        "O_(\")(\") ",
        "( ___)~ ",
        "<    >",
        "( ~ ~)  " 
    ]

    def __init__(self, nickname = "", genom = [0, 0, 0, 0], parents = [], rabbit_id = None):
        self.rabbit_helper = RabbitHelper()
        self.id = rabbit_id
        self.genom = genom
        self.max_age = genom[0]
        self.gender = random.choice(["male", "female"])
        self.parents = parents or []
        self.name = self.rabbit_helper.generate_name(genom)
        self.nickname = nickname
        self.fertility = self.rabbit_helper.get_fertility_by_id(genom[2] % 5)
        self.hp = random.randint(*self.rabbit_helper.get_health_state(genom[1] % 3)["hp_range"])
        self.is_sick = False
        self.longevity = self.rabbit_helper.get_longevity_by_id(genom[0] % 3)
        self.max_age = self.longevity["max_age"]
        self.current_age = 0


        self._id = None
        self.rabbit_id = rabbit_id
        self._load_or_create()

    def _load_or_create(self):
        existing = self.db.get_rabbit(self.rabbit_id)
        if existing:
            self._load_from_db(existing)
        else:
            self._create_new()
            self._load_or_create()

    def _load_from_db(self, data: Dict):
        self._id = data["_id"]
        self.nickname = data["name"]
        self.rabbit_id = data["rabbit_id"]
        self.genom = data["genom"]
        self.parents = [p for p in data.get("parents", [])]
        self.fertility = self.rabbit_helper.get_fertility_by_id(self.genom[2] % 5)
        self.longevity = self.rabbit_helper.get_longevity_by_id(self.genom[0] % 3)
        self.hp = data["hp"]
        self.gender = data["gender"]
        self.generation = data["generation"]

    def _create_new(self):
        self._id = self.db.create_rabbit(self.nickname, self.genom, self.parents)
        self.rabbit_id = self._id["rabbit_id"]

    @classmethod
    def from_db(cls, rabbit_id: int) -> 'Rabbit':
        data = cls.db.get_rabbit(rabbit_id)
        if not data:
            raise ValueError(f"Кролик с ID {rabbit_id} не найден")
        
        rabbit = cls(rabbit_id=rabbit_id)
        rabbit._load_from_db(data)
        return rabbit

    def _calculate_generation(self) -> int:
        if not self.parents:
            return 1
        return max(Rabbit(rabbit_id=p).generation for p in self.parents) + 1

    def _calculate_genom_hash(self) -> int:
        return hash(tuple(self.genom)) % (10 ** 8)

    def _generate_traits(self) -> Dict:
        return {
            "speed": self.genom[0] % 10,
            "fertility": self.rabbit_helper.get_fertility_by_id(self.genom[2] % 5),
            "intelligence": self.genom[2] % 10,
            "appearance": self.genom[3] % 10,
            "signature_color": f"#{self.genom[0]:02x}{self.genom[1]:02x}{self.genom[2]:02x}"
        }

    def _b(self, rab2: 'Rabbit', _k):
            new_genom = []
            for i in range(4):
                gene = random.choice([self.genom[i], rab2.genom[i]])
                
                if random.random() < 0.1:
                    gene += random.randint(-1, 1)
                    gene = max(0, min(gene, 9))
                
                new_genom.append(gene)
            if _k:
                new_genom[1] = 10
            return Rabbit(f"{self.nickname} Child", new_genom, [self.rabbit_id, rab2.rabbit_id] + self.parents + rab2.parents)
    
    @property
    def is_alive(self) -> bool:
        """Проверяет, жив ли кролик"""
        return self.hp > 0

    @property
    def traits(self) -> Dict:
        """Возвращает характеристики кролика"""
        data = self.db.get_rabbit(self.rabbit_id)
        return data.get("traits", {})

    def get_family_tree(self, depth: int = 3) -> Dict:
        """Возвращает семейное древо"""
        if depth <= 0:
            return {}
        
        tree = {
            "id": self.rabbit_id,
            "head": self.head_options[min(self.genom[2] % 5, len(self.head_options)-1)],
            "name": self.nickname,
            "generation": self.generation,
            "gender": self.gender,
            "is_alive": self.is_alive,
            "children": []
        }
        
        for i in range(0, 2):
            if self.parents != []:
                parent_tree = Rabbit(rabbit_id=self.parents[i]).get_family_tree(depth - 1)
            else:
                parent_tree = None
            if parent_tree:
                tree["children"].append(parent_tree)
        
        return tree
    
    def display(self):
        print(f"""
        -----------------------------------------------------------------
        Name: {self.name}             Alias: {self.nickname}
        Gender: {self.gender}         ID: {self.rabbit_id}
        Genom: {self.genom}
        Age: {self.current_age}/{self.max_age} ({self.longevity['description']})
        Health: {self.hp}
        Health Status: {self.rabbit_helper.get_health_description(self.genom[1], self.is_sick)}
        Fertility: {self.fertility["description"][self.gender]}
        -----------------------------------------------------------------""")

    def draw_rabbit_text(self):
        ear_index = min(self.genom[0] % 5, len(self.ears_options)-1)
        ears = self.ears_options[ear_index]
        head_index = min(self.genom[2] % 5, len(self.head_options)-1)
        head = self.head_options[head_index]
        body_index = min(self.genom[1] % 5, len(self.body_options)-1)
        body = self.body_options[body_index]

        color = "\033[38;2;{};{};{}m".format(70 + 255 // (self.genom[1] + 1),70 + 255 // (self.genom[2] + 1),70 + 255 // (self.genom[3] + 1))
        
        rabbit = f" {ears}\n  {head}\n  {body}"

        print(f"{color} {rabbit} \033[0m")
        return rabbit

    def breed(self, partner: 'Rabbit') -> List['Rabbit']:
        if self.gender == "male":
            raise ValueError("Рожать детей могут только кролики женского пола!")
        if self.gender == partner.gender:
            raise ValueError("Кролики одного пола не могут размножаться!")
        
        fertility_chance = (self.fertility["stats"]["value"] + partner.fertility["stats"]["value"]) / 2
        if random.random() > fertility_chance:
            return []

        childs = []

        _k = len(self.parents + partner.parents + [self.rabbit_id] + [partner.rabbit_id]) > len(set(self.parents + partner.parents + [self.rabbit_id] + [partner.rabbit_id]))
        for k in range(0, self.rabbit_helper.calculate_offspring(self.fertility, partner.fertility)):
            childs.append(self._b(partner, _k))
        return childs
    
    def age_up(self):
        self.current_age += 1
        self.hp = max(1, self.hp + self.longevity["hp_penalty"])
        self.db.update_rabbit(self._id, {
            'current_age': self.current_age,
            'hp': self.hp,
            'is_alive': self.hp > 0
        })
        health_status = self._get_health_status()
        self.db.record_health_history(self._id, self.hp, health_status)
    
    def get_relatives(self, relation_type: str = 'siblings') -> List[Dict]:
        """Получает родственников из базы"""
        query = {}
        if relation_type == 'siblings':
            if not self.parents:
                return []
            query = {'parents': {'$all': [p._id for p in self.parents]}}
        
        return list(self.db.rabbits.find(query))
    
    def get_all_rabbits(self):
        """Возвращает всех кроликов из базы"""
        return list(self.db.rabbits.find({}))
    
    def show_population_graph(self):
        """Показывает граф всей популяции"""
        all_rabbits = list(self.db.rabbits.find({}))
        visualizer = PopulationGraph()
        return visualizer.generate_population_graph(all_rabbits)
    
    def to_json(self) -> dict:
        """Преобразует данные кролика в JSON-совместимый словарь"""
        return {
            "id": str(self._id) if self._id else None,
            "rabbit_id": self.rabbit_id,
            "nickname": self.nickname,
            "name": self.name,
            "genom": self.genom,
            "parents": self.parents,
            "gender": self.gender,
            "generation": self._calculate_generation(),
            "current_age": self.current_age,
            "max_age": self.max_age,
            "hp": self.hp,
            "is_alive": self.is_alive,
            "is_sick": self.is_sick,
            "fertility": {
                "value": self.fertility["stats"]["value"],
                "description": self.fertility["description"][self.gender]
            },
            "longevity": {
                "max_age": self.longevity["max_age"],
                "description": self.longevity["description"]
            },
            "traits": self._generate_traits(),
            "visual_representation": {
                "ears": self.ears_options[min(self.genom[0] % 5, len(self.ears_options)-1)],
                "head": self.head_options[min(self.genom[2] % 5, len(self.head_options)-1)],
                "body": self.body_options[min(self.genom[1] % 5, len(self.body_options)-1)]
            }
        }


class FamilyTreeArtist:
    def __init__(self):
        self.rabbit_art = {
            'male': "♂️",
            'female': "♀️",
            'dead': "☠️"
        }
    
    def draw_tree(self, family_data: Dict) -> str:
        """Генерирует ASCII-древо из структуры данных"""
        tree_lines = []
        self._build_branch(family_data, "", tree_lines)
        return "\n".join(tree_lines)
    
    def _build_branch(self, rabbit: Dict, prefix: str, lines: List[str], is_last: bool = True):
        """Рекурсивно строит ветви древа"""
        # Текущий кролик
        art = self._get_rabbit_art(rabbit)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{art} {rabbit['name']} (ID:{rabbit['id']}) {rabbit["generation"]}")
        
        # Дети
        new_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(rabbit.get('children', [])):
            self._build_branch(
                child,
                new_prefix,
                lines,
                i == len(rabbit['children']) - 1
            )
    
    def _get_rabbit_art(self, rabbit: Dict) -> str:
        """Возвращает ASCII-арт в зависимости от свойств кролика"""
        if not rabbit.get('is_alive', True):
            return self.rabbit_art['dead']
        return self.rabbit_art[rabbit['gender']]

class EnhancedFamilyTreeArtist(FamilyTreeArtist):
    def __init__(self):
        super().__init__()
        self.colors = {
            'male': "\033[34m",    # Синий
            'female': "\033[35m",  # Фиолетовый
            'child': "\033[36m",   # Голубой
            'dead': "\033[90m",    # Серый
            'reset': "\033[0m"
        }
        
    def _get_rabbit_art(self, rabbit: Dict) -> str:
        art = super()._get_rabbit_art(rabbit)
        color_key = 'child' if len(rabbit.get('children', [])) == 0 else rabbit['gender']
        color = self.colors.get(color_key, self.colors['reset'])
        return f"{color}{art}{rabbit["head"]}{self.colors['reset']}"

    def draw_tree(self, family_data: Dict) -> str:
        """Добавляем заголовок и статистику"""
        tree = super().draw_tree(family_data)
        stats = self._get_family_stats(family_data)[0]
        return f"Семейное древо кроликов:\n{tree}\n\n{stats}"
    
    def _get_family_stats(self, rabbit: Dict) -> Union[str, Dict]:
        """Собираем статистику по семье"""
        stats = {
            'total': 1,
            'alive': 1 if rabbit.get('is_alive', False) else 0,
            'generations': rabbit.get('generation', 1)
        }
        
        for child in rabbit.get('children', []):
            child_stats = self._get_family_stats(child)
            child_stats = child_stats[1]
            stats['total'] += child_stats['total']
            stats['alive'] += child_stats['alive']
            stats['generations'] = max(stats['generations'], child_stats['generations'])
        
        return [(f"Всего кроликов: {stats['total']}\n"
                    f"Живых: {stats['alive']}\n"
                    f"Поколений: {stats['generations']}"), stats]