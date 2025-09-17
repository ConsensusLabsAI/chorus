"""
ANSI color codes for terminal output.
"""

class Colors:
    """ANSI color codes for terminal output."""
    
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Text formatting
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    STRIKETHROUGH = '\033[9m'
    
    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'
    BG_MAGENTA = '\033[105m'
    BG_CYAN = '\033[106m'
    BG_WHITE = '\033[107m'
    
    # Reset
    END = '\033[0m'
    
    @staticmethod
    def colorize(text: str, color: str) -> str:
        """Apply color to text."""
        return f"{color}{text}{Colors.END}"
    
    @staticmethod
    def bold(text: str) -> str:
        """Make text bold."""
        return Colors.colorize(text, Colors.BOLD)
    
    @staticmethod
    def red(text: str) -> str:
        """Make text red."""
        return Colors.colorize(text, Colors.RED)
    
    @staticmethod
    def green(text: str) -> str:
        """Make text green."""
        return Colors.colorize(text, Colors.GREEN)
    
    @staticmethod
    def yellow(text: str) -> str:
        """Make text yellow."""
        return Colors.colorize(text, Colors.YELLOW)
    
    @staticmethod
    def blue(text: str) -> str:
        """Make text blue."""
        return Colors.colorize(text, Colors.BLUE)
    
    @staticmethod
    def cyan(text: str) -> str:
        """Make text cyan."""
        return Colors.colorize(text, Colors.CYAN)
    
    @staticmethod
    def magenta(text: str) -> str:
        """Make text magenta."""
        return Colors.colorize(text, Colors.MAGENTA)
    
    @staticmethod
    def white(text: str) -> str:
        """Make text white."""
        return Colors.colorize(text, Colors.WHITE)
