import os
import random
import uuid
from datetime import datetime, timedelta

from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "university")

TOTAL_STUDENTS = int(os.getenv("TOTAL_STUDENTS", "100000"))
FILES_PER_STUDENT = int(os.getenv("FILES_PER_STUDENT", "2"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "2000"))

FACULTIES = ["FCS", "FE", "LAW", "ECON", "MATH"]
GROUP_PREFIXES = ["SE", "DA", "CS", "ML", "BD"]
FILE_TYPES = ["passport_scan", "transcript", "photo", "application"]

FIRST_NAMES = [
    "Ivan", "Petr", "Sergey", "Anna", "Maria", "Elena",
    "Dmitry", "Olga", "Nikita", "Irina", "Alexey", "Sofia"
]
LAST_NAMES = [
    "Petrov", "Ivanov", "Sidorov", "Smirnov", "Kuznetsov",
    "Popov", "Sokolov", "Volkova", "Morozova", "Fedorov"
]

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
client.admin.command("ping")
db = client[MONGO_DB]

students_col = db.students
files_col = db.student_files


def chunked_insert(collection, docs, label):
    if docs:
        result = collection.insert_many(docs, ordered=False)
        print(f"{label}: inserted {len(result.inserted_ids)}")


def make_student(i: int):
    student_id = f"S{i:06d}"
    faculty = random.choice(FACULTIES)
    group_prefix = random.choice(GROUP_PREFIXES)
    year = random.randint(1, 4)
    group_id = f"{group_prefix}-{random.randint(21, 26)}"
    full_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    created_at = datetime.utcnow() - timedelta(days=random.randint(0, 365))

    return {
        "student_id": student_id,
        "full_name": full_name,
        "group_id": group_id,
        "faculty": faculty,
        "year": year,
        "created_at": created_at,
    }


def make_files(student_id: str, n: int):
    docs = []
    for _ in range(n):
        file_id = f"file_{uuid.uuid4().hex[:12]}"
        file_type = random.choice(FILE_TYPES)
        ext = random.choice([".pdf", ".jpg", ".png"])
        docs.append({
            "file_id": file_id,
            "student_id": student_id,
            "file_type": file_type,
            "filename": f"{file_type}_{uuid.uuid4().hex[:8]}{ext}",
            "size_bytes": random.randint(50_000, 5_000_000),
            "bucket": "university-files",
            "object_key": f"students/{student_id}/{file_type}/{file_id}{ext}",
            "etag": uuid.uuid4().hex,
            "version_id": None,
            "uploaded_at": datetime.utcnow() - timedelta(days=random.randint(0, 365)),
            "status": "active",
        })
    return docs


def main():
    print("Cleaning old demo data...")
    students_col.delete_many({})
    files_col.delete_many({})

    student_batch = []
    file_batch = []

    for i in range(1, TOTAL_STUDENTS + 1):
        student = make_student(i)
        student_batch.append(student)
        file_batch.extend(make_files(student["student_id"], FILES_PER_STUDENT))

        if len(student_batch) >= BATCH_SIZE:
            chunked_insert(students_col, student_batch, "students")
            student_batch = []

        if len(file_batch) >= BATCH_SIZE:
            chunked_insert(files_col, file_batch, "student_files")
            file_batch = []

        if i % 10000 == 0:
            print(f"processed students: {i}")

    chunked_insert(students_col, student_batch, "students")
    chunked_insert(files_col, file_batch, "student_files")

    print("Done")
    print("students:", students_col.count_documents({}))
    print("student_files:", files_col.count_documents({}))


if __name__ == "__main__":
    main()
