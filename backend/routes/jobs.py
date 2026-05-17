from flask import Blueprint, render_template
from models.job_model import get_all_jobs

jobs_bp = Blueprint("jobs", __name__)

@jobs_bp.route("/jobs")
def jobs():

    jobs = get_all_jobs()

    return render_template("jobs.html", jobs=jobs)