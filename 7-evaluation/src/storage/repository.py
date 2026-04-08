class Repository:
    """
    Abstraction layer over DB (evaluation-ready)
    """

    def __init__(self, store):
        self.store = store

    # ================= SAVE =================

    def save_label(self, data):
        self.store.insert(
            data["player_id"],
            data["label"],
            data["source"]
        )

    # ================= MATCHED DATA =================

    def get_matched_pairs(self):
        rows = self.store.fetch_matched()

        return [
            {
                "player_id": r[0],
                "expert": r[1],
                "classifier": r[2]
            }
            for r in rows
        ]

    def count_matched(self):
        return self.store.count_matched()

    # ================= CLEAN =================

    def clear(self):
        self.store.clear()

    def delete_used(self, batch):
        for item in batch:
            player_id = item["player_id"]
            self.store.delete(player_id)