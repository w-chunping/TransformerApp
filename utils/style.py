from tkinter import font

def format_channelized_decimal_aligned(values, precision=4, total_int_len = 8):
    # Convert all numbers to strings with fixed decimal places
    str_values = [f"{v:.{precision}f}" for v in values]

    # Split into integer and decimal parts
    int_parts = [s.split('.')[0] for s in str_values]
    dec_parts = [s.split('.')[1] for s in str_values]

    # Find max width of integer parts (for padding)
    max_int_width = max(len(ip) for ip in int_parts)

    # Build aligned strings
    aligned_strs = []
    for i, (ip, dp) in enumerate(zip(int_parts, dec_parts)):
        # Pad integer part to right-align decimal points
        # padded_int = ip.rjust(max_int_width)
        padded_int = ip.rjust(total_int_len)
        aligned_strs.append(f"Ch.{i+1:<2} {padded_int}.{dp}")

    # Join with separator
    return " | ".join(aligned_strs)

# Try to find a nice monospaced font
def get_pretty_mono_font(size=10):
    preferred = ["DejaVu Sans Mono", "Menlo", "Liberation Mono", "Ubuntu Mono", "Consolas", "Courier New"]
    available = font.families()

    for name in preferred:
        if name in available:
            print(f"[INFO] Using font {name} for circuit output.")
            return (name, size)

    return ("TkFixedFont", size)  # fallback