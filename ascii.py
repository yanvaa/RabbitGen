
from PIL import Image, ImageDraw, ImageFont
import re
from typing import Optional, Tuple
import io

class AsciiToImageConverter:
    def __init__(self):
        self.font = ImageFont.truetype("CousineNerdFontPropo-Regular.ttf", size=50)
        self.char_width = 30
        self.char_height = 100
        
    def _calculate_colors(self, genom):
        text_color = (
            70 + 255 // (genom[1] + 1),
            70 + 255 // (genom[2] + 1),
            70 + 255 // (genom[3] + 1)
        )
        
        brightness = sum(text_color) / 3
        bg_color = "#1a1b26" if brightness > 127 else "#c0caf5"
        
        return text_color, bg_color
    
    def _convert(self, art, colors = ["#1a1b26", "#c0caf5"]):
        lines = art.split('\n')
        width = max(len(line) for line in lines) * self.char_width
        height = len(lines) * self.char_height
        
        img = Image.new('RGB', (width, height), colors[1])
        draw = ImageDraw.Draw(img)
        
        y = 30
        for line in lines:
            draw.text((0, y), line, fill=colors[0], font=self.font)
            y += self.char_height
            
        return img


    def convert(self, art, output_file=None):
        if not output_file:
            return self._convert(art)
        else:
            self._convert(art).save()
            return output_file

    def convert_rabbit(self, rabbit, output_file=None):
        ascii_art = " " + rabbit.draw_rabbit_text().replace("\t", "")
        text_color, bg_color = self._calculate_colors(rabbit.genom)
        if not output_file:
            return self._convert(ascii_art, (text_color, bg_color))
        else:
            self._convert(ascii_art, (text_color, bg_color)).save()
            return output_file
