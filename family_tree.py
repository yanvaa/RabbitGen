from graphviz import Digraph
from PIL import Image, ImageDraw, ImageFont
import io
import random
from typing import Dict, List, Union
from datetime import datetime

class FamilyTreeArtist:
    def __init__(self):
        self.rabbit_art = {
            'male': "♂️",
            'female': "♀️",
            'dead': "☠️"
        }
    
    def draw_tree(self, family_data: Dict) -> str:
        tree_lines = []
        self._build_branch(family_data, "", tree_lines)
        return "\n".join(tree_lines)
    
    def _build_branch(self, rabbit: Dict, prefix: str, lines: List[str], is_last: bool = True):
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
        tree = super().draw_tree(family_data)
        stats = self._get_family_stats(family_data)[0]
        return f"Семейное древо кроликов:\n{tree}\n\n{stats}"
    
    def _get_family_stats(self, rabbit: Dict) -> Union[str, Dict]:
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

class GraphicFamilyTree:
    def __init__(self):
        self.colors = {
            "background": "#121212",
            "node_bg": "#1e1e1e",
            "border": "#3a3a3a",
            "male": "#64b5f6",  # синий
            "female": "#ff8a65",  # оранжевый
            "text": "#e0e0e0",
            "dead": "#424242"
        }
        self.font = "CousineNerdFontPropo-Regular.ttf"

    def generate(self, family_data, filename="dark_family_tree"):
        """Генерирует минималистичное тёмное древо"""
        dot = Digraph(
            format='png',
            graph_attr={
                "bgcolor": self.colors["background"],
                "rankdir": "TB",
                "nodesep": "0.4",
                "ranksep": "0.6",
                "margin": "0.2"
            },
            node_attr={
                "shape": "box",
                "style": "filled",
                "fontname": self.font,
                "fontsize": "11",
                "fontcolor": self.colors["text"],
                "penwidth": "1.5",
                "margin": "0.15"
            },
            edge_attr={
                "splines": "ortho",
                "constraint": "true",
                "color": self.colors["border"],
                "penwidth": "2",
                "weight": "100",
                "arrowhead": "none"
            }
        )

        self._add_nodes(dot, family_data)
        
        img_bytes = dot.pipe()
        img = Image.open(io.BytesIO(img_bytes))
        
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(self.font, 18)
        except:
            font = ImageFont.load_default()
            
        draw.text(
            (20, 5),
            "Rabbit Family Tree",
            fill=self.colors["text"],
            font=font
        )
        
        img.save(f"{filename}.png")
        return img

    def _add_nodes(self, dot, rabbit):
        status = "dead" if not rabbit.get("is_alive", True) else rabbit.get("gender", "child")
        
        color_map = {
            "male": self.colors["male"],
            "female": self.colors["female"],
            "dead": self.colors["dead"]
        }
        
        dot.node(
            str(rabbit["id"]),
            label=f"{rabbit['name']}\nID: {rabbit['id']} | Gen: {rabbit.get('generation', 1)}",
            shape="box",
            fillcolor=self.colors["node_bg"],
            color=color_map.get(status, self.colors["border"]),
            fontsize="10",
        )

        for child in rabbit.get("children", []):
            dot.edge(
                str(child["id"]),
                str(rabbit["id"]),
                **{
                    "weight": "100",
                    "splines": "ortho",
                    "minlen": "1"
                }
            )
            self._add_nodes(dot, child)

class PopulationGraph:
    def __init__(self):
        self.colors = {
            "male": "#64b5f6",
            "female": "#ff8a65",
            "dead": "#424242",
            "bg": "#121212",
            "text": "#ffffff"
        }

    def generate_population_graph(self, rabbits_data, filename="population"):
        dot = Digraph(
            format='png',
            engine='dot',
            graph_attr={
                "bgcolor": self.colors["bg"],
                "rankdir": "TB",
                "nodesep": "0.5",
                "ranksep": "0.8",
                "spacing": "1.5",
                "fontcolor": self.colors["text"],
                "fontname": "Arial"
            },
            node_attr={
                "style": "filled",
                "fontcolor": self.colors["text"],
                "fontsize": "10",
                "shape": "box",
                "penwidth": "1.5",
                "width": "0.6",
                "height": "0.4",
            },
            edge_attr={
                "color": "#555555",
                "penwidth": "2",
                "arrowhead": "vee"
            }
        )

        for rabbit in rabbits_data:
            self._add_rabbit_node(dot, rabbit)

        for rabbit in rabbits_data:
            for parent_id in rabbit.get("parents", []):
                dot.edge(str(parent_id), str(rabbit["rabbit_id"]))

        dot.render(filename, cleanup=True)
        self._add_title(f"{filename}.png")
        
        return f"{filename}.png"

    def generate_population_bytes(self, rabbits_data) -> bytes:
        dot = self._create_population_graph(rabbits_data)
        return dot.pipe(format='png')
    
    def _create_population_graph(self, rabbits_data):
        dot = Digraph(
            format='png',
            engine='dot',
            graph_attr={
                "bgcolor": self.colors["bg"],
                "rankdir": "TB",
                "nodesep": "0.5",
                "ranksep": "0.8",
                "spacing": "1.5",
                "fontcolor": self.colors["text"],
                "fontname": "Arial"
            },
            node_attr={
                "style": "filled",
                "fontcolor": self.colors["text"],
                "fontsize": "10",
                "shape": "box",
                "penwidth": "1.5",
                "width": "0.6",
                "height": "0.4",
            },
            edge_attr={
                "color": "#555555",
                "penwidth": "2",
                "arrowhead": "vee"
            }
        )

        for rabbit in rabbits_data:
            self._add_rabbit_node(dot, rabbit)

        for rabbit in rabbits_data:
            for parent_id in rabbit.get("parents", []):
                dot.edge(str(parent_id), str(rabbit["rabbit_id"]))
                
        return dot

    def _add_rabbit_node(self, dot, rabbit):
        status = "dead" if not rabbit.get("is_alive", True) else rabbit["gender"]
        color = self.colors[status]
        
        dot.node(
            str(rabbit["rabbit_id"]),
            label=f"{rabbit['name']}\nID: {rabbit['rabbit_id']} | Gen: {rabbit.get('generation', 1)}",
            fillcolor=color,
            color="#777777"
        )

    def _add_title(self, image_path):
        img = Image.open(image_path)
        width, height = img.size
        new_img = Image.new("RGB", (width, height + 500), self.colors["bg"])
        new_img.paste(img, (0, 40))
        
        draw = ImageDraw.Draw(new_img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
            
        draw.text(
            (20, 10),
            "Rabbit Population Graph",
            fill=self.colors["text"],
            font=font
        )
        
        new_img.save(image_path)