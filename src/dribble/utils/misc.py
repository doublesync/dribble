import re


# Function to check if a string contains only valid characters (alphanumeric, hyphens, apostrophes, and spaces)
def HasValidCharacters(text):
    return bool(re.fullmatch(r"[a-zA-Z0-9-'. ]+", text))


# Function to convert an integer to a memory-friendly value
def ConvertToGameValue(integer, length):
    """
    Convert an integer to a game-friendly value.

    :param integer: The integer to convert (should be in the range of 25-110).
    :param length: The length of the value in bits.
    """
    game_value = (
        integer - 25
    ) * 3  # Scale the value to the game's range (0-255 aka. the 8-bit range)
    game_value = max(
        0, min(game_value, 255)
    )  # Clamp the value to ensure it stays within the 0-255 range
    bytes_value = game_value.to_bytes(1, byteorder="little")  # Convert to a single byte
    return bytes_value


# Function to convert a memory-friendly value to a user-readble integer
def ConvertToReadableValue(integer):
    """
    Convert a memory-friendly value back to a user-readable integer.

    :param integer: The memory-friendly value to convert (should be in the range of 0-255).
    """
    return (integer // 3) + 25


# Function to convert bit length to byte length
def BitLengthToByteLength(length, start_bit=0):
    """
    Convert bit length to byte length, adding 7 to ensure we round up to multiple of 8.

    :param length: The length in bits.
    :param start_bit: The starting bit position.
    """
    return max((start_bit + length + 7) // 8, 1)
