from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import requests
import sqlite3
from datetime import datetime
import threading

app = Flask(__name__)

##########################################
# CONFIG
##########################################

INGESTION_URL = "http://127.0.0.1:5001/run"

CSV_FILES = [
    "../data/inputs/raws_football_db.csv",
    "../data/inputs/raws_medical_db.csv",
    "../data/inputs/raws_social_db.csv"
]

##########################################
# DATABASE
##########################################

def init_db():
    conn = sqlite3.connect("client_system.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_labels (
        player_id TEXT PRIMARY KEY,
        label INTEGER,
        classifier_id TEXT,
        decision TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


##########################################
# SEND TO INGESTION
##########################################

def send_record(record):
    try:
        response = requests.post(INGESTION_URL, json=record)
        print(f"Sent: {record}")
        print(f"Response: {response.json()}")

    except Exception as e:
        print(f"Error sending record: {e}")


##########################################
# CSV STREAMER
##########################################

def stream_csv_data():

    df1 = pd.read_csv(CSV_FILES[0]).replace({np.nan: None})
    df2 = pd.read_csv(CSV_FILES[1]).replace({np.nan: None})
    df3 = pd.read_csv(CSV_FILES[2]).replace({np.nan: None})

    for _, row in df1.iterrows():

        player_id = row["player_id"]

        ###################################
        # FOOTBALL RECORD
        ###################################
        record1 = {
            "player_id": player_id,
            "skill_overall": row["overall"],
            "label": 3
        }

        send_record(record1)

        ###################################
        # MEDICAL RECORD
        ###################################
        match2 = df2[df2["player_id"] == player_id]

        if not match2.empty:
            r2 = match2.iloc[0]

            record2 = {
                "player_id": r2["player_id"],
                "days_missed": r2["days_missed"],
                "games_missed": r2["games_missed"]
            }

            send_record(record2)

        ###################################
        # SOCIAL RECORD
        ###################################
        match3 = df3[df3["id_player"] == player_id]

        if not match3.empty:
            r3 = match3.iloc[0]

            record3 = {
                "player_id": r3["id_player"],
                "number_of_likes": r3["numberOfLikes"],
                "number_of_followers": r3["numberOfFollowers"]
            }

            send_record(record3)


##########################################
# START PIPELINE
##########################################

@app.route("/start", methods=["POST"])
def start_pipeline():

    threading.Thread(target=stream_csv_data).start()

    return jsonify({
        "message": "CSV streaming started"
    })


##########################################
# RECEIVE LABEL FROM CLASSIFIER
##########################################

@app.route("/receive-label", methods=["POST"])
def receive_label():

    data = request.get_json()

    player_id = data["player_id"]
    label = data["label"]
    classifier_id = data["classifier_id"]

    ###################################
    # DECISION LOGIC
    ###################################
    decision = "APPROVED" if label >= 4 else "REJECTED"

    ###################################
    # STORE
    ###################################
    conn = sqlite3.connect("client_system.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO player_labels
    VALUES (?, ?, ?, ?, ?)
    """, (
        player_id,
        label,
        classifier_id,
        decision,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Label stored",
        "decision": decision
    })


##########################################
# GET PLAYER RESULT
##########################################

@app.route("/player/<player_id>", methods=["GET"])
def get_player(player_id):

    conn = sqlite3.connect("client_system.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM player_labels WHERE player_id=?",
        (player_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if not row:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "player_id": row[0],
        "label": row[1],
        "classifier_id": row[2],
        "decision": row[3],
        "updated_at": row[4]
    })


##########################################

if __name__ == "__main__":
    app.run(port=5000, debug=True)