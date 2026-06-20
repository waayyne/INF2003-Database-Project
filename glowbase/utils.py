from textwrap import dedent

import matplotlib
from flask import session

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def is_admin_logged_in():
    return session.get("admin_logged_in") == True


def fix_mongo_id(review):
    if "_id" in review:
        review["_id"] = str(review["_id"])
    return review


def parse_number_range(value):
    """Return a validated numeric range, or None for an invalid filter value."""
    if not value:
        return None

    try:
        minimum, maximum = value.split("-", 1)
        minimum = float(minimum)
        maximum = float(maximum)
    except (TypeError, ValueError):
        return None

    if minimum > maximum:
        return None

    return minimum, maximum


def make_pasteable_sql(query, params):
    pasteable_query = dedent(query).strip()

    for param in params:
        if param is None:
            value = "NULL"
        elif isinstance(param, (int, float)):
            value = str(param)
        else:
            escaped = str(param).replace("\\", "\\\\").replace("'", "''")
            value = f"'{escaped}'"

        pasteable_query = pasteable_query.replace("%s", value, 1)

    return pasteable_query


def save_bar_chart(file_path, labels, values, title, x_label, y_label, color):
    figure, axis = plt.subplots(figsize=(6, 3.5))
    figure.patch.set_facecolor("white")

    if labels and values:
        axis.bar(labels, values, color=color, edgecolor="#333333")
        axis.tick_params(axis="x", rotation=35)
    else:
        axis.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center",
            transform=axis.transAxes,
            fontsize=14,
            color="#666666"
        )
        axis.set_xticks([])
        axis.set_yticks([])

    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)

    for spine in ["top", "right"]:
        axis.spines[spine].set_visible(False)

    figure.tight_layout()
    figure.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(figure)
