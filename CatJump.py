# Pygame 2D platformer game - Jump and climb on randomly generated platforms

import pygame  # Game engine and graphics
import sys  # System-level functions for exiting
import os  # File path operations
import random  # Random number generation for platform placement
import json  # JSON file operations for saving high score

# Initialize Pygame
pygame.init()

# Game Settings Class
class GameSettings:
    """Centralized game configuration and constants"""
    # Screen dimensions
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 768
    
    # Colors (RGB tuples)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    BROWN = (139, 69, 19)
    
    # Upgrade colors
    UPGRADE_COLORS = {
        'Jump Boost': (0, 255, 0),           # Green
        'Speed Boost': (255, 165, 0),        # Orange
        'Invincibility': (128, 0, 128),      # Purple
        'Gravity Reduction': (0, 255, 255),  # Cyan
        'Shield': (0, 0, 255)                # Blue
    }
    
    # Player settings
    PLAYER_WIDTH = 90
    PLAYER_HEIGHT = 90
    PLAYER_SPEED = 7
    GRAVITY = 0.4
    PLAYER_JUMP = -19
    
    # Difficulty scaling
    SCORE_PER_DIFFICULTY = 500

# Create game screen
screen = pygame.display.set_mode((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
pygame.display.set_caption("Cat Jump")

# Functions to load and save high score using a JSON file in the same directory as the script
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

# Save high score to file
def save_high_score(score):
    """Save the high score to file."""
    script_dir = os.path.dirname(__file__)
    high_score_file = os.path.join(script_dir, "high_score.json")
    
    try:
        with open(high_score_file, 'w') as f:
            json.dump({'high_score': score}, f)
    except IOError:
        pass  # Silently fail if can't write file

# Player class - Represents the player character that the user controls
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        """Initialize the player sprite at position (x, y)"""
        super().__init__()
        # Load the player images from files
        script_dir = os.path.dirname(__file__)
        self.idle_image = pygame.image.load(os.path.join(script_dir, "CarPhotos", "Car.png")).convert_alpha()
        self.jump_image = pygame.image.load(os.path.join(script_dir, "CarPhotos", "Car-jump.png")).convert_alpha()
        self.fall_image = pygame.image.load(os.path.join(script_dir, "CarPhotos", "Car-fall.png")).convert_alpha()
        self.jump_balloon_image = pygame.image.load(os.path.join(script_dir, "CarPhotos", "Car-jump-balloon.png")).convert_alpha()
        self.fall_balloon_image = pygame.image.load(os.path.join(script_dir, "CarPhotos", "Car-fall-balloon.png")).convert_alpha()
        
        # Scale all images to player dimensions
        self.idle_image = pygame.transform.scale(self.idle_image, (GameSettings.PLAYER_WIDTH, GameSettings.PLAYER_HEIGHT))
        self.jump_image = pygame.transform.scale(self.jump_image, (GameSettings.PLAYER_WIDTH, GameSettings.PLAYER_HEIGHT))
        self.fall_image = pygame.transform.scale(self.fall_image, (GameSettings.PLAYER_WIDTH, GameSettings.PLAYER_HEIGHT))
        self.jump_balloon_image = pygame.transform.scale(self.jump_balloon_image, (GameSettings.PLAYER_WIDTH, GameSettings.PLAYER_HEIGHT))
        self.fall_balloon_image = pygame.transform.scale(self.fall_balloon_image, (GameSettings.PLAYER_WIDTH, GameSettings.PLAYER_HEIGHT))
        
        # Set current image
        self.image = self.idle_image
        self.rect = self.image.get_rect()
        self.rect.x = x  # Set initial X position
        self.rect.y = y  # Set initial Y position
        self.vel_x = 0  # Horizontal velocity
        self.vel_y = 0  # Vertical velocity
        self.on_ground = True  # Track if player is touching a platform
        self.fall_time = 0  # Track how long player has been falling without landing
        # Upgrade tracking
        self.active_upgrades = {}  # Dictionary of active upgrades: {name: remaining_frames}
        self.shield_active = False  # One-time shield protection
    
    def handle_input(self, keys):
        """Handle horizontal movement based on keyboard input"""
        self.vel_x = 0  # Reset horizontal velocity each frame
        
        # Move left with arrow keys or 'A'
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -GameSettings.PLAYER_SPEED
        # Move right with arrow keys or 'D'
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = GameSettings.PLAYER_SPEED

    def jump(self, jump_mult=1.0):
        """Execute a jump with optional difficulty modifier. Resets fall timer."""
        self.vel_y = GameSettings.PLAYER_JUMP * jump_mult
        self.fall_time = 0  # Reset fall timer on jump

    def update(self, platforms, gravity_mult=1.0, jump_mult=1.0):
        """Update player position, apply physics, and check collisions"""
        # Apply gravity modifiers from upgrades
        if 'Gravity Reduction' in self.active_upgrades:
            gravity_mult *= 0.5  # Half gravity when upgrade active
        
        # Apply jump modifiers from upgrades
        if 'Jump Boost' in self.active_upgrades:
            jump_mult *= 1.3  # 30% stronger jumps
        
        # Apply speed modifiers from upgrades
        if 'Speed Boost' in self.active_upgrades:
            if self.vel_x > 0:
                self.vel_x = int(GameSettings.PLAYER_SPEED * 1.5)
            elif self.vel_x < 0:
                self.vel_x = int(-GameSettings.PLAYER_SPEED * 1.5)
        
        # Decrease all upgrade timers
        expired = []
        for upgrade_name in self.active_upgrades:
            self.active_upgrades[upgrade_name] -= 1
            if self.active_upgrades[upgrade_name] <= 0:
                expired.append(upgrade_name)
        for upgrade_name in expired:
            del self.active_upgrades[upgrade_name]
        
        # Apply gravity to vertical velocity with difficulty modifier
        self.vel_y += GameSettings.GRAVITY * gravity_mult
        # Update position based on velocity
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Assume player is not on ground (will be set to True if collision detected)
        self.on_ground = False

        # Check for platform collisions (only when falling down)
        if self.vel_y > 0:
            # Find all platforms the player collides with
            hits = pygame.sprite.spritecollide(self, platforms, False)
            for platform in hits:
                # Only land on platform if approaching from above
                if self.rect.bottom <= platform.rect.bottom:
                    # Check if platform is deadly - only kill if player lands on it
                    if platform.deadly:
                        # Check if player has shield upgrade or invincibility
                        if self.shield_active:
                            self.shield_active = False  # Use up the shield
                            # Position player on top of platform anyway
                            self.rect.bottom = platform.rect.top
                            self.jump(jump_mult)
                            self.on_ground = True
                            break  # Stop processing other platforms
                        elif 'Invincibility' in self.active_upgrades:
                            # Position player on top of platform anyway
                            self.rect.bottom = platform.rect.top
                            self.jump(jump_mult)
                            self.on_ground = True
                            break  # Stop processing other platforms
                        else:
                            return True  # Deadly platform - game over
                    else:
                        # Position player on top of platform
                        self.rect.bottom = platform.rect.top
                        # Apply upward jump velocity with difficulty modifier
                        self.jump(jump_mult)
                        self.on_ground = True
                        # Mark breakable platforms for removal (don't remove directly)
                        platform.will_break = platform.breakable
                        break  # Stop processing other platforms after landing

        # Keep player within horizontal screen bounds (can fall off top/bottom)
        if self.rect.left < 0:
            self.rect.left = 0  # Prevent going left of screen
        if self.rect.right > GameSettings.SCREEN_WIDTH:
            self.rect.right = GameSettings.SCREEN_WIDTH  # Prevent going right of screen
        
        # Track falling time - increment if not on ground
        if not self.on_ground:
            self.fall_time += 1
        
        # Check if either Gravity Reduction or Jump Boost is active
        has_balloon_upgrades = 'Gravity Reduction' in self.active_upgrades or 'Jump Boost' in self.active_upgrades
        
        # Update sprite based on player state
        if self.on_ground:
            self.image = self.idle_image
        elif self.vel_y < 0:  # Moving upward (jumping)
            self.image = self.jump_balloon_image if has_balloon_upgrades else self.jump_image
        else:  # Moving downward (falling)
            self.image = self.fall_balloon_image if has_balloon_upgrades else self.fall_image
        
        # Return True if player has been falling too long without finding a platform
        if self.fall_time > 210:  # ~3.5 seconds at 60 FPS
            return True
        # Also die immediately if player falls below screen by a large margin
        if self.rect.top > GameSettings.SCREEN_HEIGHT + 200:
            return True
        return False
    
    def draw(self, surface, camera_y):
        """Draw the player sprite with camera offset"""
        # Adjust Y position based on camera position for scrolling effect
        surface.blit(self.image, (self.rect.x, self.rect.y - camera_y))

# Platform class - Represents static platforms the player can jump on
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width=220, height=200, breakable=False, deadly=False):
        """Create a platform rectangle at position (x, y) with given dimensions"""
        super().__init__()
        self.breakable = breakable  # Flag for breakable platforms
        self.deadly = deadly  # Flag for deadly platforms
        
        # Load the appropriate platform image
        script_dir = os.path.dirname(__file__)
        if breakable:
            image_path = os.path.join(script_dir, "broken-floor.png")
        else:
            image_path = os.path.join(script_dir, "floor.png")
        
        # Load and scale the platform image
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))
        
        # Tint deadly platforms red
        if deadly:
            red_surface = pygame.Surface(self.image.get_size())
            red_surface.fill((255, 0, 0))
            self.image.blit(red_surface, (0, 0), special_flags=pygame.BLEND_MULT)
        
        # Create a collision rect at the top of the platform for landing detection
        # This represents the solid surface of the platform where the player can land
        self.rect = pygame.Rect(x, y, width, 15)  # Thin rect at the visual top of platform
        self.x = x  # Store position separately
        self.y = y
        self.will_break = False  # Flag to mark for breaking on next frame

# Orb class - Collectible that provides random upgrades to the player
class Orb(pygame.sprite.Sprite):
    UPGRADES = [
        {'name': 'Jump Boost', 'duration': 900},  # ~15 seconds at 60 FPS
        {'name': 'Speed Boost', 'duration': 900},
        {'name': 'Invincibility', 'duration': 900},
        {'name': 'Gravity Reduction', 'duration': 900},
        {'name': 'Shield', 'duration': 0}  # One-time use
    ]
    
    def __init__(self, x, y):
        """Create an orb at position (x, y) with a random upgrade"""
        super().__init__()
        # Select a random upgrade
        self.upgrade = random.choice(self.UPGRADES).copy()
        # Get the color corresponding to this upgrade
        color = GameSettings.UPGRADE_COLORS.get(self.upgrade['name'], (255, 255, 255))
        
        # Create a simple colored circle for the orb
        self.size = 20
        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (self.size, self.size), self.size)
        pygame.draw.circle(self.image, (255, 255, 255), (self.size, self.size), self.size, 2)
        
        self.rect = self.image.get_rect()
        self.rect.x = x + 100  # Center on platform
        self.rect.y = y - 50  # Float above platform
    
    def draw(self, surface, camera_y):
        """Draw the orb with camera offset"""
        surface.blit(self.image, (self.rect.x, self.rect.y - camera_y))

# Game Over Screen Function
def show_game_over_screen(screen, score=0):
    """Display game over screen with retry/quit options. Returns True if player chooses to retry.
    Displays final `score` on the game over screen."""
    # Create fonts for displaying text
    font_large = pygame.font.Font(None, 80)  # Large font for "GAME OVER"
    font_medium = pygame.font.Font(None, 50)  # Medium font for instructions
    
    # Loop until player chooses to retry or quit
    while True:
        # Handle user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Window close button
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # R key for retry
                    return True
                # ESC or Q keys to quit
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return False
        
        # Draw semi-transparent dark overlay to darken the background
        overlay = pygame.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        overlay.set_alpha(200)  # 200 out of 255 opacity
        overlay.fill(GameSettings.BLACK)
        screen.blit(overlay, (0, 0))
        
        # Render and display "GAME OVER" text
        game_over_text = font_large.render("GAME OVER", True, GameSettings.RED)
        game_over_rect = game_over_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 - 100))
        screen.blit(game_over_text, game_over_rect)
        
        # Render and display retry instruction
        retry_text = font_medium.render("Press R to Retry", True, GameSettings.WHITE)
        retry_rect = retry_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2))
        screen.blit(retry_text, retry_rect)
        
        # Render and display quit instruction
        quit_text = font_medium.render("Press ESC or Q to Quit", True, GameSettings.WHITE)
        quit_rect = quit_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 + 100))
        screen.blit(quit_text, quit_rect)

        # Render and display final score
        score_text = font_medium.render(f"Score: {score}", True, GameSettings.BLACK)
        score_rect = score_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 + 180))
        screen.blit(score_text, score_rect)
        
        # Update display to show the screen
        pygame.display.flip()

# Start/Menu Screen Function
def show_start_screen(screen):
    """Simple start/menu screen. Returns True to start game, False to quit."""
    font_large = pygame.font.Font(None, 100)
    font_small = pygame.font.Font(None, 48)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return True
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return False

        overlay = pygame.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        overlay.fill(GameSettings.BLACK)
        screen.blit(overlay, (0, 0))
        
        # Display upgrade color legend in top left (smaller)
        font_legend_title = pygame.font.Font(None, 28)
        font_legend_text = pygame.font.Font(None, 24)
        legend_y = 20
        legend_title = font_legend_title.render("Upgrades:", True, GameSettings.WHITE)
        screen.blit(legend_title, (20, legend_y))
        
        legend_y += 30
        for upgrade_name, color in GameSettings.UPGRADE_COLORS.items():
            upgrade_text = font_legend_text.render(upgrade_name, True, color)
            screen.blit(upgrade_text, (20, legend_y))
            legend_y += 22

        title = font_large.render("2D Game", True, GameSettings.WHITE)
        title_rect = title.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 - 120))
        screen.blit(title, title_rect)

        instr = font_small.render("Press ENTER or SPACE to Start", True, GameSettings.WHITE)
        instr_rect = instr.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2))
        screen.blit(instr, instr_rect)

        quit_instr = font_small.render("Press ESC or Q to Quit", True, GameSettings.WHITE)
        quit_rect = quit_instr.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 + 70))
        screen.blit(quit_instr, quit_rect)

        pygame.display.flip()

# Pause Menu Function
def show_pause_menu(screen):
    """Pause menu. Returns one of: 'resume', 'restart', 'quit'"""
    font_large = pygame.font.Font(None, 80)
    font_med = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 36)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'resume'
                if event.key == pygame.K_r:
                    return 'restart'
                if event.key == pygame.K_q:
                    return 'quit'

        overlay = pygame.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(GameSettings.BLACK)
        screen.blit(overlay, (0, 0))

        title = font_large.render("PAUSED", True, GameSettings.WHITE)
        title_rect = title.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 - 120))
        screen.blit(title, title_rect)

        # Display upgrade color legend in top left (smaller)
        font_legend_title = pygame.font.Font(None, 28)
        font_legend_text = pygame.font.Font(None, 24)
        legend_y = 20
        legend_title = font_legend_title.render("Upgrades:", True, GameSettings.WHITE)
        screen.blit(legend_title, (20, legend_y))
        
        legend_y += 30
        for upgrade_name, color in GameSettings.UPGRADE_COLORS.items():
            upgrade_text = font_legend_text.render(upgrade_name, True, color)
            screen.blit(upgrade_text, (20, legend_y))
            legend_y += 22

        resume = font_med.render("Press ESC to Resume", True, GameSettings.WHITE)
        resume_rect = resume.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 + 100))
        screen.blit(resume, resume_rect)

        restart = font_med.render("Press R to Restart", True, GameSettings.WHITE)
        restart_rect = restart.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 + 150))
        screen.blit(restart, restart_rect)

        quit_text = font_med.render("Press Q to Quit", True, GameSettings.WHITE)
        quit_rect = quit_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2 + 200))
        screen.blit(quit_text, quit_rect)

        pygame.display.flip()

# Difficulty Scaling Function
def get_difficulty_modifiers(score):
    """Calculate difficulty modifiers based on score. Returns (gravity_mult, jump_mult, gap_mult, difficulty_level)"""
    difficulty_level = score // GameSettings.SCORE_PER_DIFFICULTY
    # Each level increases gravity by 5%, reduces jump height by 2% (capped at 0.85), increases gap by 3%
    gravity_mult = 1.0 + (difficulty_level * 0.05)
    jump_mult = max(0.85, 1.0 - (difficulty_level * 0.02))  # Cap at 0.85 to keep jumps reasonable
    gap_mult = 1.0 + (difficulty_level * 0.03)  # More modest gap increase
    return gravity_mult, jump_mult, gap_mult, difficulty_level

# Main Game Function
def main():
    """Main game loop - handles initialization and game state"""
    # Show start menu first
    start = show_start_screen(screen)
    if not start:
        pygame.quit()
        sys.exit()

    while True:  # Outer loop allows game restart
        # Initialize game clock for 60 FPS
        clock = pygame.time.Clock()
        # Load high score from file
        high_score = load_high_score()
        # Create player sprite in center of screen
        player = Player(GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2)
        # Score tracking: initial Y and highest (lowest numeric) Y reached
        initial_player_y = player.rect.y
        highest_player_y = player.rect.y
        score = 0
        score_font = pygame.font.Font(None, 40)
        # Load background image
        script_dir = os.path.dirname(__file__)
        background_path = os.path.join(script_dir, "Room.png")
        background = pygame.image.load(background_path).convert_alpha()
        background = pygame.transform.scale(background, (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        
        # Create groups to hold all sprites
        platforms = pygame.sprite.Group()
        orbs = pygame.sprite.Group()
        
        # Create the ground platform at bottom of screen
        ground = Platform(0, GameSettings.SCREEN_HEIGHT - 100, GameSettings.SCREEN_WIDTH, 300)
        platforms.add(ground)

        # Generate initial random platforms that form a reachable path upward
        num_platforms = 13  # Initial number of platforms to generate
        platform_height = GameSettings.SCREEN_HEIGHT - 200  # Starting height for first platform
        min_gap = 60  # Minimum vertical distance between platforms (pixels)
        max_gap = 100  # Maximum vertical distance between platforms (pixels)
        min_horizontal_gap = 200  # Minimum horizontal distance between platforms
        
        last_x = GameSettings.SCREEN_WIDTH // 2  # Track last platform X position for spacing
        highest_platform_y = platform_height  # Track highest platform for new platform generation
        
        # Track difficulty level for display
        current_difficulty = 0
        
        # Generate the initial set of platforms
        for _ in range(num_platforms):
            # Generate random X position with minimum horizontal spacing
            x = random.randint(0, GameSettings.SCREEN_WIDTH - 120)
            # Keep regenerating if too close to previous platform
            while abs(x - last_x) < min_horizontal_gap:
                x = random.randint(0, GameSettings.SCREEN_WIDTH - 120)
            last_x = x
            
            # Move platform up by random amount
            platform_height -= random.randint(min_gap, max_gap)
            # Cap minimum platform height to prevent spawning too high
            if platform_height < 100:
                platform_height = 100
            highest_platform_y = platform_height
            # Randomly make 30% of platforms breakable
            is_breakable = random.random() < 0.3
            # Deadly platforms start appearing at level 3 with 8% spawn rate
            is_deadly = False
            # Add platform to the game
            platform = Platform(x, platform_height, breakable=is_breakable, deadly=is_deadly)
            platforms.add(platform)
            # Randomly spawn orb on this platform (10% chance) - but not on deadly platforms
            if random.random() < 0.1 and not is_deadly:
                orbs.add(Orb(x, platform_height))

        # Main game loop for one game session
        running = True
        while running:
            clock.tick(60)  # Cap framerate at 60 FPS
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Window close button
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:  # ESC to pause
                            action = show_pause_menu(screen)
                            if action == 'quit':
                                pygame.quit()
                                sys.exit()
                            if action == 'restart':
                                running = False
                                break
            
            # Process player input for this frame
            keys = pygame.key.get_pressed()
            player.handle_input(keys)
            
            # Calculate camera position to keep player centered vertically
            camera_y = player.rect.centery - GameSettings.SCREEN_HEIGHT // 2
            
            # Get difficulty modifiers based on current score
            gravity_mult, jump_mult, gap_mult, current_difficulty = get_difficulty_modifiers(score)
            
            # Update player position and check collisions with difficulty applied
            game_over = player.update(platforms, gravity_mult, jump_mult)

            # Update highest Y reached (smaller Y means higher on screen)
            if player.rect.y < highest_player_y:
                highest_player_y = player.rect.y
                # Score increments per 10 pixels climbed
                score = int((initial_player_y - highest_player_y) / 10)
            
            # Check if player has been falling without finding a platform
            if game_over:
                # Update high score if current score is higher
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
                retry = show_game_over_screen(screen, score)
                if retry:
                    running = False  # Exit to restart the game
                else:
                    pygame.quit()
                    sys.exit()
            
            # Dynamically generate new platforms as player climbs
            if player.rect.top < highest_platform_y + GameSettings.SCREEN_HEIGHT:
                # Generate 5 new platforms with adjusted gaps based on difficulty
                for _ in range(5):
                    # Random X position with horizontal spacing
                    x = random.randint(0, GameSettings.SCREEN_WIDTH - 120)
                    while abs(x - last_x) < min_horizontal_gap:
                        x = random.randint(0, GameSettings.SCREEN_WIDTH - 120)
                    last_x = x
                    
                    # Position new platform above the current highest with difficulty scaling
                    adjusted_gap = int(min_gap + (random.randint(0, int(max_gap - min_gap)) * gap_mult))
                    highest_platform_y -= adjusted_gap
                    # Randomly make 30% of platforms breakable
                    is_breakable = random.random() < 0.3
                    # Deadly platforms start appearing at level 3 with 8% spawn rate
                    is_deadly = current_difficulty >= 3 and random.random() < 0.08
                    platform = Platform(x, highest_platform_y, breakable=is_breakable, deadly=is_deadly)
                    platforms.add(platform)
                    # Randomly spawn orb on this platform (10% chance) - but not on deadly platforms
                    if random.random() < 0.1 and not is_deadly:
                        orbs.add(Orb(x, highest_platform_y))
            
            # Remove platforms and orbs that are far below the screen (performance optimization)
            # Collect items to remove first to avoid modifying list during iteration
            platforms_to_remove = []
            for platform in platforms:
                if platform.rect.top > camera_y + GameSettings.SCREEN_HEIGHT + 100:
                    platforms_to_remove.append(platform)
                elif platform.will_break:  # Remove platforms marked to break
                    platforms_to_remove.append(platform)
                    platform.will_break = False  # Reset flag
            for platform in platforms_to_remove:
                platforms.remove(platform)
            
            orbs_to_remove = []
            for orb in orbs:
                if orb.rect.top > camera_y + GameSettings.SCREEN_HEIGHT + 100:
                    orbs_to_remove.append(orb)
            for orb in orbs_to_remove:
                orbs.remove(orb)
            
            # Check for orb collection
            collected_orbs = pygame.sprite.spritecollide(player, orbs, False)
            for orb in collected_orbs:
                # Apply the upgrade
                if orb.upgrade['name'] == 'Shield':
                    player.shield_active = True
                else:
                    player.active_upgrades[orb.upgrade['name']] = orb.upgrade['duration']
                # Remove the orb
                orbs.remove(orb)

            # Render the current frame
            # Draw background image
            screen.blit(background, (0, 0))
            # Apply a 10% black tint over the background for a subtle darkening
            tint = pygame.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
            tint.set_alpha(int(255 * 0.25))
            tint.fill(GameSettings.BLACK)
            screen.blit(tint, (0, 0))
            
            # Draw all platforms with camera offset
            for platform in platforms:
                screen.blit(platform.image, (platform.x, platform.y - camera_y))
            
            # Draw all orbs with camera offset
            for orb in orbs:
                orb.draw(screen, camera_y)
            
            # Draw the player with camera offset
            player.draw(screen, camera_y)
            
            # Draw shield bubble if shield is active
            if player.shield_active:
                # Calculate shield bubble position (centered on player)
                shield_center_x = player.rect.centerx
                shield_center_y = player.rect.centery - camera_y
                shield_radius = 70  # Bubble radius
                # Create a surface for the shield with alpha
                shield_surf = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
                # Draw a filled circle with very transparent cyan
                pygame.draw.circle(shield_surf, (0, 255, 255, 30), (shield_radius, shield_radius), shield_radius)
                # Draw the filled shield on screen
                screen.blit(shield_surf, (shield_center_x - shield_radius, shield_center_y - shield_radius))
            
            # Draw upward arrows effect if player has both Jump Boost and Gravity Reduction
            if 'Jump Boost' in player.active_upgrades and 'Gravity Reduction' in player.active_upgrades:
                screen_center_y = GameSettings.SCREEN_HEIGHT // 2
                # Draw arrows on the left side
                for i in range(4):
                    offset_y = i * 45
                    alpha = int(255 * (0.8 - i * 0.15))  # Fade out as they go up
                    if alpha > 0:
                        # Create transparent surface for large arrow
                        arrow_surf = pygame.Surface((60, 50), pygame.SRCALPHA)
                        # Draw large upward-pointing arrow
                        pygame.draw.polygon(arrow_surf, (100, 200, 255, alpha), [
                            (30, 0),      # Top point
                            (50, 35),     # Right point
                            (38, 35),     # Right indent
                            (38, 50),     # Bottom right
                            (22, 50),     # Bottom left
                            (22, 35),     # Left indent
                            (10, 35)      # Left point
                        ])
                        screen.blit(arrow_surf, (20, screen_center_y - 100 - offset_y))
                
                # Draw arrows on the right side
                for i in range(4):
                    offset_y = i * 45
                    alpha = int(255 * (0.8 - i * 0.15))  # Fade out as they go up
                    if alpha > 0:
                        # Create transparent surface for large arrow
                        arrow_surf = pygame.Surface((60, 50), pygame.SRCALPHA)
                        # Draw large upward-pointing arrow
                        pygame.draw.polygon(arrow_surf, (100, 200, 255, alpha), [
                            (30, 0),      # Top point
                            (50, 35),     # Right point
                            (38, 35),     # Right indent
                            (38, 50),     # Bottom right
                            (22, 50),     # Bottom left
                            (22, 35),     # Left indent
                            (10, 35)      # Left point
                        ])
                        screen.blit(arrow_surf, (GameSettings.SCREEN_WIDTH - 80, screen_center_y - 100 - offset_y))
            
            # Draw speed boost arrows if Speed Boost is active
            if 'Speed Boost' in player.active_upgrades:
                arrow_x = player.rect.centerx + 50
                arrow_y = player.rect.centery - camera_y
                # Draw first ">" arrow pointing right
                pygame.draw.polygon(screen, (255, 165, 0), [
                    (arrow_x, arrow_y - 10),
                    (arrow_x + 12, arrow_y),
                    (arrow_x, arrow_y + 10)
                ])
                # Draw second ">" arrow pointing right (offset to the right)
                pygame.draw.polygon(screen, (255, 165, 0), [
                    (arrow_x + 10, arrow_y - 10),
                    (arrow_x + 22, arrow_y),
                    (arrow_x + 10, arrow_y + 10)
                ])
            
            # Draw HUD info inside a centered white/gray box at the top
            info_text = f"Score: {score}   |   High Score: {high_score}   |   Level: {current_difficulty + 1}"
            score_surface = score_font.render(info_text, True, GameSettings.BLACK)
            # Create a background box slightly larger than the text
            padding_x = 16
            padding_y = 8
            box_w = score_surface.get_width() + padding_x * 2
            box_h = score_surface.get_height() + padding_y * 2
            box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            # Fill with light gray and slight opacity
            box_surf.fill((230, 230, 230, 240))
            # Draw border
            pygame.draw.rect(box_surf, (100, 100, 100), box_surf.get_rect(), 2)
            # Blit text onto box
            box_surf.blit(score_surface, (padding_x, padding_y))
            # Position box centered at the top (y = 10)
            box_x = GameSettings.SCREEN_WIDTH // 2 - box_w // 2
            box_y = 10
            screen.blit(box_surf, (box_x, box_y))
            
            # Draw upgrade status at top left without box
            if player.active_upgrades or player.shield_active:
                upgrade_font = pygame.font.Font(None, 32)
                upgrade_list = []
                for name, remaining in player.active_upgrades.items():
                    seconds = remaining / 60
                    upgrade_list.append(f"{name} ({seconds:.1f}s)")
                if player.shield_active:
                    upgrade_list.append("Shield: ON")
                
                for i, upgrade_text in enumerate(upgrade_list):
                    upgrade_surf = upgrade_font.render(upgrade_text, True, GameSettings.WHITE)
                    screen.blit(upgrade_surf, (10, 10 + i * 35))
            
            # Update the display
            pygame.display.flip()

# Entry point - run the game
if __name__ == "__main__":
    main()

