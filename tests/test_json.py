from common.json_io import JsonIO

data = {
    "system": "ingestion",
    "status": "ok"
}

JsonIO.save("data/test/sample.json", data)

loaded = JsonIO.load("data/test/sample.json")
print(loaded)