import os
from datetime import datetime

import typer
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from minio import Minio
from rich.console import Console
from rich.table import Table


app = typer.Typer(help="University DB CLI")
console = Console()

mongo = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = mongo[os.getenv("MONGO_DB", "university")]

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
    secure=False,
)


@app.command()
def add_student(student_id: str, full_name: str, group_id: str, faculty: str, year: int):
    existing = db.students.find_one({"student_id": student_id}, {"_id": 1})
    if existing:
        console.print(f"[red]Student {student_id} already exists[/red]")
        raise typer.Exit(code=1)

    db.students.insert_one({
        "student_id": student_id,
        "full_name": full_name,
        "group_id": group_id,
        "faculty": faculty,
        "year": year,
        "created_at": datetime.utcnow(),
    })
    console.print(f"[green]Student {student_id} added[/green]")


@app.command()
def list_students(limit: int = 20):
    if limit <= 0:
        console.print("[red]limit must be > 0[/red]")
        raise typer.Exit(code=1)

    table = Table(title=f"Students (showing up to {limit})")
    table.add_column("student_id")
    table.add_column("full_name")
    table.add_column("group_id")
    table.add_column("faculty")
    table.add_column("year")

    students = db.students.find({}, {"_id": 0}).limit(limit)

    count = 0
    for s in students:
        table.add_row(
            s["student_id"],
            s["full_name"],
            s["group_id"],
            s["faculty"],
            str(s["year"]),
        )
        count += 1

    if count == 0:
        console.print("[yellow]No students found[/yellow]")
        return

    console.print(table)


if __name__ == "__main__":
    app()
