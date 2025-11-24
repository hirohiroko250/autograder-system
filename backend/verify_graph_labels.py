import sys
import os
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from scores.utils import _generate_svg_bar_chart

def verify():
    scores = [150, 180]
    avg_scores = [120, 130]
    max_score = 200
    
    svg = _generate_svg_bar_chart(scores, avg_scores, '#000000', 'test_chart', max_score=max_score)
    
    print("Generated SVG:")
    print(svg)
    
    # Check for axis labels
    # Should contain "200" and "100" (half of 200)
    
    if '>200</text>' in svg:
        print("SUCCESS: Found max score label '200'.")
    else:
        print("FAILURE: Did not find max score label '200'.")
        
    if '>100</text>' in svg:
        print("SUCCESS: Found half score label '100'.")
    else:
        print("FAILURE: Did not find half score label '100'.")

    # Check for a case with 100 max score
    svg_100 = _generate_svg_bar_chart(scores, avg_scores, '#000000', 'test_chart_100', max_score=100)
    if '>100</text>' in svg_100 and '>50</text>' in svg_100:
         print("SUCCESS: Found labels '100' and '50' for max_score=100.")
    else:
         print("FAILURE: Labels incorrect for max_score=100.")

if __name__ == '__main__':
    verify()
