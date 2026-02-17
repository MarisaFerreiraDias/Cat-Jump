#!/usr/bin/env python3
import re

# Read the current file
with open('CatJump.py', 'r') as f:
    content = f.read()

# Add json import
content = content.replace(
    'import random  # Random number generation for platform placement',
    'import random  # Random number generation for platform placement\nimport json  # JSON file operations for saving high score'
)

# Add high score functions after SCORE_PER_DIFFICULTY
high_score_functions = '''
# High Score Management Functions
def load_high_score():
    """Load the high score from file. Returns 0 if file doesn't exist."""
    script_dir = os.path.dirname(__file__)
    high_score_file = os.path.join(script_dir, "high_score.json")
    
    try:
        if os.path.exists(high_score_file):
            with open(high_score_file, 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0)
    except (json.JSONDecodeError, IOError):
        pass
    return 0

def save_high_score(score):
    """Save the high score to file."""
    script_dir = os.path.dirname(__file__)
    high_score_file = os.path.join(script_dir, "high_score.json")
    
    try:
        with open(high_score_file, 'w') as f:
            json.dump({'high_score': score}, f)
    except IOError:
        pass  # Silently fail if can't write file
'''

content = content.replace(
    'SCORE_PER_DIFFICULTY = 500  # Every 500 points increases difficulty by 1\n\n# Player class',
    'SCORE_PER_DIFFICULTY = 500  # Every 500 points increases difficulty by 1' + high_score_functions + '\n# Player class'
)

# Update main() to load and display high score
content = content.replace(
    '    while True:  # Outer loop allows game restart\n        # Initialize game clock for 60 FPS\n        clock = pygame.time.Clock()\n        # Create player sprite in center of screen\n        player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)',
    '    while True:  # Outer loop allows game restart\n        # Initialize game clock for 60 FPS\n        clock = pygame.time.Clock()\n        # Load high score from file\n        high_score = load_high_score()\n        # Create player sprite in center of screen\n        player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)'
)

# Update HUD display
content = content.replace(
    '            # Draw the player with camera offset\n            player.draw(screen, camera_y)\n            # Draw current score (HUD) centered at top\n            score_surface = score_font.render(f"Score: {score}  |  Level: {current_difficulty + 1}", True, BLACK)',
    '            # Draw the player with camera offset\n            player.draw(screen, camera_y)\n            # Draw current score and high score (HUD) centered at top\n            score_surface = score_font.render(f"Score: {score}  |  High Score: {high_score}  |  Level: {current_difficulty + 1}", True, BLACK)'
)

# Update game over section to save high score
content = content.replace(
    '            # Check if player has been falling without finding a platform\n            if game_over:\n                retry = show_game_over_screen(screen, score)',
    '            # Check if player has been falling without finding a platform\n            if game_over:\n                # Update high score if current score is higher\n                if score > high_score:\n                    high_score = score\n                    save_high_score(high_score)\n                retry = show_game_over_screen(screen, score)'
)

# Write the modified content
with open('Test.py', 'w') as f:
    f.write(content)

print('File updated successfully with high score system!')

