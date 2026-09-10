from sqlalchemy.orm import Session
from sqlalchemy import select,func

from .models import Task
from .schemas import TaskCreate, TaskUpdate


def list_tasks(db: Session, completed: bool | None = None, limit: int = 20) -> list[Task]:
    statement = select(Task)

    if completed is not None:
        statement = statement.where(Task.completed == completed)

    statement = statement.order_by(Task.id.desc()).limit(limit) 
    return list(db.scalars(statement).all())


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def create_task(db: Session, payload: TaskCreate) -> Task:
    task = Task(
        title=payload.title.strip(),
        description=payload.description,
        completed=False,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, payload: TaskUpdate) -> Task:
    task.title = payload.title.strip()
    task.description = payload.description
    task.completed = payload.completed
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()

def get_stats(db: Session) -> dict[str, int]:
    total_tasks = db.scalar(select(func.count()).select_from(Task))
    completed_tasks = db.scalar(select(func.count()).select_from(Task).where(Task.completed == True))
    pending_tasks = total_tasks - completed_tasks
    return {
        "total": total_tasks,
        "completed": completed_tasks,
        "pending": pending_tasks,
    }