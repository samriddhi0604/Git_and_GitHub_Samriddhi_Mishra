# Git & GitHub – DevOps Assignment

**Student:** Samriddhi Mishra
**Repository:** https://github.com/samriddhi0604/Git_and_GitHub_Samriddhi_Mishra

A Flask + MongoDB Atlas project used to practise the full Git workflow:
SSH setup, branching, merging, conflict resolution, sequential commits,
`git reset` and rebasing.

## Routes

| Route | Method | Description |
|---|---|---|
| `/api` | GET | Returns the JSON list stored in `data.json` |
| `/` | GET / POST | Form that saves the submitted data in MongoDB Atlas |
| `/success` | GET | "Data submitted successfully" page |

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env      # then paste your MongoDB Atlas connection string
python app.py
```

Open http://127.0.0.1:5000
