import sys

with open('backend/routes/reports.py', 'r') as f:
    content = f.read()

# Add imports
imports_to_add = """
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
"""
content = content.replace('from fastapi import APIRouter, Depends', imports_to_add + '\nfrom fastapi import APIRouter, Depends')

# Add templates
content = content.replace('router = APIRouter()', 'router = APIRouter()\ntemplates = Jinja2Templates(directory="templates")\n')

# Add dashboard view route
dashboard_route = """

@router.get("/dashboard-view", response_class=HTMLResponse)
def get_dashboard_view(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch metrics using existing logic (simplified)
    total_contacts = db.query(Contact).count()
    opp_metrics = db.query(
        func.count(Opportunity.id).label('total'),
        func.sum(case((Opportunity.stage.in_(["lead", "qualified", "proposal"]), Opportunity.value), else_=0)).label('pipeline_value'),
        func.sum(case((Opportunity.stage == "won", Opportunity.value), else_=0)).label('won_value'),
    ).first()

    task_metrics = db.query(
        func.count(Task.id).label('total'),
        func.sum(case((Task.status != "completed", 1), else_=0)).label('open_tasks')
    ).first()

    # Calculate percentages for pipeline
    total_pipeline_val = opp_metrics.pipeline_value or 0 if opp_metrics else 0
    pipeline = [
        {"name": "Lead", "value": f"${opp_metrics.pipeline_value or 0}", "percentage": "100"}
    ]

    # Fetch next tasks
    next_tasks = db.query(Task).filter(Task.status != "completed").limit(5).all()
    tasks_data = [{"title": t.title, "due_date": t.due_date, "priority": t.priority} for t in next_tasks]

    # Fetch top opps
    top_opportunities = db.query(Opportunity).order_by(Opportunity.value.desc()).limit(5).all()
    opps_data = [{"account_name": o.title, "closing_date": "Soon", "confidence": 80, "value": f"${o.value}"} for o in top_opportunities]

    metrics = {
        "total_contacts": total_contacts,
        "pipeline_value": f"${total_pipeline_val}",
        "won_value": f"${opp_metrics.won_value or 0 if opp_metrics else 0}",
        "open_tasks": task_metrics.open_tasks or 0 if task_metrics else 0
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "metrics": metrics,
        "pipeline": pipeline,
        "next_tasks": tasks_data,
        "top_opportunities": opps_data
    })
"""
content = content + dashboard_route

with open('backend/routes/reports.py', 'w') as f:
    f.write(content)
