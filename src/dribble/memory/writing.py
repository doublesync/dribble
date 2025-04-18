from rich import print

from . import BitLengthToByteLength

# List of categories and what they are written to the game as
written_in_bytes = ["Attributes"]
written_in_integers = [
    "Vitals",
    "Badges",
    "Tendencies",
    "Signatures",
    "Gear",
    "Hotzones",
    "Accessories",
]


# Write bytes to memory at a specific address
def WriteBinaryBytes(game, address, length, value):
    """
    Write bytes to memory at a specific address; only used for attributes
    because they are the only values that are written as bytes/binary
    while others are written as integers or strings.

    :param game: The game memory writer instance.
    :param address: The memory address to write to.
    :param length: The value to write as bits.
    :param value: The value in byte-format to write to memory.
    :return: None
    """
    num_bytes = BitLengthToByteLength(length)
    game.memory.write_bytes(address, value, num_bytes)


# Write integers to memory at a specific address
def WriteInteger(game, address, length, start_bit, value):
    """
    Write an integer to memory at a specific bit offset and length.

    :param game: The game memory writer instance.
    :param address: The memory address to write to.
    :param length: The number of bits to write.
    :param value: The value to write.
    :param start_bit: The starting bit position within the byte.
    """
    try:
        # Clamp the value to allowed range
        max_value = (1 << length) - 1
        value = max(0, min(value, max_value))

        # Compute how many bytes we need to affect
        num_bytes = BitLengthToByteLength(length, start_bit)

        # Read existing bytes from memory
        raw_bytes = game.memory.read_bytes(address, num_bytes)
        current_int = int.from_bytes(raw_bytes, byteorder="little")

        # Clear the bit range, then insert the new value
        mask = ((1 << length) - 1) << start_bit
        updated_int = (current_int & ~mask) | ((value & max_value) << start_bit)

        # Convert back to bytes and write the full block back
        updated_bytes = updated_int.to_bytes(num_bytes, byteorder="little")
        game.memory.write_bytes(address, updated_bytes, num_bytes)
    except Exception as e:
        print(f"[red]Error writing integer to memory: {e}[/red]")
