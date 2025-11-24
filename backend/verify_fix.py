import sys
import os
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from scores.utils import _generate_svg_bar_chart

def verify():
    scores = [80, 90]
    avg_scores = [50, 60]
    
    svg = _generate_svg_bar_chart(scores, avg_scores, '#000000', 'test_chart')
    
    print("Generated SVG:")
    print(svg)
    
    # Check if star positions are different
    # We look for y coordinates of the stars (text with ★)
    # <text x="..." y="{avg_y + 4}" ...>★</text>
    
    lines = svg.split('\n')
    star_y_coords = []
    for line in lines:
        if '★' in line and '<text' in line:
            # Extract y attribute
            parts = line.split('y="')
            if len(parts) > 1:
                y_val = parts[1].split('"')[0]
                star_y_coords.append(float(y_val))
    
    print(f"Star Y coordinates: {star_y_coords}")
    
    if len(star_y_coords) >= 2:
        if star_y_coords[0] != star_y_coords[1]:
            print("SUCCESS: Star positions are different.")
        else:
            print("FAILURE: Star positions are identical.")
    else:
        print("FAILURE: Could not find enough stars.")

if __name__ == '__main__':
    verify()
