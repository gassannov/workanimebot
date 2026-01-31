"""
URL Decoder - ports the hex substitution cipher from ani-cli's provider_init function.

The encrypted URLs use a custom hex substitution where each byte is mapped
through a substitution table. This module decodes them back to readable URLs.

Reference: ani-cli lines 168-172
"""

# Hex substitution mapping extracted from ani-cli's provider_init function
# Format: encrypted_hex -> decoded_character
HEX_DECODE_MAP = {
    # Uppercase letters
    "79": "A", "7a": "B", "7b": "C", "7c": "D", "7d": "E",
    "7e": "F", "7f": "G", "70": "H", "71": "I", "72": "J",
    "73": "K", "74": "L", "75": "M", "76": "N", "77": "O",
    "68": "P", "69": "Q", "6a": "R", "6b": "S", "6c": "T",
    "6d": "U", "6e": "V", "6f": "W", "60": "X", "61": "Y",
    "62": "Z",
    # Lowercase letters
    "59": "a", "5a": "b", "5b": "c", "5c": "d", "5d": "e",
    "5e": "f", "5f": "g", "50": "h", "51": "i", "52": "j",
    "53": "k", "54": "l", "55": "m", "56": "n", "57": "o",
    "48": "p", "49": "q", "4a": "r", "4b": "s", "4c": "t",
    "4d": "u", "4e": "v", "4f": "w", "40": "x", "41": "y",
    "42": "z",
    # Numbers
    "08": "0", "09": "1", "0a": "2", "0b": "3", "0c": "4",
    "0d": "5", "0e": "6", "0f": "7", "00": "8", "01": "9",
    # Special characters
    "15": "-", "16": ".", "67": "_", "46": "~",
    "02": ":", "17": "/", "07": "?", "1b": "#",
    "63": "[", "65": "]", "78": "@", "19": "!",
    "1c": "$", "1e": "&", "10": "(", "11": ")",
    "12": "*", "13": "+", "14": ",", "03": ";",
    "05": "=", "1d": "%",
}


def decode_provider_url(encrypted_url: str) -> str:
    """
    Decode an encrypted provider URL from AllAnime.

    The URL is encrypted as hex pairs that need to be mapped through
    the substitution table.

    Args:
        encrypted_url: The encrypted URL string (hex encoded)

    Returns:
        The decoded URL string
    """
    if not encrypted_url:
        return ""

    # Remove leading "--" if present (as seen in ani-cli response parsing)
    if encrypted_url.startswith("--"):
        encrypted_url = encrypted_url[2:]

    decoded_chars = []

    # Process hex pairs (2 characters at a time)
    i = 0
    while i < len(encrypted_url):
        if i + 1 < len(encrypted_url):
            hex_pair = encrypted_url[i:i + 2].lower()

            if hex_pair in HEX_DECODE_MAP:
                decoded_chars.append(HEX_DECODE_MAP[hex_pair])
                i += 2
            else:
                # If not in map, keep original character
                decoded_chars.append(encrypted_url[i])
                i += 1
        else:
            # Odd character at end - keep as is
            decoded_chars.append(encrypted_url[i])
            i += 1

    result = "".join(decoded_chars)

    # Apply the /clock -> /clock.json transformation (from ani-cli)
    result = result.replace("/clock", "/clock.json")

    return result
