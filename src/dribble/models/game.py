import pymem
import json


# Attach to the NBA2K25.exe process and gets its important memory addresses
class Game:
    def __init__(self):
        try:
            # Attempt to attach to NBA2K25.exe process
            self.memory = pymem.Pymem("NBA2K25.exe")
            self.module = pymem.process.module_from_name(
                self.memory.process_handle, "NBA2K25.exe"
            )

            # Check if the module was found
            if not self.module:
                raise RuntimeError("Could not find NBA2K25.exe module.")

            # Store the base address
            self.base_address = self.module.lpBaseOfDll

        except pymem.exception.PymemError as e:
            raise RuntimeError(f"Memory Error, {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"{str(e)}") from e


# A class to represent a player with attributes and methods to manipulate them
class Player:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    # Export to JSON
    def to_json(self):
        return json.dumps(self.__dict__, indent=4)

    # Override the __str__ method to provide a string representation of the object
    def __str__(self):
        try:
            return f"{self.vitals['First Name']} {self.vitals['Last Name']}"
        except AttributeError:
            return "Unknown Player"

    # Override the __repr__ method to provide a string representation of the object
    def __repr__(self):
        return self.__str__()
