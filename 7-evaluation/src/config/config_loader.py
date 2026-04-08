import json
import os


class Config:
    """
    Singleton config loader
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)

            # ================= LOAD CONFIG =================

            # Go from:
            # src/config/config_loader.py
            # -> up to parent of 7-evaluation
            parent_dir = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(__file__)
                    )
                )
            )

            # Build config path
            config_path = os.path.join(parent_dir, "config", "evaluationConfig.json")

            # Validate file exists
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")

            # Load JSON
            with open(config_path, "r") as f:
                instance._config = json.load(f)

            cls._instance = instance

        return cls._instance

    # ================= DICT ACCESS =================

    def __getitem__(self, key):
        return self._config[key]

    # ================= OPTIONAL HELPERS =================

    def get(self, key, default=None):
        return self._config.get(key, default)

    def all(self):
        return self._config



# import json
# import os


# class Config:
#     """
#     Singleton config loader
#     """

#     _instance = None

#     def __new__(cls):
#         if cls._instance is None:
#             instance = super().__new__(cls)

#             # ================= LOAD CONFIG =================
#             base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
#             config_path = os.path.join(base_dir, "data", "config.json")

#             if not os.path.exists(config_path):
#                 raise FileNotFoundError(f"Config file not found: {config_path}")

#             with open(config_path, "r") as f:
#                 instance._config = json.load(f)

#             cls._instance = instance

#         return cls._instance

#     # ================= DICT ACCESS =================

#     def __getitem__(self, key):
#         return self._config[key]

#     # ================= OPTIONAL HELPERS =================

#     def get(self, key, default=None):
#         return self._config.get(key, default)

#     def all(self):
#         return self._config

